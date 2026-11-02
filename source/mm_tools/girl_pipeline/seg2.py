import numpy as np, cv2, glob, os
files = sorted(glob.glob('all/f*.png'))
os.makedirs('mask', exist_ok=True)
for i,f in enumerate(files):
    im = cv2.imread(f); H,W = im.shape[:2]
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
    border = np.concatenate([lab[:, :40].reshape(-1,3), lab[:, -40:].reshape(-1,3), lab[:60].reshape(-1,3)])
    bgc = np.median(border,0)
    dab = np.sqrt((lab[...,1]-bgc[1])**2+(lab[...,2]-bgc[2])**2)
    dl = np.abs(lab[...,0]-bgc[0])
    score = dab*1.0 + 0.25*dl
    sure_fg = (dab>22).astype(np.uint8)
    sure_fg = cv2.erode(sure_fg, np.ones((5,5),np.uint8))
    # candidate region
    cand = ((dab>7)|(dl>45)).astype(np.uint8)
    cand = cv2.morphologyEx(cand, cv2.MORPH_CLOSE, np.ones((15,15),np.uint8))
    n,lbl,st,_ = cv2.connectedComponentsWithStats(cand)
    k = 1+np.argmax(st[1:,cv2.CC_STAT_AREA]); cand=(lbl==k).astype(np.uint8)
    gc = np.full((H,W), cv2.GC_BGD, np.uint8)
    gc[cv2.dilate(cand,np.ones((9,9),np.uint8))>0] = cv2.GC_PR_BGD
    gc[cand>0] = cv2.GC_PR_FGD
    gc[sure_fg>0] = cv2.GC_FGD
    b1=np.zeros((1,65)); b2=np.zeros((1,65))
    small = cv2.resize(im,(W//2,H//2)); gs = cv2.resize(gc,(W//2,H//2),interpolation=cv2.INTER_NEAREST)
    cv2.grabCut(small, gs, None, b1, b2, 4, cv2.GC_INIT_WITH_MASK)
    m = ((gs==cv2.GC_FGD)|(gs==cv2.GC_PR_FGD)).astype(np.uint8)
    m = cv2.resize(m,(W,H),interpolation=cv2.INTER_NEAREST)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
    n,lbl,st,_ = cv2.connectedComponentsWithStats(m)
    k = 1+np.argmax(st[1:,cv2.CC_STAT_AREA]); m=(lbl==k).astype(np.uint8)
    cnts,_ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    m2 = np.zeros_like(m); cv2.drawContours(m2, cnts, -1, 1, -1)
    cv2.imwrite(f'mask/m{i+1:03d}.png', m2*255)
rows=[]
for i in [1,30,60,90,120,145]:
    im=cv2.imread(f'all/f{i:03d}.png'); m=cv2.imread(f'mask/m{i:03d}.png',0)
    ov=im.copy(); ov[m>0]=(0.5*ov[m>0]+0.5*np.array([0,255,0])).astype(np.uint8)
    rows.append(cv2.resize(ov,(277,368)))
cv2.imwrite('segsheet.png', np.hstack(rows))
