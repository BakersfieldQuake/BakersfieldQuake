import numpy as np, cv2, time, os
from scipy import ndimage
import cams_lib as c
N,H,W=c.N,c.H,c.W
P=np.load('P2.npy').copy(); P[:,0]*=-1; P[:,1]=0; P[:,2]=0
dm=[cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8))>0 for m in c.masks]
grays=[cv2.GaussianBlur(cv2.cvtColor(cv2.imread(f'all/f{i+1:03d}.png'),cv2.COLOR_BGR2GRAY),(0,0),1.0) for i in range(N)]
t0=time.time()
if os.path.exists('flows.npy'): FL=np.load('flows.npy')
else:
    dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    FL=np.zeros((N-1,H//2,W//2,2),np.float32)
    for t in range(N-1):
        f=dis.calc(grays[t],grays[t+1],None)
        FL[t]=cv2.resize(f,(W//2,H//2),interpolation=cv2.INTER_AREA)  # flow in full-res px units retained below
    np.save('flows.npy',FL)
print('flows',FL.shape,round(time.time()-t0),flush=True)
def vote_hull(P,ratio=0.88,step=2):
    cnt=np.zeros(len(c.X),np.int16); used=0
    for i in range(0,N,step):
        u,v=c.proj(c.X,c.Y,c.Z,i,P[i]); ui=np.round(u).astype(int); vi=np.round(v).astype(int)
        ok=(ui>=0)&(ui<W)&(vi>=0)&(vi<H); ins=np.zeros(len(c.X),bool); ins[ok]=dm[i][vi[ok],ui[ok]]; cnt+=ins; used+=1
    return cnt>=ratio*used
def surf_points(alive):
    A=alive.reshape(c.NX,c.NY,c.NZ)
    f=ndimage.gaussian_filter(A.astype(np.float32),1.5); gx,gy,gz=np.gradient(f)
    sm=A&~ndimage.binary_erosion(A); idx=np.nonzero(sm)
    n=-np.stack([gx[idx],gy[idx],gz[idx]],1); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-9
    p=np.stack([c.xs[idx[0]],c.ys[idx[1]],c.zs[idx[2]]],1)
    return p,n
def est_omega(t,p,n,P):
    th=P[t,0]; cam=np.array([-np.sin(th),0,np.cos(th)])
    sel=((n@cam)>0.4)
    q=p[sel]
    u,v=c.proj(q[:,0],q[:,1],q[:,2],t,P[t])
    ok=(u>3)&(u<W-4)&(v>3)&(v<H-4)
    q=q[ok];u=u[ok];v=v[ok]
    inm=c.masks[t][np.round(v).astype(int),np.round(u).astype(int)]
    q,u,v=q[inm],u[inm],v[inm]
    if len(q)<300: return 0.0,0.0,0.0,9
    fl=FL[t]
    uo=cv2.remap(fl[...,0],(u/2).astype(np.float32)[None],(v/2).astype(np.float32)[None],cv2.INTER_LINEAR)[0]
    vo=cv2.remap(fl[...,1],(u/2).astype(np.float32)[None],(v/2).astype(np.float32)[None],cv2.INTER_LINEAR)[0]
    uo*=1.0; vo*=1.0           # flows were computed at full res then area-resized: magnitudes still in full-res px
    s=P[t,3]
    best=(9,0,0)
    for om in np.radians(np.arange(-14,14.01,0.1)):
        du=s*(q[:,0]*(np.cos(th+om)-np.cos(th))+q[:,2]*(np.sin(th+om)-np.sin(th)))
        r=uo-du; T=0.0; res=np.minimum(np.abs(r),6.0).mean()
        if res<best[0]: best=(res,om,T)
    return best[1],best[2],np.median(vo),best[0]
for it in range(4):
    alive=vote_hull(P); p,n=surf_points(alive)
    keep=(p[:,1]>150)&(p[:,1]<760); p,n=p[keep],n[keep]
    sel=np.random.RandomState(it).choice(len(p),min(len(p),8000),replace=False); p,n=p[sel],n[sel]
    om=np.zeros(N-1);Tx=np.zeros(N-1);err=np.zeros(N-1)
    newP=P.copy()
    for t in range(N-1):
        om[t],Tx[t],_,err[t]=est_omega(t,p,n,newP)
        newP[t+1,0]=newP[t,0]+om[t]; newP[t+1,1]=newP[t,1]
    P=newP
    print('iter',it,'hull',alive.sum(),'total deg',np.degrees(om.sum()).round(1),'mean err',err.mean().round(2),
          'deg@',np.degrees(P[[0,24,48,72,96,120,144],0]-P[0,0]).round(0),round(time.time()-t0),flush=True)
    np.save('P4.npy',P)
