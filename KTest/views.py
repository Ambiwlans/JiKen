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

#Math
import numpy as np
from scipy.optimize import curve_fit
from bisect import bisect

#DEV Graphing
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

#Models
from .models import TestMaterial, \
    TestLog, QuestionLog

#Session
from . import app, db


##########################################
### HELPER FN
##########################################

def sigmoid(x, t, a):
    y = 1 / (1 + np.exp(t*(x-a)))
    return y

##########################################
### ROUTES
##########################################

@app.route("/")
def home():
    return render_template('home.html')

#TODO - allow more variance/fuzzier selection (rather than exactly mid)
#TODO - allow a wrap/better kanji selection when hitting an already answered on
#TODO - more optimistic selections (1 wrong, 30 right shouldn't result in a tight selection)

#TODO - show the estimate + variance
#TODO - tidy the 'handle data' section
#TODO - replace magic number 400 in line: p0 = [0.05,400]
#TODO2 - show user the graph? 
    # Add vertical lines for answered questions
    # use chart.js?
#TODO2 - clean up views
#TODO3 - error bars? Ask questions at point of largest error bars?
#TODO4 - clientside the math?
#TODO5 - avoid recalculating everything each question - modify rather than redo
#TODO5 - clear out superfluous DEV code
    
@app.route("/test")
def test():
    
    ###
    ### Collect Data/Setup
    ###
    
    #Get answer/score
    score = request.args.get('a')
    testmaterialid = request.args.get('q')
    
    if score is None or session['testlogid'] is None:
        # New Test, new log
        newTest = TestLog()
        db.session.add(newTest)
        db.session.commit()
        session['testlogid'] = newTest.id
        print("New Sess:" + str(session['testlogid']))
    else:
        # Log score
        answered = QuestionLog(
                testlogid = session['testlogid'],
                testmaterialid = testmaterialid,
                score = bool(int(score)))
        db.session.add(answered)
        db.session.commit()
        
    ###
    ### Handle Data, Prep output
    ###
    
    history = db.session.query(QuestionLog).filter(QuestionLog.testlogid==session['testlogid'])
    
    
    #Get updated statistics and next question
    
    #For the first question, ask a random kanji (for data gathering purposes)
    
    xdata = []
    ydata = []
    
    if history.count() == 0:
        newquestion = db.session.query(TestMaterial).order_by(func.random()).first()
    else:
        result = history.all()
        print("RESULT: " + str(result))
        
        
        for r in result:
            xdata.append(r.testmaterialid)
            ydata.append(r.score)

        print("Xdata: " + str(xdata))
        print("Ydata: " + str(ydata))
        
        #Create new LOBF
            #fit to Sigmoid fn:  1/(1 + e^(t(x-a)))
            # minimize t?
        
        p0 = [0.05,400] # 400 should be the kanji 50% of people on avg know

        popt, pcov = curve_fit(sigmoid, xdata, ydata, p0, sigma=[.5]*len(xdata), bounds=([0.001, 2], [.1,1500]), method='dogbox')
        
        x = np.linspace(0, 1500, 1500)
        y = sigmoid(x, *popt)

        #DEV
        fig = plt.figure()
        plt.plot(xdata, ydata, 'o', label='data')
        plt.plot(x,y, label='fit')
        plt.ylim(0, 1)
        plt.xlim(-100, 1500)
        plt.legend(loc='best')
        fig.savefig('C:/Users/Angelo/Documents/Code/Python/KTest/testimagepython.png')
        
  
        mid = 0
        while y[mid] > .5:
            mid += 1
            if mid == 999: break   #biggest kanji atm TODO
            

        print ("Mid point is letter: " + str(mid))
        print ("Mid point val: " + str(y[mid]))
        
            
        while history.filter(QuestionLog.testmaterialid==mid).first():
            mid += 1
            if mid == 999: break   #biggest kanji atm TODO
            print("Already answered" + str(mid))
            
        newquestion = db.session.query(TestMaterial).filter(TestMaterial.id == mid).first()
        
    #Get some history to show
    oldquestions = history.order_by(QuestionLog.id.desc()).limit(10)
    
#    for q in oldquestions:
#        print("Old Q:" + str(q.testmaterial.id))
    return render_template('test.html', question = newquestion, oldquestions = oldquestions)











