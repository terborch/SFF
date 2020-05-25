from matplotlib import pyplot as plt
import numpy as np

size_ref = 42
cost_ref = 1350*1.06

interp = [29,31]

size = np.arange(10,60,1)
Cost = np.zeros(len(size))



def cost(size):
    return cost_ref*(size/size_ref)**0.6

for i, s in enumerate(size):
    Cost[i] = cost(s)

plt.plot(size, Cost)



a, b = (cost(i) for i in interp)

m = (a - b)/(interp[0] - interp[1])

h = a - m*interp[0]

cost_linnear = m*size + h

plt.plot(size, cost_linnear)

print(m,h)