# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: JiKen - Kanji testing site
@description: Views/Routes
"""

#Flask
from flask import request, render_template, redirect, url_for, session, abort
from flask import Blueprint, current_app

bp = Blueprint('main', __name__)

#SQLAlch
from sqlalchemy import func #desc
import json

#Math
import random
from scipy.optimize import minimize
from scipy.integrate import quad

import datetime

#Models
from .models import TestMaterial, \
    TestLog, QuestionLog, \
    MetaStatistics

#Session
from app import db
from app.utils import sigmoid, logit, sigmoid_cost_regularized

##########################################
### ROUTES
##########################################

@bp.route("/")
def home():
    return render_template('home.html')

#TODO2 - bias first question towards more commonly known ones
#TODO5 - avoid recalculating everything each question - modify rather than redo
@bp.route("/test")
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
                t = db.session.query(MetaStatistics).first().default_tightness,
                ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                start_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
        
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
            #minimized using Nelder-Mead, custom cost fn
            #fit to Sigmoid fn:  1/(1 + e^(t(x-a)))
            #update our db and the session data
        
        p0 = [session['t'], session['a']]       # use last LOBF as starting point for new one
        
        res = minimize(sigmoid_cost_regularized, p0, args=(xdata, ydata, p0[0], p0[1]),method="Nelder-Mead")
            #,options={'eps': [0.0001,1]})#, bounds=[(0,10),(1,7000)])
        
        db.session.query(TestLog).get(session['testlogid']).a = session['a'] = float(res.x[1])
        db.session.query(TestLog).get(session['testlogid']).t = session['t'] = float(res.x[0])
        
        # Predict known kanji
        if len(result) > 10:
            #[mid, upper, lower]
            pred = [(quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x,1))[0]),
                        (quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x,.5))[0]),
                        (quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x,2))[0])]
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
        else:
            # Score not given, fail gracefully
            #TODO - error screens
            return render_template('home.html')
        
        if x < 1 : x = 1
        if x > current_app.config['MAX_X']: x = current_app.config['MAX_X']

        # don't ask repeats
        searchkey = 1
        while history.filter(TestMaterial.my_rank==x).first() or x < 1 or x > current_app.config['MAX_X']:
            print("Already answered" + str(x))
            x += searchkey
            
            if searchkey > 0:
                searchkey = -searchkey - 1
            else:
                searchkey = -searchkey + 1
            
            if x > current_app.config['MAX_X'] and x + searchkey < 1: 
                print("Test # " + str(session['testlogid']) + " asked every question!")
                x = 1
                #TODO - go to seperate page
                break
                
        newquestion = db.session.query(TestMaterial).filter(TestMaterial.my_rank == x).first()
    
    #Get some history to show
    oldquestions = history.order_by(QuestionLog.id.desc()).limit(100)
    
    rightanswers = oldquestions.from_self().filter(QuestionLog.score == 1).all()
    rightanswers = [i.TestMaterial.my_rank for i in rightanswers]
    wronganswers = oldquestions.from_self().filter(QuestionLog.score == 0).all()
    wronganswers = [i.TestMaterial.my_rank for i in wronganswers]
    oldquestions = oldquestions.limit(10)
    
    print ("Asking test #" + str(session['testlogid']) + ", Question #: " + str(newquestion.id) + ", Rank: " + str(newquestion.my_rank) + " -- " + str(newquestion.kanji.encode("utf-8")))
    return render_template('test.html', question = newquestion, oldquestions = oldquestions, wronganswers = json.dumps(wronganswers), rightanswers = json.dumps(rightanswers), pred = pred)











