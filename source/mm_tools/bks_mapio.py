"""Helpers of make_bakolansmall.py: read a generated .map (the output of make_goldenwest.py / make_bklan.py), cut a window out of it
and move the pieces to a new place (brush planes AND the texture offsets, so aligned textures stay put).
Units are map units (12 per foot). No dependency on the generators: it only reads their text output."""
import re

_NUM = re.compile(r"\(\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s*\)")
_FACE = re.compile(r"^(\(\s*-?\d+\s+-?\d+\s+-?\d+\s*\)\s*){3}(\S+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*$")

# Quake's axial texture projection: (normal, s axis, t axis)
_AXES = (((0, 0, 1), (1, 0, 0), (0, -1, 0)), ((0, 0, -1), (1, 0, 0), (0, -1, 0)),
         ((1, 0, 0), (0, 1, 0), (0, 0, -1)), ((-1, 0, 0), (0, 1, 0), (0, 0, -1)),
         ((0, 1, 0), (1, 0, 0), (0, 0, -1)), ((0, -1, 0), (1, 0, 0), (0, 0, -1)))


class Brush:
    __slots__ = ("lines", "lo", "hi", "texs")

    def __init__(self, lines):
        self.lines = lines
        pts = [tuple(int(v) for v in m) for ln in lines for m in _NUM.findall(ln)]
        self.lo = tuple(min(p[i] for p in pts) for i in range(3))
        self.hi = tuple(max(p[i] for p in pts) for i in range(3))
        self.texs = {_FACE.match(ln).group(2) for ln in lines if _FACE.match(ln)}

    def text(self):
        return "{\n" + "".join(ln + "\n" for ln in self.lines) + "}\n"

    def moved(self, d):
        """A copy moved by d = (dx, dy, dz) units; texture offsets follow so the pattern does not slide."""
        out = []
        for ln in self.lines:
            m = _FACE.match(ln)
            if not m:
                out.append(ln)
                continue
            p = [tuple(int(v) for v in mm) for mm in _NUM.findall(ln)]
            a = [p[0][i] - p[1][i] for i in range(3)]
            b = [p[2][i] - p[1][i] for i in range(3)]
            n = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
            best = max(_AXES, key=lambda ax: sum(n[i] * ax[0][i] for i in range(3)))
            tex, xo, yo, rot, sx, sy = m.group(2), float(m.group(3)), float(m.group(4)), m.group(5), float(m.group(6)), float(m.group(7))
            sv, tv = best[1], best[2]
            xo -= sum(d[i] * sv[i] for i in range(3)) / sx
            yo -= sum(d[i] * tv[i] for i in range(3)) / sy
            pts = " ".join("( %d %d %d )" % (q[0] + d[0], q[1] + d[1], q[2] + d[2]) for q in p)
            out.append("%s %s %.3f %.3f %s %s %s" % (pts, tex, xo, yo, rot, m.group(6), m.group(7)))
        return Brush(out)


class Ent:
    def __init__(self, kv, brushes):
        self.kv = kv
        self.brushes = brushes

    @property
    def cls(self):
        return self.kv.get("classname", "")

    def origin(self):
        if "origin" in self.kv:
            return tuple(int(float(v)) for v in self.kv["origin"].split())
        return None

    def text(self, d=(0, 0, 0)):
        kv = dict(self.kv)
        if "origin" in kv:
            o = self.origin()
            kv["origin"] = "%d %d %d" % (o[0] + d[0], o[1] + d[1], o[2] + d[2])
        s = "{\n" + "".join('"%s" "%s"\n' % it for it in kv.items())
        s += "".join((b.moved(d) if d != (0, 0, 0) else b).text() for b in self.brushes)
        return s + "}\n"


def read_map(path):
    ents, cur, brush = [], None, None
    for raw in open(path, encoding="utf-8"):
        ln = raw.strip()
        if not ln:
            continue
        if ln == "{":
            if cur is None:
                cur = Ent({}, [])
            else:
                brush = []
        elif ln == "}":
            if brush is not None:
                cur.brushes.append(Brush(brush))
                brush = None
            else:
                ents.append(cur)
                cur = None
        elif brush is not None:
            brush.append(ln)
        else:
            k, v = re.match(r'"([^"]*)"\s+"(.*)"$', ln).groups()
            cur.kv[k] = v
    return ents


def inside(b, win):
    """win = (x0, y0, x1, y1) units (z unlimited): the whole brush must lie inside."""
    return b.lo[0] >= win[0] and b.hi[0] <= win[2] and b.lo[1] >= win[1] and b.hi[1] <= win[3]
