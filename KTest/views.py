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
from scipy.optimize import curve_fit, minimize

#Models
from .models import TestMaterial, \
    TestLog, QuestionLog, \
    MetaStatistics

#Session
from . import app, db


##########################################
### HELPER FN
##########################################

#DEV - TEMP
@app.route("/calc_ranks")
def calc_ranks():
    data = db.session.query(TestMaterial).all()
#    cur_rank = db.session.query(TestMaterial).filter(TestMaterial.frequency is not None).count()
#    print("Cur rank: " + str(cur_rank))
    
#    for item in data:
#        if "Kyōiku-Jōyō (1st" in item.grade:
#            item.grade = 1
#        elif "Kyōiku-Jōyō (2nd" in item.grade:
#            item.grade = 2
#        elif "Kyōiku-Jōyō (3rd" in item.grade:
#            item.grade = 3
#        elif "Kyōiku-Jōyō (4th" in item.grade:
#            item.grade = 4
#        elif "Kyōiku-Jōyō (5th" in item.grade:
#            item.grade = 5
#        elif "Kyōiku-Jōyō (6th" in item.grade:
#            item.grade = 6
#        elif "Jōyō (1st" in item.grade:
#            item.grade = 7
#        elif "Jōyō (2nd" in item.grade:
#            item.grade = 8
#        elif "Jōyō (3rd" in item.grade:
#            item.grade = 9
#        elif "Kyōiku-Jōyō (high" in item.grade:
#            item.grade = 10
#        elif "Hyōgaiji (former Jinmeiyō candidate)" in item.grade:
#            item.grade = 11
#        elif "Jinmeiyō (used in names)" in item.grade:
#            item.grade = 13
#        else:
#            item.grade = 14
#            
#        if "1" in (item.jlpt or ""):
#            item.jlpt = 1
#        elif "2" in (item.jlpt or ""):
#            item.jlpt = 2
#        elif "3" in (item.jlpt or ""):
#            item.jlpt = 3
#        elif "4" in (item.jlpt or ""):
#            item.jlpt = 4
#        elif "5" in (item.jlpt or ""):
#            item.jlpt = 5
#        else:
#            item.jlpt = 6
            
#        item.meaning = item.meaning.replace(";","; ")
        
#        item.my_rank = int(item.frequency or 0)
#        
#        if item.frequency is None:
#            
#            item.my_rank = 7000    
            
    return render_template('home.html')    
    
def sigmoid(x, t, a):
    y = 1 / (1 + np.exp(t*(x-a))) #2**x
    return y

def sigmoid_cost_regularized(params, true_X, true_Y):
    
    t, a = params
    
    pred_Y = sigmoid(true_X, t, a)
    
    #Ranges: 
        # Unregularized cost is 0~1
        # cost of 1 means that the prediction is 100% wrong
        
        # reg should be 0~.1
        
        # 0<t<inf
        # t is very steep > .1
        # t is shallow < .001
        
        # 0<a<6000
        # ~400 is average but this value need not be particularly penalized
        
    #penalties for overly flat or steep slopes, a far from the average
    reg = t + (1/t)/10000 + abs(a - db.session.query(MetaStatistics).first().default_kanji)/100000
    if t < 0: reg += 10
    if a < 0: reg += 10
#    if a > 3000: reg += a - 3000

    regweight = 1
    print("")
    print(str(t)+" + "+str(a))
    print(str(np.mean((pred_Y - true_Y)**2)) + " + " + str(reg * regweight))
    return np.mean((pred_Y - true_Y)**2) + reg * regweight

##########################################
### ROUTES
##########################################

@app.route("/")
def home():
    return render_template('home.html')

    
#TODO2 - bias first question towards more commonly known ones
#TODO3 - error bars? Ask questions at point of largest error bars?
#TODO5 - avoid recalculating everything each question - modify rather than redo
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
    
    #For the first question, ask a random kanji (for data gathering purposes)
    
    xdata = []
    ydata = []
    
    if history.count() == 0:
        newquestion = db.session.query(TestMaterial).order_by(func.random()).first()
        db.session.query(TestLog).get(session['testlogid']).a = session['a'] = db.session.query(MetaStatistics).first().default_kanji
        db.session.query(TestLog).get(session['testlogid']).t = session['t'] = db.session.query(MetaStatistics).first().default_tightness
    else:
        result = history.order_by(TestMaterial.my_rank.desc()).all()
        print("RESULT: " + str(result))
        
        
        for r in result:
            xdata.append(r.TestMaterial.my_rank)
            ydata.append(r.QuestionLog.score)

        print("Xdata: " + str(xdata))
        print("Ydata: " + str(ydata))
        
        #Create new LOBF
            #minimized using BFGS
            #fit to Sigmoid fn:  1/(1 + e^(t(x-a)))
        
        p0 = [session['t'], session['a']]
        
        res = minimize(sigmoid_cost_regularized, p0, args=(xdata,ydata))
        
        db.session.query(TestLog).get(session['testlogid']).a = session['a'] = res.x[1]
        db.session.query(TestLog).get(session['testlogid']).t = session['t'] = res.x[0]
        
        print (res.x)
        x = np.linspace(0, 5000, 5000)
        y = sigmoid(x, *res.x)
          
        print(score)
        print(y[500])

        for tgt in range(1, 3000):
            # do a range with probablistic questioning
            # Failed last question, give easy question
            if score == 0 and y[tgt] < .7: 
                print("break")
                break
            
                
            # Got last question right, ask hard question
            elif score == 1 and y[tgt] < .3: break

        print ("Selected letter #" + str(tgt))
        
            
        while history.filter(TestMaterial.my_rank==tgt).first():
            tgt += 1
            if tgt == 3000: break   #biggest kanji atm TODO
            print("Already answered" + str(tgt))
            
        newquestion = db.session.query(TestMaterial).filter(TestMaterial.my_rank == tgt).first()

        
    #Get some history to show
    oldquestions = history.order_by(QuestionLog.id.desc()).limit(50)
    rightanswers = oldquestions.from_self().filter(QuestionLog.score == 1).all()
    rightanswers = [i.TestMaterial.my_rank for i in rightanswers]
    wronganswers = oldquestions.from_self().filter(QuestionLog.score == 0).all()
    wronganswers = [i.TestMaterial.my_rank for i in wronganswers]
    oldquestions = oldquestions.limit(10)
    return render_template('test.html', question = newquestion, oldquestions = oldquestions, wronganswers = json.dumps(wronganswers), rightanswers = json.dumps(rightanswers))











