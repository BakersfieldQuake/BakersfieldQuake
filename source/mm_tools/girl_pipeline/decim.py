import numpy as np, sys, fast_simplification as fs
d=np.load('mesh5.npz'); V=d['V'].astype(np.float32); F=d['F'].astype(np.int32)
for tag,target in (('hi',26000),('lo',5000)):
    red=1-target/len(F)
    P,Q=fs.simplify(V,F,target_reduction=red,agg=5)
    print(tag,len(V),len(F),'->',len(P),len(Q))
    np.savez(f'mesh_{tag}.npz',V=P.astype(np.float64),F=Q)
# bake variants
s=open('bake6.py').read()
for tag,target in (('hi',26000),('lo',5000)):
    t=s.replace("'mesh5.npz'",f"'mesh_{tag}.npz'")
    for n in ('atlas','baked','preview','head'):
        t=t.replace(n+'6.',n+f'_{tag}.')
    t=t.replace('csz[co]<500',f'csz[co]<{int(500*target/180000)+20}')
    open(f'bake_{tag}.py','w').write(t)
