import numpy as np, cv2, sys
d=np.load('baked5.npz'); V=d['V']; F=d['F']; fu=d['fu']; fv=d['fv']
atlas=cv2.imread('atlas5.png'); AT=atlas.shape[0]
out=sys.argv[1]
# crop atlas to used rows
rows=int(np.ceil(fv.max()))+4; rows=min(AT,max(rows,64))
cv2.imwrite(out+'/girl.png',atlas[:rows])
# centre on feet, units: 1 px of video = 0.05 quake units later; keep px here
V=V.copy(); V[:,1]-=V[:,1].min(); V[:,0]-=V[:,0].mean(); V[:,2]-=V[:,2].mean()
with open(out+'/girl.mtl','w') as f: f.write('newmtl girl\nKd 1 1 1\nmap_Kd girl.png\n')
with open(out+'/girl.obj','w') as f:
    f.write('mtllib girl.mtl\nusemtl girl\n')
    for x,y,z in V: f.write(f'v {x:.2f} {y:.2f} {z:.2f}\n')
    U=fu.reshape(-1)/AT; Vt=1-fv.reshape(-1)/AT   # atlas pixel -> uv (v up)
    Vt=1-(fv.reshape(-1))/rows if False else 1-fv.reshape(-1)/rows
    U=fu.reshape(-1)/AT
    for a,b in zip(U,Vt): f.write(f'vt {a:.5f} {b:.5f}\n')
    for i,(a,b,c) in enumerate(F):
        f.write(f'f {a+1}/{3*i+1} {b+1}/{3*i+2} {c+1}/{3*i+3}\n')
print('rows',rows,'verts',len(V),'faces',len(F))
