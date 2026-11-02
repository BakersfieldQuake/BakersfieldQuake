import numpy as np, cv2
for i in range(1,146):
    im=cv2.imread(f'all/f{i:03d}.png'); m=cv2.imread(f'mask/m{i:03d}.png',0)>0
    lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(np.float32)
    border=np.concatenate([lab[:, :40].reshape(-1,3),lab[:, -40:].reshape(-1,3),lab[:60].reshape(-1,3)]); bg=np.median(border,0)
    dab=np.sqrt((lab[...,1]-bg[1])**2+(lab[...,2]-bg[2])**2)
    ys,_=np.nonzero(m); bot=ys.max()
    rows=np.zeros_like(m); rows[max(0,bot-110):]=True
    cut=m&rows&(dab<9)            # neutral grey = floor shadow
    m2=m&~cut
    m2=cv2.morphologyEx(m2.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    n,l,st,_=cv2.connectedComponentsWithStats(m2); k=1+np.argmax(st[1:,cv2.CC_STAT_AREA]); m2=(l==k)
    cv2.imwrite(f'mask2/m{i:03d}.png',m2.astype(np.uint8)*255)
print('ok')
