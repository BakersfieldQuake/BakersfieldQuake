import numpy as np, cv2, time
from scipy import ndimage, sparse
from skimage import measure
import cams_lib as c
N,H,W=c.N,c.H,c.W
P=np.load('P5.npy')
dm=[cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8))>0 for m in c.masks]
# coarse candidate from vote hull at VS=5
cnt=np.zeros(len(c.X),np.int16)
for i in range(N):
    u,v=c.proj(c.X,c.Y,c.Z,i,P[i]); ui=np.round(u).astype(int); vi=np.round(v).astype(int)
    ok=(ui>=0)&(ui<W)&(vi>=0)&(vi<H); ins=np.zeros(len(c.X),bool); ins[ok]=dm[i][vi[ok],ui[ok]]; cnt+=ins
A=(cnt>=0.80*N).reshape(c.NX,c.NY,c.NZ)
A=ndimage.binary_dilation(A,iterations=2)
VS=3.0; NX,NZ,NY=164,164,344
xs=(np.arange(NX)-NX/2+.5)*VS; ys=(np.arange(NY)+.5)*VS; zs=(np.arange(NZ)-NZ/2+.5)*VS
# candidate fine voxels
gi=np.nonzero(np.ones((NX,NY,NZ),bool))
fx,fy,fz=np.meshgrid(xs,ys,zs,indexing='ij')
cx=np.clip(((fx/5.0)+c.NX/2-.5+0.5).astype(int),0,c.NX-1); cy=np.clip(((fy/5.0)-.5+.5).astype(int),0,c.NY-1); cz=np.clip(((fz/5.0)+c.NZ/2-.5+.5).astype(int),0,c.NZ-1)
cand=A[cx,cy,cz]
print('candidates',cand.sum())
x,y,z=fx[cand],fy[cand],fz[cand]
cn=np.zeros(len(x),np.int16)
for i in range(N):
    u,v=c.proj(x,y,z,i,P[i]); ui=np.round(u).astype(int); vi=np.round(v).astype(int)
    ok=(ui>=0)&(ui<W)&(vi>=0)&(vi<H); ins=np.zeros(len(x),bool); ins[ok]=dm[i][vi[ok],ui[ok]]; cn+=ins
fr=cn/N; fr=np.where(y<110,np.minimum(1.0,fr+0.08),fr)
field=np.zeros((NX,NY,NZ),np.float32); field[cand]=fr
field=ndimage.gaussian_filter(field,1.2)
lab,n=ndimage.label(field>0.85); sz=ndimage.sum(field>0.85,lab,range(1,n+1)); keep=lab==(1+np.argmax(sz)); field=field*ndimage.binary_dilation(keep,iterations=3)
v,f,_,_=measure.marching_cubes(field,0.86)
V=np.stack([(v[:,0]-NX/2+.5)*VS,(v[:,1]+.5)*VS,(v[:,2]-NZ/2+.5)*VS],1)
# Taubin smoothing
E=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]); 
A_=sparse.coo_matrix((np.ones(len(E)),(E[:,0],E[:,1])),shape=(len(V),len(V))); A_=((A_+A_.T)>0).astype(np.float32)
deg=np.asarray(A_.sum(1)).ravel(); L=sparse.diags(1/deg)@A_
for _ in range(8):
    V=V+0.5*(L@V-V); V=V-0.53*(L@V-V)
np.savez('mesh5.npz',V=V,F=f)
print('verts',len(V),'faces',len(f),'height',V[:,1].min(),V[:,1].max(),'x',V[:,0].min(),V[:,0].max(),'z',V[:,2].min(),V[:,2].max())
