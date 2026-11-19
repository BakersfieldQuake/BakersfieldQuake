#!/usr/bin/env bash
# Deletes stale Actions caches and build artifacts, but always keeps the newest of each kind.
#
# - cache "kind" = the key up to its content hash (bq-update-win-..., zz_karts, zz_bakovan, zz_gunnomip, bq-mac-deps-...)
#   Stale = not accessed for more than N days. The newest-accessed entry of each kind is kept however old.
# - artifact "kind" = its name (bq-update-windows). Stale = created more than N days ago. Newest of each name is kept.
#
# usage: cleanup_actions_storage.sh [days]   (default 5; DRY_RUN=1 lists without deleting)
# Needs GH_TOKEN and GITHUB_REPOSITORY (set on Actions runners).
set -euo pipefail
days="${1:-5}"
repo="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY not set}"
secs=$((days * 86400))
dry="${DRY_RUN:-0}"

# jq's fromdateiso8601 rejects fractional seconds, which cache timestamps have.
age='(now - (sub("\\.[0-9]+Z$"; "Z") | fromdateiso8601))'

echo "== caches not accessed for $days days (newest per kind kept)"
gh cache list -R "$repo" -L 1000 --json id,key,lastAccessedAt \
    --jq "map(.kind = (.key | sub(\"-[0-9a-f]{40,}.*\$\"; \"\")))
          | group_by(.kind) | .[] | sort_by(.lastAccessedAt) | .[:-1][]
          | select(.lastAccessedAt | $age > $secs) | [.id, .key] | @tsv" |
while IFS=$'\t' read -r id key; do
    if [ "$dry" = 1 ]; then echo "would delete cache $id ${key:0:60}"; continue; fi
    echo "deleting cache $id ${key:0:60}"
    gh cache delete "$id" -R "$repo"
done

echo "== artifacts older than $days days (newest per name kept)"
gh api --paginate "repos/$repo/actions/artifacts?per_page=100" --jq '.artifacts[] | select(.expired | not)' |
    jq -rs "group_by(.name) | .[] | sort_by(.created_at) | .[:-1][]
            | select(.created_at | $age > $secs) | [.id, .name, .created_at] | @tsv" |
while IFS=$'\t' read -r id name created; do
    if [ "$dry" = 1 ]; then echo "would delete artifact $id $name $created"; continue; fi
    echo "deleting artifact $id $name $created"
    gh api -X DELETE "repos/$repo/actions/artifacts/$id" --silent
done
