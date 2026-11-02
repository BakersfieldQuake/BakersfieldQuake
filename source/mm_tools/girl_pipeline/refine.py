import numpy as np, cv2, time
src=open('flipcheck.py').read().split("Pn=P.copy()")[0]
exec(src)
P4=np.load('P4.npy')
best=None
for sc in (1.06,1.10,1.14):
    Q=P4.copy(); Q[:,0]=P4[0,0]+(P4[:,0]-P4[0,0])*sc
    cst=photocost(Q)[0]; print('scale',sc,cst,flush=True)
    if best is None or cst<best[0]: best=(cst,sc,Q)
P=best[2].copy(); print('using scale',best[1],flush=True)
cols=[cv2.GaussianBlur(cv2.imread(f'all/f{i+1:03d}.png').astype(np.float32),(0,0),2.0) for i in range(N)]
def sample(i,p,n,pi):
    th=pi[0]; cam=np.array([-np.sin(th),0,np.cos(th)]); face=(n@cam)>0.5
    u,v=c.proj(p[:,0],p[:,1],p[:,2],i,pi); ok=face&(u>2)&(u<W-3)&(v>2)&(v<H-3)
    vals=np.full((len(p),3),np.nan,np.float32)
    if ok.any(): vals[ok]=cv2.remap(cols[i],u[ok].astype(np.float32)[None],v[ok].astype(np.float32)[None],cv2.INTER_LINEAR)[0]
    return vals
def cost(i,pi,p,n,P,nb):
    a=sample(i,p,n,pi); tot=0;cnt=0
    for j in nb:
        b=sample(j,p,n,P[j]); ok=~np.isnan(a[:,0])&~np.isnan(b[:,0])
        if ok.sum()<400: continue
        x=a[ok];y=b[ok]; x=(x-x.mean(0))/(x.std(0)+1e-6); y=(y-y.mean(0))/(y.std(0)+1e-6)
        tot+=np.mean(np.minimum(np.abs(x-y).mean(1),2.0)); cnt+=1
    return tot/cnt if cnt else 9
t0=time.time()
for it in range(3):
    alive=vote_hull(P); p,n=surf_points(alive)
    keep=(p[:,1]>180)&(p[:,1]<700); p,n=p[keep],n[keep]
    sel=np.random.RandomState(it).choice(len(p),min(len(p),12000),replace=False); p,n=p[sel],n[sel]
    tot=0
    for i in range(N):
        nb=[j for j in (i-3,i+3,i-8,i+8) if 0<=j<N]
        b=P[i].copy(); bc=cost(i,b,p,n,P,nb)
        for stepth,stepx,stepy in ((np.radians(1.5),3,3),(np.radians(0.5),1,1)):
            for _ in range(4):
                imp=False
                for j,st in ((0,stepth),(1,stepx),(2,stepy)):
                    for sg in (-1,1):
                        cnd=b.copy(); cnd[j]+=sg*st; cc=cost(i,cnd,p,n,P,nb)
                        if cc<bc-1e-4: bc,b,imp=cc,cnd,True
                if not imp: break
        P[i]=b; tot+=bc
    print('pass',it,'cost',round(tot/N,4),'deg',np.degrees(P[[0,24,48,72,96,120,144],0]).round(0),'hull',alive.sum(),round(time.time()-t0),flush=True)
np.save('P5.npy',P)
