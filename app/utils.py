# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: JiKen - Kanji testing site
@description: Utils
"""

#Math
import numpy as np
from scipy.stats import norm

##########################################
### HELPER FNs
##########################################

# Our sigmoid/logistic function that we fit to the data
# e term allows a warp to find upper/lower bounds
def sigmoid(x, t, a, e):
    return (1 / (1 + np.exp(t*(x-a)))) ** e

# Inverse of the logistical/sigmoid fn
    # used to grab x vals given y on our sigmoid
def logit(y, t, a):
    x = (np.log((1/y) - 1))/t + a
    return x

# Custom cost fn
    # used to fit our curve
    # Expected Ranges: 
        # Unregularized cost is 0~1
        # cost of 1 means that the prediction is 100% wrong
        
        # reg should be 0~.1
        
        # 0<t<inf
        # t is very steep > .1
        # t is shallow < .001
        
        # 0<a<6000
        # ~400 is average but this value need not be particularly penalized
def sigmoid_cost_regularized(params, true_X, true_Y, last_t, last_a):
    reg = 0
    t, a = params    
    i = len(true_X)
    
    # Get predictions from our sigmoid    
    pred_Y = sigmoid(true_X, t, a, 1)
    
    # Calculate the sample bias correcting array
        # Cortes, C., Mohri, M., Riley, M., & Rostamizadeh, A. (2008, October). Sample selection bias correction theory. In International conference on algorithmic learning theory (pp. 38-53). Springer, Berlin, Heidelberg.
            # https://cs.nyu.edu/~mohri/pub/bias.pdf
    
    #Fit a line across whole dataset
        # using a gaussian distribution for a close enough estimate (reality will be slightly left biased and have a clipped top)
        # Invert the dist for cost weights to correct sample bias    
    
    mean,std=norm.fit(true_X)
    dist = norm(mean,std)
    weights = dist.pdf(true_X)
    
    if i == 1:
        weights = 1
        
    #Regularization penalties
    
    #Clip OOB values
    if t <= 0: return (1 - t)*100
    if a < 1: return 100
    
    #Penalize very large jumps
    reg += np.log((t / last_t) + (last_t / t) - 1) / i       
    reg += (abs(a - last_a) / last_a) / (4 * i)

    #Penalize shallowness while a is small and early in test
    reg += (np.log((0.01/t)+3)) / (((last_a/150)**.3 + 1) * (i**.65))
    
    #Penalize steepness while early in test
    reg += (np.log((t / 0.01)+3)) / (10 * (i**.65))

#    print("")
#    print("Cost on question #" +  str(i) +":")
#    print("t: " + str(t) + ", last_t: " + str(last_t))
#    print("a: " + str(a) + ", last_a: " + str(last_a))
#    print("----")
#
#    print("Jump size penalty")
#    print(np.log((t / last_t) + (last_t / t) - 1) / i)
#    print((abs(a - last_a) / last_a) / (4 * i))
#    print("Shallowness penalty")
#    print((np.log((0.01/t)+3)) / (((last_a/150)**3 + 1) * (i**.75)))
#    print("Steepness penalty")
#    print((np.log((t / 0.01)+3)) / (10 * (i**.75)))
#    print("Total:")
#    print(str(np.mean(((pred_Y - true_Y)**2)/weights)*(np.mean(weights))) + " + " + str(reg))
    return np.mean(((pred_Y - true_Y)**2)/weights)*(np.mean(weights)) + reg