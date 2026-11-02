"""Check a drive / flight route against a .map: sweep a box along every leg and print what it runs into.
usage: python route_check.py <map> <half_width_ft> <z0_ft> <z1_ft> "x,y x,y x,y ..."     (feet, map frame, closed loop)
Brushes of trigger_* and func_detail_illusionary entities are ignored (they are not solid); clip brushes count
(they stand for parked models)."""
import math
import re
import sys

OX, OY, U = -110, 225, 12
num = re.compile(r"\(\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s*\)")
tex_re = re.compile(r"\)\s+([A-Za-z{_][\w{}.-]*)\s+-?[\d.]+")


def brushes(path):
    out, depth, cls, br = [], 0, None, []
    for line in open(path).read().split("\n"):
        if line == "{":
            depth += 1
            if depth == 2:
                br = []
            elif depth == 1:
                cls = None
        elif line == "}":
            if depth == 2 and cls and not cls.startswith("trigger") and cls != "func_detail_illusionary":
                pts = [tuple(map(int, g)) for g in num.findall("\n".join(br))]
                if pts:
                    lo = [min(p[i] for p in pts) for i in range(3)]
                    hi = [max(p[i] for p in pts) for i in range(3)]
                    tex = [t for t in tex_re.findall("\n".join(br))]
                    if "sky_bk" not in tex:
                        out.append((lo[0] / U + OX, lo[1] / U + OY, lo[2] / U, hi[0] / U + OX, hi[1] / U + OY, hi[2] / U,
                                    cls, tex[-1] if tex else "?"))
            depth -= 1
        elif depth == 1:
            m = re.match(r'"classname" "([^"]+)"', line)
            if m:
                cls = m.group(1)
        elif depth == 2:
            br.append(line)
    return out


def check(B, pts, hw, z0, z1, closed=True):
    bad = []
    legs = list(zip(pts, pts[1:] + (pts[:1] if closed else [])))
    for i, (a, b) in enumerate(legs):
        L = math.dist(a, b)
        n = max(1, int(L / 3))
        hits = {}
        for k in range(n + 1):
            x = a[0] + (b[0] - a[0]) * k / n
            y = a[1] + (b[1] - a[1]) * k / n
            for bb in B:
                if bb[0] < x + hw and bb[3] > x - hw and bb[1] < y + hw and bb[4] > y - hw and bb[2] < z1 and bb[5] > z0:
                    hits.setdefault((round(bb[0]), round(bb[1]), round(bb[3]), round(bb[4]), bb[6], bb[7]), (round(x), round(y)))
        if hits:
            bad.append((i, a, b, list(hits.items())[:6]))
    return bad


if __name__ == "__main__":
    B = brushes(sys.argv[1])
    hw, z0, z1 = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    pts = [tuple(float(v) for v in p.split(",")) for p in sys.argv[5].split()]
    for i, a, b, hits in check(B, pts, hw, z0, z1):
        print("leg %d %s -> %s" % (i, a, b))
        for h, at in hits:
            print("    ", h, "at", at)
    print("done")
