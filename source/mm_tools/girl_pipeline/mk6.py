s = open('bake5.py').read()
marker = "print('invalid faces',inv.sum(),'unfixed',bad.sum())\n"
add = marker + '''# outlier colour patches (hair/skin bleed onto shirt/shoes): small components far from ring-mean colour
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
'''
assert marker in s
t = s.replace(marker, add)
for n in ('atlas', 'baked', 'preview', 'head'):
    t = t.replace(n + '5.', n + '6.')
open('bake6.py', 'w').write(t)
print('ok')
