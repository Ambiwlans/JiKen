# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: KTest - Kanji test site JiKen
@description: Views/Routes
"""

#Flask
from flask import request, render_template, redirect, url_for, session, abort

#SQLAlch
from sqlalchemy import func #desc

import json

#Math
import numpy as np
import random
from scipy.optimize import minimize
from scipy.stats import norm
from scipy.integrate import quad

#Models
from .models import TestMaterial, \
    TestLog, QuestionLog, \
    MetaStatistics

#Session
from . import app, db


##########################################
### HELPER FNs
##########################################

# Our sigmoid/logistic function that we fit to the data
# e term allows a warp to find upper/lower bounds
def sigmoid(x, t, a, e):
    y = (1 / (1 + np.exp(t*(x-a)))) ** e
    return y

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
    if t <= 0: return 100
    if a < 1: return 100
    
    #Penalize very large jumps
    reg += np.log((t / last_t) + (last_t / t) - 1) / i       
    reg += (abs(a - last_a) / last_a) / (4 * i)
    print("Jump size penalty")
    print(np.log((t / last_t) + (last_t / t) - 1) / i   )
    print((abs(a - last_a) / last_a) / (4 * i))
            
    #Penalize shallowness while a is small
    reg += (np.log((0.01/t)+3)) / (((last_a/150)**3 + 1) * (i**.75))
    print("Shallowness penalty")
    print((np.log((0.01/t)+3)) / (((last_a/150)**3 + 1) * (i**.75)))
    
    #Penalize steepness while a is large
    reg += (np.log((t / 0.01)+3)) / (10 * (i**.75))
    print("Steepness penalty")
    print((np.log((t / 0.01)+3)) / (10 * (i**.75)))


    print("Cost:")
    print("t: " + str(t) + " -- a: " + str(a))
    print("last_t: " + str(last_t) + " -- last_a: " + str(last_a))
    print(str(np.mean(((pred_Y - true_Y)**2)/weights)*(np.mean(weights))) + " + " + str(reg))
    return np.mean(((pred_Y - true_Y)**2)/weights)*(np.mean(weights)) + reg

##########################################
### ROUTES
##########################################

@app.route("/")
def home():
    return render_template('home.html')

#TODO2 - bias first question towards more commonly known ones
#TODO5 - avoid recalculating everything each question - modify rather than redo
@app.route("/test")
def test():
    
    ###
    ### Log Answer/Score
    ###
    
    score = request.args.get('a')
    testmaterialid = request.args.get('q')
    
    if score is None or session['testlogid'] is None:
        # New Test, new log
        newTest = TestLog(
                a = db.session.query(MetaStatistics).first().default_kanji,
                t = db.session.query(MetaStatistics).first().default_tightness)
        
        db.session.add(newTest)
        db.session.commit()
        session['testlogid'] = newTest.id
        print("New Sess:" + str(session['testlogid']))
    else:
        # Log score
        score = bool(int(score))
    
        answered = QuestionLog(
                testlogid = session['testlogid'],
                testmaterialid = testmaterialid,
                score = score)
        db.session.add(answered)
        db.session.commit()
        
    ###
    ### Handle Data, Prep output
    ###
    
    history = db.session.query(QuestionLog, TestMaterial).join(TestMaterial).filter(QuestionLog.testlogid==session['testlogid'])
    
    
    #Get updated statistics and next question
    
    xdata = []
    ydata = []
    pred = [0,0,0]
    
    if score is None:
        #For the first question, ask a random kanji (for data gathering purposes)
        newquestion = db.session.query(TestMaterial).order_by(func.random()).first()
        db.session.query(TestLog).get(session['testlogid']).a = session['a'] = db.session.query(MetaStatistics).first().default_kanji
        db.session.query(TestLog).get(session['testlogid']).t = session['t'] = db.session.query(MetaStatistics).first().default_tightness
    else:
        result = history.order_by(TestMaterial.my_rank.desc()).all()
        
        for r in result:
            xdata.append(r.TestMaterial.my_rank)
            ydata.append(r.QuestionLog.score)
        
        # Get new LOBF (a, t values)
            #minimized using BFGS, custom cost fn
            #fit to Sigmoid fn:  1/(1 + e^(t(x-a)))
            #update our db and the session data
        
        p0 = [session['t'], session['a']]       # use last LOBF as starting point for new one
        
        res = minimize(sigmoid_cost_regularized, p0, args=(xdata, ydata, p0[0], p0[1]),method="Nelder-Mead")
            #,options={'eps': [0.0001,1]})#, bounds=[(0,10),(1,7000)])
        
        db.session.query(TestLog).get(session['testlogid']).a = session['a'] = res.x[1]
        db.session.query(TestLog).get(session['testlogid']).t = session['t'] = res.x[0]
        
        
        # Predict known kanji
        if len(result) > 10:
            #[mid, upper, lower]
            pred = [(quad(sigmoid,0,app.config['MAX_X'],args=(*res.x,1))[0]),
                        (quad(sigmoid,0,app.config['MAX_X'],args=(*res.x,.5))[0]),
                        (quad(sigmoid,0,app.config['MAX_X'],args=(*res.x,2))[0])]
            #fixed to clear all the knowns
            for r in result:
                pred[0] += (r.QuestionLog.score - sigmoid(r.TestMaterial.my_rank, *res.x, 1))
                pred[1] += (r.QuestionLog.score - sigmoid(r.TestMaterial.my_rank, *res.x, .5))
                pred[2] += (r.QuestionLog.score - sigmoid(r.TestMaterial.my_rank, *res.x, 2))
            
            pred = list(map(int,pred))
            print(pred)
            
        # Select next question
        
        # left half of graph if last question wrong, right half if correct (skew selection slightly away from the middle)
        if score == 1:
            x = int(logit((random.random()**.5)/2, *res.x))
        elif score == 0:
            x = int(logit((random.random()**.5)/(-2) + 1, *res.x))
        
        if x < 1 : x = 1
        if x > app.config['MAX_X']: x = app.config['MAX_X']
            
        # don't ask repeats
        searchkey = 1
        while history.filter(TestMaterial.my_rank==x).first() or x < 1 or x > app.config['MAX_X']:
            print("Already answered" + str(x))
            x += searchkey
            
            if searchkey > 0:
                searchkey = -searchkey - 1
            else:
                searchkey = -searchkey + 1
            
            if x > app.config['MAX_X'] and x + searchkey < 1: 
                print("Have asked every question!")
                x = 1
                break;
                
        print ("Selected letter #" + str(x))
        newquestion = db.session.query(TestMaterial).filter(TestMaterial.my_rank == x).first()

        
    #Get some history to show
    oldquestions = history.order_by(QuestionLog.id.desc()).limit(100)
    
    rightanswers = oldquestions.from_self().filter(QuestionLog.score == 1).all()
    rightanswers = [i.TestMaterial.my_rank for i in rightanswers]
    wronganswers = oldquestions.from_self().filter(QuestionLog.score == 0).all()
    wronganswers = [i.TestMaterial.my_rank for i in wronganswers]
    oldquestions = oldquestions.limit(10)
    return render_template('test.html', question = newquestion, oldquestions = oldquestions, wronganswers = json.dumps(wronganswers), rightanswers = json.dumps(rightanswers), pred = pred)











