"""Applies the votes from wheelman_cannon_sound_vote.html to the game sounds.

    python3.13 apply_wcannon_votes.py [votes.json]        (default ~/Downloads/votes.json)

For each slot (charge, shoot, scream, boom) the star pick is copied from
source/wcannon_sound_vote/clips/ to sound/wcannon/wc_<slot>.wav.  A slot with no star falls back to the clip
with the most (likes - dislikes); if nothing was voted on that slot the current game sound is left alone.
"""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
CLIPS = os.path.join(MOD, "source", "wcannon_sound_vote", "clips")
OUT = os.path.join(MOD, "sound", "wcannon")
SLOTS = ["charge", "shoot", "scream", "boom"]

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "Downloads", "votes.json")
    if not os.path.isfile(path):
        sys.exit("votes file not found: " + path)
    with open(path, encoding="utf-8") as f:
        votes = json.load(f)
    with open(os.path.join(MOD, "source", "wcannon_sound_vote", "clips.json"), encoding="utf-8") as f:
        labels = {c["id"]: c["label"] for c in json.load(f)}
    os.makedirs(OUT, exist_ok=True)
    for slot in SLOTS:
        v = votes.get(slot) or {}
        likes, dislikes = v.get("likes") or [], v.get("dislikes") or []
        pick, why = v.get("pick"), "star pick"
        if not pick:
            score = {}
            for c in likes: score[c] = score.get(c, 0) + 1
            for c in dislikes: score[c] = score.get(c, 0) - 1
            ranked = sorted(score.items(), key=lambda kv: -kv[1])
            if ranked and ranked[0][1] > 0:
                pick, why = ranked[0][0], "most likes (score %+d)" % ranked[0][1]
        if not pick:
            print("%-7s no pick and no likes: left wc_%s.wav as it is" % (slot, slot)); continue
        src = os.path.join(CLIPS, pick + ".wav")
        if not pick.startswith(slot + "_") or not os.path.isfile(src):
            print("%-7s clip %r not found in %s: skipped" % (slot, pick, CLIPS)); continue
        dst = os.path.join(OUT, "wc_%s.wav" % slot)
        shutil.copyfile(src, dst)
        print("%-7s %s (%s) -> %s   [%s]" % (slot, pick, labels.get(pick, "?"), dst, why))

if __name__ == "__main__":
    main()
