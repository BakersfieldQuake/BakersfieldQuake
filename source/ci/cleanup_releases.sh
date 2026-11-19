#!/usr/bin/env bash
# Removes releases a cancelled or failed "Build release packages" run left half-made.
#
# gh creates a release as a draft, uploads the assets, then publishes it. A run cancelled in between leaves a draft
# tagged build-YYYYMMDD-<sha7>. Intended drafts always end in -draft (test builds) or are base-v* (asset bases), so
# only that exact tag shape is deleted.
#
# usage: cleanup_releases.sh [min_age_minutes]   (default 0; DRY_RUN=1 lists without deleting)
# Needs GH_TOKEN and GITHUB_REPOSITORY (set on Actions runners).
set -euo pipefail
min="${1:-0}"
repo="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY not set}"

gh release list -R "$repo" -L 200 --json tagName,isDraft,createdAt \
    --jq ".[] | select(.isDraft and (.tagName | test(\"^build-[0-9]{8}-[0-9a-f]{7}\$\")) and (now - (.createdAt | fromdateiso8601) > $min * 60)) | .tagName" |
while read -r tag; do
    if [ "${DRY_RUN:-0}" = 1 ]; then
        echo "would delete incomplete draft $tag"
    else
        echo "deleting incomplete draft $tag"
        gh release delete "$tag" -R "$repo" --yes --cleanup-tag
    fi
done

# A published release without its DMG means the macos job failed or was cancelled. Players' updaters still work (the
# manifests are on the release), so it is only reported, not deleted.
gh release list -R "$repo" -L 5 --exclude-drafts --json tagName,createdAt \
    --jq '.[] | select(.tagName | startswith("build-")) | select(now - (.createdAt | fromdateiso8601) > 7200) | .tagName' |
while read -r tag; do
    if ! gh release view "$tag" -R "$repo" --json assets --jq '.assets[].name' | grep -qx 'BAKOQUAKE-macos-arm64.dmg'; then
        echo "::warning::release $tag has no macOS DMG (macos job failed or was cancelled); re-run the workflow to replace it"
    fi
done
