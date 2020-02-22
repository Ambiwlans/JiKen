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

#DB
from app import db
from .models import TestLog, QuestionLog

#Data Handling
import json
import pandas as pd
import math
import pickle

#Tools
from app.utils import sigmoid, logit, sigmoid_cost_regularized

import random
from scipy.optimize import minimize
from scipy.integrate import quad

import datetime

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
    
    if session.get('TestLog') is None or score is None:
        # New Test, new log
        session['TestLog'] = pd.Series({
                "id" : int(current_app.config['SESSION_REDIS'].get('cur_testlog_id').decode('utf-8')),
                "a" : int(current_app.config['SESSION_REDIS'].get('default_kanji')),
                "t" : float(current_app.config['SESSION_REDIS'].get('default_tightness')),
                "ip" : request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                "start_time" : datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})
        
        session['QuestionLog'] = pd.DataFrame(columns=['testmaterialid','score'], dtype='int64')

        current_app.config['SESSION_REDIS'].incr('cur_testlog_id')
    elif int(score) == -1:
        # Flag to just continue a test
        score = int(score)
        #print("Continuing test")
        pass
    else:
        # Got an answer, log it (to redis session)
        score = bool(int(score))
        session['QuestionLog'] = session['QuestionLog'].append({'testmaterialid' : testmaterialid, 'score' : score}, ignore_index=True)
        
    ###
    ### Handle Data, Prep output
    ###
    
    history = pd.merge(session['QuestionLog'], \
                       pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')), \
                       left_on=session['QuestionLog'].testmaterialid.astype(int), \
                       right_on='id')
    
    #Get updated statistics and next question
    
    xdata = []
    ydata = []
    pred = [0,0,0]
    
    if score is None:
        #For the first question, ask a random kanji (for data gathering purposes)
        newquestion = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')).sample().iloc[0]
    else:
        history = history.sort_values(by=['my_rank'], ascending=False)
        
        for i, r in history.iterrows():
            xdata.append(r.my_rank)
            ydata.append(r.score)
        
        # Get new LOBF (a, t values)
            #minimized using Nelder-Mead, custom cost fn
            #fit to Sigmoid fn:  1/(1 + e^(t(x-a)))
            #update our db and the session data
        
        p0 = [session['TestLog'].t, session['TestLog'].a]       # use last LOBF as starting point for new one
        
        res = minimize(sigmoid_cost_regularized, p0, args=(xdata, ydata, p0[0], p0[1]),method="Nelder-Mead")
            #,options={'eps': [0.0001,1]})#, bounds=[(0,10),(1,7000)])
        
        session['TestLog'].a = float(res.x[1])
        session['TestLog'].t = float(res.x[0])
        
        # Predict known kanji
        if len(history) > current_app.config['GRAPH_AFTER']:
            #[mid, upper, lower]
            pred = [(quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x,1))[0]),
                        (quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x,.5))[0]),
                        (quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x,2))[0])]
            # account for all the answered values
            for i, r in history.iterrows():
                pred[0] += (r.score - sigmoid(r.my_rank, *res.x, 1))
                pred[1] += (r.score - sigmoid(r.my_rank, *res.x, .5))
                pred[2] += (r.score - sigmoid(r.my_rank, *res.x, 2))
            
            pred = list(map(int,pred))
            
        # Select next question
        
        # left half of graph if last question wrong, right half if correct (skew selection slightly away from the middle)
        if score == 1:
            x = int(logit((random.random()**.5)/2, *res.x))
        elif score == 0:
            x = int(logit((random.random()**.5)/(-2) + 1, *res.x))
        elif score == -1:
            x = int(logit((random.random()**.5), *res.x))
        else:
            # Score not given, fail gracefully
            #TODO - error screens
            return render_template('home.html')
        
        if x < 1 : x = 1
        if x > current_app.config['MAX_X']: x = current_app.config['MAX_X']

        # don't ask repeats
        searchkey = 1
        while (history['my_rank']==x).sum() or x < 1 or x > current_app.config['MAX_X']:
            #print("Already answered" + str(x))
            x += searchkey
            
            if searchkey > 0:
                searchkey = -searchkey - 1
            else:
                searchkey = -searchkey + 1
            
            if x > current_app.config['MAX_X'] and x + searchkey < 1: 
                print("Test # " + str(session['TestLog'].id) + " asked every question!")
                x = 1
                #TODO - go to seperate page
                break
                
        newquestion = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))[pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))['my_rank']==x].iloc[0]
    
    #Get some history to show
    oldquestions = history.sort_values(by=['id'], ascending=False)[:100]
    
    rightanswers = oldquestions[oldquestions['score']==1]
    rightanswers = [(r.my_rank, r.kanji) for i, r in rightanswers.iterrows()]
    wronganswers = oldquestions[oldquestions['score']==0]
    wronganswers = [(r.my_rank, r.kanji) for i, r in wronganswers.iterrows()]
    
    #Find a sensible max x value
    xmax = min(int(math.ceil((max(oldquestions['my_rank'], default=0) + 250) / 400) * 500), int(current_app.config['MAX_X']))
    
    #Refresh the timeout flag
    session['last_touched'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    print ("Asking Kanji #: " + str(newquestion['my_rank']) + " -- " + str(newquestion['kanji']))
    print("Sess: A = " + str(session['TestLog'].a) + "  T = " + str(session['TestLog'].t) + "  # = " + str(len(session['QuestionLog'])))

    return render_template('test.html', question = newquestion, a = session['TestLog'].a, t = session['TestLog'].t, wronganswers = json.dumps(wronganswers), rightanswers = json.dumps(rightanswers), xmax = xmax, pred = pred, cnt = len(history))

@bp.route("/history/<id>")
def history(id):
    ###
    ### Locate/Load test data
    ###
    
    data = {}
    datafound = False
    curtest = False
    
    #If test is in cache still, use that data.
    for sess in current_app.config['SESSION_REDIS'].scan_iter("session:*"):
        data = pickle.loads(current_app.config['SESSION_REDIS'].get(sess))
        try:
            if data['TestLog']['id'] == int(id):
                #print("Test found in cache")            
                datafound = True
                if session['TestLog']['id'] == int(id):
                    #print("Test is current test")
                    curtest = True
                break
        except:
            pass
        
    #Otherwise, load data from Sql
    if not datafound:
        #print("Test not in cache")
        data['TestLog'] = db.session.query(TestLog).filter(TestLog.id == id).first()
        if not data['TestLog']:
            #if it isn't in the DB either, 404 out, test not found.
            #print("Test not in DB")
            return("Test not found")
        data['QuestionLog'] = db.session.query(QuestionLog).filter(QuestionLog.testlogid == id).all()
        data['QuestionLog'] = pd.DataFrame([s.__dict__ for s in data['QuestionLog']])
        #print("Test found in DB")

    ###        
    ### Prep output
    ###
    
    history = pd.merge(data['QuestionLog'], \
               pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')), \
               left_on=data['QuestionLog'].testmaterialid.astype(int), \
               right_on='id')
            
    #Redo Predictions
    pred = [0,0,0]      #[mid, upper, lower]    
    x = [data['TestLog'].t, data['TestLog'].a]
    
    pred = [(quad(sigmoid,0,current_app.config['MAX_X'],args=(*x,1))[0]),
                (quad(sigmoid,0,current_app.config['MAX_X'],args=(*x,.5))[0]),
                (quad(sigmoid,0,current_app.config['MAX_X'],args=(*x,2))[0])]
    # account for all the answered values
    for i, r in history.iterrows():
        pred[0] += (r.score - sigmoid(r.my_rank, *x, 1))
        pred[1] += (r.score - sigmoid(r.my_rank, *x, .5))
        pred[2] += (r.score - sigmoid(r.my_rank, *x, 2))
    
    pred = list(map(int,pred))
       
        
    #Prep historical graph display data
    oldquestions = history.sort_values(by=['id'], ascending=False)[:100]
    
    rightanswers = oldquestions[oldquestions['score']==1]
    rightanswers = [(r.my_rank, r.kanji) for i, r in rightanswers.iterrows()]
    wronganswers = oldquestions[oldquestions['score']==0]
    wronganswers = [(r.my_rank, r.kanji) for i, r in wronganswers.iterrows()]
    
            
    #Find a sensible max x value
    xmax = min(int(math.ceil((max(oldquestions['my_rank'], default=0) + 250) / 400) * 500), int(current_app.config['MAX_X']))
    
    return  render_template('history.html', \
        a = data['TestLog'].a, t = data['TestLog'].t, wronganswers = json.dumps(wronganswers), rightanswers = json.dumps(rightanswers), xmax = xmax, pred = pred,\
        curtest = curtest, cnt = len(history), \
        avg_answered = int(current_app.config['SESSION_REDIS'].get('avg_answered')), avg_known = int(current_app.config['SESSION_REDIS'].get('avg_known')))










