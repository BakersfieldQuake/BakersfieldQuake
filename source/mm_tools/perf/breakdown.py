"""Split a loadtime.py run into time per model (the gap until the next \"loading model\" line) and image bytes.
    python -I breakdown.py <tag> [<tag>...]    (run from the work dir that holds runs/)
The first row can carry the idle gap before the map command; ignore a large "None" entry."""
import re,collections,sys
ALWAYS=None
def load(tag):
    rows=[]
    for l in open("runs/%s.timed.log"%tag,encoding="utf-8"):
        m=re.match(r"\s*(\d+\.\d\d) (.*)",l)
        if m: rows.append((float(m.group(1)),re.sub(r"\^\d","",m.group(2))))
    return rows
def analyze(tag):
    rows=load(tag)
    t_go=next(t for t,s in rows if "SpawnServer" in s); t_end=next(t for t,s in rows if "entered the game" in s)
    cur=None; cost=collections.Counter(); px=collections.Counter(); nimg=collections.Counter(); last=rows[0][0]; order=[]
    for t,s in rows:
        m=re.match(r"loading model (\S+)",s)
        if m:
            cur=m.group(1); order.append(cur)
        m2=re.match(r"loaded image (\S+) \((\d+)x(\d+)\)",s)
        if m2 and cur and t_go<=t<=t_end: px[cur]+=int(m2.group(2))*int(m2.group(3))*4; nimg[cur]+=1
        if t_go<=t<=t_end: cost[cur]+=t-last
        last=t
    return t_end-t_go,cost,px,nimg,rows
if __name__=="__main__":
    for tag in sys.argv[1:]:
        tot,cost,px,nimg,rows=analyze(tag)
        print(f"== {tag}: load {tot:.1f}s | images {sum(nimg.values())} = {sum(px.values())/1e6:.0f} MB raw")
        for k,v in sorted(cost.items(),key=lambda kv:-kv[1])[:40]:
            print(f"      {v:5.2f}s {nimg[k]:4} img {px[k]/1e6:5.0f}MB  {k}")
