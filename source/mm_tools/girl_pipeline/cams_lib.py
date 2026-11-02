import numpy as np, cv2, time
from scipy.ndimage import uniform_filter1d
N=145
masks=[cv2.imread(f'mask/m{i:03d}.png',0)>0 for i in range(1,N+1)]
H,W=masks[0].shape
masks_orig=masks
tops=[];bots=[]
for m in masks:
    ys,_=np.nonzero(m); tops.append(ys.min()); bots.append(ys.max())
import os
if os.environ.get('CLEAN')=='1': masks=[cv2.imread(f'mask2/m{i:03d}.png',0)>0 for i in range(1,N+1)]
CX=415.0
th0=np.load('theta.npy')
# params per frame: theta, dx, dy, s
P=np.zeros((N,4)); P[:,0]=th0; P[:,3]=[(bots[i]-tops[i])/1000. for i in range(N)]
def grid(VS,NX,NY,NZ):
    xs=(np.arange(NX)-NX/2+.5)*VS; ys=(np.arange(NY)+.5)*VS; zs=(np.arange(NZ)-NZ/2+.5)*VS
    return xs,ys,zs
def proj(x,y,z,i,p):
    th,dx,dy,s=p
    u=CX+dx+(x*np.cos(th)+z*np.sin(th))*s
    v=bots[i]+dy-y*s
    return u,v
def carve_pts(x,y,z,idx,Pm,margin=0):
    alive=np.ones(len(x),bool)
    for i in idx:
        u,v=proj(x,y,z,i,Pm[i]); ui=np.round(u).astype(int); vi=np.round(v).astype(int)
        ok=(ui>=0)&(ui<W)&(vi>=0)&(vi<H)
        ins=np.zeros(len(x),bool); ins[ok]=masks[i][vi[ok],ui[ok]]
        alive&=ins
    return alive
VS=5.0; NX,NY,NZ=96,204,96
xs,ys,zs=grid(VS,NX,NY,NZ)
def iou_dense(px,py,pz,i,p,k=9):
    u,v=proj(px,py,pz,i,p); ui=np.round(u).astype(int); vi=np.round(v).astype(int)
    img=np.zeros((H,W),np.uint8); ok=(ui>=0)&(ui<W)&(vi>=0)&(vi<H); img[vi[ok],ui[ok]]=1
    img=cv2.morphologyEx(img,cv2.MORPH_CLOSE,np.ones((k,k),np.uint8))
    m=masks[i]; return (img>0)&m, (img>0), m
VS=5.0; NX,NY,NZ=96,204,96
xs,ys,zs=grid(VS,NX,NY,NZ)
X,Y,Z=[a.ravel() for a in np.meshgrid(xs,ys,zs,indexing='ij')]
