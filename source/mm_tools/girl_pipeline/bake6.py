import numpy as np, cv2, time, sys
from scipy import sparse
import cams_lib as c
N,H,W=c.N,c.H,c.W
P=np.load('P5.npy'); d=np.load('mesh5.npz'); V=d['V'].astype(np.float64); F=d['F']
nF=len(F)
tri=V[F]; fn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); area=np.linalg.norm(fn,axis=1); fn/=area[:,None]+1e-12
cen=tri.mean(1)
if (fn*(cen-V.mean(0))).sum()<0: fn=-fn; F=F[:,[0,2,1]]
# key frames: thetas nearest every 30 deg, skip frame 0 (odd exposure)
th=np.unwrap(P[:,0]); targets=th[1]-np.radians(30)*np.arange(12)
keys=[int(np.argmin(np.abs(th[1:]-t)))+1 for t in targets]; keys=sorted(set(keys),key=lambda k:-th[k]); print('key order',keys)
print('keys',keys,np.degrees(th[keys]).round(0))
imgs={k:cv2.imread(f'all/f{k+1:03d}.png') for k in keys}
dts={k:cv2.distanceTransform(c.masks[k].astype(np.uint8),cv2.DIST_L2,5) for k in keys}
# face adjacency
e=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]); fid=np.tile(np.arange(nF),3)
es=np.sort(e,1); key=es[:,0].astype(np.int64)*len(V)+es[:,1]; o=np.argsort(key); key=key[o]; fo=fid[o]
same=key[1:]==key[:-1]; a=fo[:-1][same]; b=fo[1:][same]
Adj=sparse.coo_matrix((np.ones(len(a)),(a,b)),shape=(nF,nF)); Adj=(Adj+Adj.T).tocsr()
deg=np.asarray(Adj.sum(1)).ravel()+1e-9
# scores per key frame
S=np.zeros((len(keys),nF),np.float32)
Vn=np.zeros_like(V)
for j,k in enumerate(keys):
    t=P[k,0]; cam=np.array([-np.sin(t),0,np.cos(t)])
    u,v=c.proj(V[:,0],V[:,1],V[:,2],k,P[k]); depth=-V[:,0]*np.sin(t)+V[:,2]*np.cos(t)
    ui=np.round(u).astype(int); vi=np.round(v).astype(int)
    ok=(ui>=0)&(ui<W)&(vi>=0)&(vi<H)
    zb=np.full((H,W),-1e9,np.float32)
    np.maximum.at(zb,(vi[ok],ui[ok]),depth[ok])
    zb=cv2.dilate(zb,np.ones((5,5),np.uint8))
    # face visibility from its 3 vertices + centroid
    uc,vc=c.proj(cen[:,0],cen[:,1],cen[:,2],k,P[k]); dc=-cen[:,0]*np.sin(t)+cen[:,2]*np.cos(t)
    uci=np.clip(np.round(uc).astype(int),0,W-1); vci=np.clip(np.round(vc).astype(int),0,H-1)
    vis=dc>=zb[vci,uci]-8
    facing=np.clip(fn@cam,0,1)
    edge=np.clip(dts[k][vci,uci]/10,0,1)
    S[j]=(facing**1.5*edge*vis).astype(np.float32)
# smooth scores over adjacency
Ss=S.copy()
for _ in range(6): Ss=0.5*Ss+0.5*(Adj@Ss.T).T/deg
lab=np.argmax(Ss,0)
inv=S.max(0)<=1e-4
head=(cen[:,1]>875)&(S[0]>0.12)
forced=np.zeros(nF,bool)
camv=lambda k: np.array([-np.sin(P[k,0]),0,np.cos(P[k,0])])
f0=np.clip(fn@camv(keys[0]),0,1); f6=np.clip(fn@camv(keys[6]),0,1)
def inside(k):
    u,v=c.proj(cen[:,0],cen[:,1],cen[:,2],keys[k],P[keys[k]])
    ui=np.clip(np.round(u).astype(int),0,W-1); vi=np.clip(np.round(v).astype(int),0,H-1)
    return dts[keys[k]][vi,ui]>=3
ff=(((f0>0.55)&inside(0))|((cen[:,1]>875)&(S[0]>0.12))); lab[ff]=0; forced|=ff
fb=(f6>0.55)&inside(6)&~ff; lab[fb]=6; forced|=fb
oneh=lambda l: sparse.csr_matrix((np.ones(nF),(np.arange(nF),l)),shape=(nF,len(keys)))
for _ in range(6):
    nbv=(Adj@oneh(lab)).toarray()/deg[:,None]
    s2=Ss.T+0.45*nbv
    nl=np.argmax(s2,1); nl[forced]=lab[forced]; nl[inv]=lab[inv]; lab=nl
