
"""
Test program to compare angle gate velocity versions

ga uit van een skiff sessie!!

"""
import numpy as np
import math
from scipy import signal

import matplotlib.pyplot as plt

from utils import *
import globalData as gd
import main

main.interactive()

header = gd.sessionInfo['Header']
print(header)
print('Pieces')
print(gd.sessionInfo['Pieces'])
nm, aa, (scnt, r), sp = gd.sessionInfo['Pieces'][0]

gd.dataObject.shape
#plt.plot(gd.dataObject[:, 0])
print(f' nm {nm} ====  {gd.norm_arrays.shape}  \n  {sp}\n')
#plt.plot(gd.norm_arrays[0, :, 1], label=header[1])
#  7 voor skiff en 25 voor 8
plt.plot(math.pi*gd.norm_arrays[0, :, 25]/180,  label=header[7])

q, aa = gd.prof_data[0]
print(f'prof_data {aa} \n  max power {np.max(aa[0])}  max vel {np.max(aa[1])}  max gateAngleVel {math.pi*np.max(gd.norm_arrays[0, :, 7]/180)}')

plt.plot(aa[1], label='vel') # uitgerekende gateanglevel

# calculate velocity directly from angle
[B, A] = signal.butter(4, 2*5/Hz)


# plt.plot(gateAngleVel,  label='vel')

leg = plt.legend(loc='upper right')

plt.show()
