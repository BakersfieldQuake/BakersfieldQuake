import numpy as np, cv2, sys
def load(tag='5'):
    d=np.load(f'baked{tag}.npz'); atlas=cv2.imread(f'atlas{tag}.png')
    return d['V'],d['F'],d['fu'],d['fv'],atlas
def render(M,yaw,scale=1.0,size=(520,1040),ss=2,focus=None):
    V,F,fu,fv,atlas=M; AT=atlas.shape[0]
    tri=V[F]; fn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); fn/=np.linalg.norm(fn,axis=1,keepdims=True)+1e-9
    cen=tri.mean(1)
    if (fn*(cen-V.mean(0))).sum()<0: fn=-fn
    c_,s_=np.cos(yaw),np.sin(yaw)
    x=V[:,0]*c_+V[:,2]*s_; d=-V[:,0]*s_+V[:,2]*c_
    W_,H_=size[0]*ss,size[1]*ss; sc=scale*ss
    if focus is None: ox,oy=W_/2,H_-20*ss
    else: ox,oy=W_/2-focus[0]*sc,H_/2+focus[1]*sc
    pu=x*sc+ox; pv=oy-V[:,1]*sc
    cam=np.array([-s_,0,c_]); front=(fn@cam)>-0.05
    cu=np.clip(np.round(fu.mean(1)).astype(int),0,AT-1); cv_=np.clip(np.round(fv.mean(1)).astype(int),0,AT-1)
    col=atlas[cv_,cu]
    dc=d[F].mean(1); idx=np.nonzero(front)[0]; idx=idx[np.argsort(dc[idx])]
    img=np.full((H_,W_,3),235,np.uint8)
    pts=np.stack([pu[F],pv[F]],2).astype(np.int32)
    for k in idx: cv2.fillConvexPoly(img,np.ascontiguousarray(pts[k].reshape(3,1,2)),tuple(int(q) for q in col[k]))
    return cv2.resize(img,size,interpolation=cv2.INTER_AREA)
if __name__=='__main__':
    M=load(sys.argv[1] if len(sys.argv)>1 else '5')
    a=render(M,np.radians(0),scale=3.0,size=(700,520),focus=(0,60))
    b=render(M,np.radians(40),scale=3.0,size=(700,520),focus=(0,60))
    c=render(M,np.radians(0),scale=3.0,size=(700,520),focus=(0,740))
    cv2.imwrite('closeups.png',np.vstack([np.hstack([a,b]),np.hstack([c,render(M,np.radians(-60),scale=3.0,size=(700,520),focus=(0,740))])]))