lab[S.max(0)<=1e-4]=np.argmax(Ss[:,S.max(0)<=1e-4],0) if (S.max(0)<=1e-4).any() else 0
print('label counts',np.bincount(lab,minlength=len(keys)))
# charts = connected comps of same label
m=lab[a]==lab[b]
Ac=sparse.coo_matrix((np.ones(m.sum()),(a[m],b[m])),shape=(nF,nF))
from scipy.sparse.csgraph import connected_components
nc,chart=connected_components(Ac,directed=False)
print('charts',nc)
# per chart bbox in source frame
uv_u=np.zeros((nF,3)); uv_v=np.zeros((nF,3))
for j,k in enumerate(keys):
    idx=np.nonzero(lab==j)[0]
    for q in range(3):
        u,v=c.proj(V[F[idx,q],0],V[F[idx,q],1],V[F[idx,q],2],k,P[k]); uv_u[idx,q]=u; uv_v[idx,q]=v
AT=4096; PAD=3
charts=[]
for ch in range(nc):
    idx=np.nonzero(chart==ch)[0]
    x0=int(np.floor(uv_u[idx].min()))-PAD; x1=int(np.ceil(uv_u[idx].max()))+PAD
    y0=int(np.floor(uv_v[idx].min()))-PAD; y1=int(np.ceil(uv_v[idx].max()))+PAD
    charts.append((ch,lab[idx[0]],x0,y0,x1-x0+1,y1-y0+1))
# shelf pack, tallest first
charts.sort(key=lambda t:-t[5])
atlas=np.zeros((AT,AT,3),np.uint8); X0=Y0=0; rowh=0; place={}
for ch,l,x0,y0,w,h in charts:
    if X0+w>AT: X0=0; Y0+=rowh; rowh=0
    if Y0+h>AT: print('ATLAS FULL at chart',ch); break
    k=keys[l]; src=imgs[k]
    sx0,sy0=max(0,x0),max(0,y0); sx1,sy1=min(W,x0+w),min(H,y0+h)
    atlas[Y0+(sy0-y0):Y0+(sy1-y0),X0+(sx0-x0):X0+(sx1-x0)]=src[sy0:sy1,sx0:sx1]
    place[ch]=(X0-x0,Y0-y0); X0+=w; rowh=max(rowh,h)
print('atlas rows used',Y0+rowh)
# face UVs in atlas pixels
fu=np.zeros((nF,3)); fv=np.zeros((nF,3))
for f in range(nF):
    pass
offx=np.array([place[chart[f]][0] if chart[f] in place else 0 for f in range(nF)]); offy=np.array([place[chart[f]][1] if chart[f] in place else 0 for f in range(nF)])
fu=uv_u+offx[:,None]; fv=uv_v+offy[:,None]
_cu=np.clip(np.round(fu.mean(1)).astype(int),0,AT-1); _cv=np.clip(np.round(fv.mean(1)).astype(int),0,AT-1)
_col=atlas[_cv,_cu].astype(int)
neutral=((_col.max(1)-_col.min(1))<75)&(_col.mean(1)>140)&(cen[:,1]<135)
print('neutral shoe-level faces',neutral.sum())
bad=inv|neutral; inv=bad.copy(); Adj_l=Adj.tolil().rows
for rnd in range(8):
    nb=np.nonzero(bad)[0]
    if len(nb)==0: break
    for f in nb:
        for g in Adj_l[f]:
            if not bad[g]:
                fu[f]=fu[g].mean(); fv[f]=fv[g].mean(); bad[f]=False; break
print('invalid faces',inv.sum(),'unfixed',bad.sum())
# outlier colour patches (hair/skin bleed onto shirt/shoes): small components far from ring-mean colour
cu_=np.clip(np.round(fu.mean(1)).astype(int),0,AT-1); cv2_=np.clip(np.round(fv.mean(1)).astype(int),0,AT-1)
colf=atlas[cv2_,cu_].astype(np.float32)
An=sparse.diags(1/deg)@Adj
M=colf.copy()
for _ in range(4): M=An@M
reg=((cen[:,1]>650)&(cen[:,1]<860))|(cen[:,1]<140)
outl=(np.linalg.norm(colf-M,axis=1)>55)&reg
mo=outl[a]&outl[b]
Ao=sparse.coo_matrix((np.ones(mo.sum()),(a[mo],b[mo])),shape=(nF,nF))
nco,co=connected_components(Ao,directed=False)
csz=np.bincount(co); small=(csz[co]<500)&outl
print('outlier faces',outl.sum(),'small-comp',small.sum())
bad=small.copy()
for rnd in range(10):
    nb=np.nonzero(bad)[0]
    if len(nb)==0: break
    for f in nb:
        for g in Adj_l[f]:
            if not bad[g] and not small[g]:
                fu[f]=fu[g].mean(); fv[f]=fv[g].mean(); bad[f]=False; break
print('outlier unfixed',bad.sum())
cv2.imwrite('atlas6.png',atlas)
np.savez('baked6.npz',V=V,F=F,fu=fu,fv=fv,lab=lab,keys=np.array(keys))


def render(yaw,scale=1.0,size=(520,1040),ss=2,focus=None):
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
    for k in idx:
        cv2.fillConvexPoly(img,np.ascontiguousarray(pts[k].reshape(3,1,2)),tuple(int(q) for q in col[k]))
    return cv2.resize(img,size,interpolation=cv2.INTER_AREA)
cv2.imwrite('preview6.png',np.hstack([render(np.radians(a)) for a in (0,50,120,200)]))
cv2.imwrite('head6.png',render(np.radians(0),scale=3.2,size=(800,700),focus=(0,930)))
