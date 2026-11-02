import numpy as np, cv2
src=open('flowcal.py').read().split("for it in range(3):")[0]
exec(src)
g=[cv2.GaussianBlur(cv2.cvtColor(cv2.imread(f'all/f{i+1:03d}.png'),cv2.COLOR_BGR2LAB),(0,0),2.0).astype(np.float32) for i in range(N)]
def photocost(P):
    alive=vote_hull(P); p,n=surf_points(alive)
    keep=(p[:,1]>180)&(p[:,1]<700); p,n=p[keep],n[keep]
    sel=np.random.RandomState(0).choice(len(p),min(len(p),12000),replace=False); p,n=p[sel],n[sel]
    tot=[]
    for i in range(0,N-12,6):
        j=i+12
        vals=[]
        for k in (i,j):
            th=P[k,0]; cam=np.array([-np.sin(th),0,np.cos(th)]); face=(n@cam)>0.45
            u,v=c.proj(p[:,0],p[:,1],p[:,2],k,P[k]); ok=face&(u>2)&(u<W-3)&(v>2)&(v<H-3)
            a=np.full((len(p),3),np.nan,np.float32)
            a[ok]=cv2.remap(g[k],u[ok].astype(np.float32)[None],v[ok].astype(np.float32)[None],cv2.INTER_LINEAR)[0]; vals.append(a)
        ok=~np.isnan(vals[0][:,0])&~np.isnan(vals[1][:,0])
        if ok.sum()<300: continue
        x=vals[0][ok];y=vals[1][ok]; x=(x-x.mean(0))/(x.std(0)+1e-6); y=(y-y.mean(0))/(y.std(0)+1e-6)
        tot.append(np.minimum(np.abs(x-y).mean(1),2).mean())
    return np.mean(tot),len(tot),alive.sum()
Pn=P.copy(); Pn[:,0]=-P[:,0]
print('as-is  (cost,n,hull):',photocost(P))
print('flipped(cost,n,hull):',photocost(Pn))
