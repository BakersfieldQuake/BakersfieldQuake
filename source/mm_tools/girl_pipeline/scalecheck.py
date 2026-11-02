import numpy as np
src=open('flipcheck.py').read().split("Pn=P.copy()")[0]
exec(src)
P4=np.load('P4.npy')
for sc in (0.95,1.0,1.1,1.196,1.3):
    Q=P4.copy(); Q[:,0]=P4[0,0]+(P4[:,0]-P4[0,0])*sc
    print('scale',sc,'total',np.degrees(Q[-1,0]-Q[0,0]).round(0),'cost',photocost(Q))
