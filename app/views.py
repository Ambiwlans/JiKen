# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: JiKen - Kanji testing site
@description: Views/Routes
"""

#Flask
from flask import request, render_template, redirect, url_for, session, abort, send_file
from flask import Blueprint, current_app

bp = Blueprint('main', __name__)

#DB
from app import db
from .models import TestLog, QuestionLog, TestMaterial, TempTestMaterial

#Data Handling
import pandas as pd
import math
import pickle
import genanki
import tempfile
#import html

#Tools
from app.utils import sigmoid, logit, sigmoid_cost_regularized

import random
from scipy.optimize import minimize
from scipy.integrate import quad

import datetime

##########################################
### ERROR ROUTES
##########################################

@bp.errorhandler(500)
def server_error(e):
    return render_template('error.html', err = "500", \
        msg = "Your test timed out or there was an internal server error. Contact <a href='https://github.com/Ambiwlans' target='_blank'>Ambiwlans</a> or return to the <a href='/'>home page</a>.")

@bp.errorhandler(404)
def notfound_error(e):
#    return "404 Page not found. Contact <a href='https://github.com/Ambiwlans' target='_blank'>Ambiwlans</a> or return to the <a href='/'>home page</a>.", 404
    return render_template('home.html')

##########################################
### ADMIN ROUTES
##########################################

@bp.route("/adminpanel")
def adminpanel():
    if request.args.get('p') != current_app.config['SECRET_KEY']:    
        return render_template('home.html')
    
    recent_t_ids = db.session.query(TestLog.id).order_by(TestLog.id.desc()).limit(5).all() or 0
    recent_t_ids = [r for r, in recent_t_ids]
    
    return render_template('admin.html', p = request.args.get('p'), msg = request.args.get('msg'),\
        hist = list(zip(pd.read_msgpack(current_app.config['SESSION_REDIS'].get('Hist')).index,pd.read_msgpack(current_app.config['SESSION_REDIS'].get('Hist')))), \
        pred = [int(current_app.config['SESSION_REDIS'].get('avg_known') or 0)],
        recent_t_ids = recent_t_ids)
    
@bp.route("/forcemetaupdate")
def forcemetaupdate():
    if request.args.get('p') != current_app.config['SECRET_KEY']:    
        return render_template('home.html')
    
    print("Force metaupdate attempt")
    from app.updater import update_meta as mupd
    mupd(current_app)
    
    return redirect(url_for('.adminpanel', p = request.args.get('p'), msg = "Force metaupdate Success"))

@bp.route("/forceupdate")
def forceupdate():
    if request.args.get('p') != current_app.config['SECRET_KEY']:    
        return render_template('home.html')
    
    print("Force update attempt")
    from app.updater import update_TestQuestionLogs as upd
    upd(current_app)
    
    return redirect(url_for('.adminpanel', p = request.args.get('p'), msg = "Force Update Success"))

@bp.route("/reset_redis")
def reset_redis():
    if request.args.get('p') != current_app.config['SECRET_KEY']:    
        return render_template('home.html')
    
    print("Reset Redis attempt")
    
    # flush all
    current_app.config['SESSION_REDIS'].flushall()
    
    # reload from sql
    current_app.config['SESSION_REDIS'].set('cur_testlog_id', db.session.query(TestLog).order_by('id').all()[-1].id + 1)    
    current_app.config['SESSION_REDIS'].set('TestMaterial', pd.read_sql(db.session.query(TestMaterial).statement,db.engine).to_msgpack(compress='zlib'))
    current_app.config['SESSION_REDIS'].set('TempTestMaterial', pd.read_sql(db.session.query(TempTestMaterial).statement,db.engine).to_msgpack(compress='zlib'))
    
    # update meta
    from app.updater import update_meta as mupd
    mupd(current_app)
    
    return redirect(url_for('.adminpanel', p = request.args.get('p'), msg = "Redis Reset!"))

#
# Pushes rank changes to redis (will update to sql next metaupdate)
#    
@bp.route("/shift_rank")
def shift_rank():
    if request.args.get('p') != current_app.config['SECRET_KEY']:    
        return render_template('home.html')
    
    q_kanji = (request.args.get('q_kanji') or 0)
    shiftsize = int(request.args.get('shiftsize') or 0)
    incdir = int(request.args.get('incdir') or 0)
    if (q_kanji == 0) or (shiftsize == 0) or (incdir == 0):
        return render_template('home.html')
    
    tm = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))
    ttm = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TempTestMaterial'))
    
    q_id = tm[tm['kanji'] == q_kanji].iloc[0].id
    q_L2rank = ttm[ttm['id'] == q_id].iloc[0].L2R_my_rank
    print(f"Bumping: #{q_id} {q_kanji}, q_L2rank={q_L2rank}, incdir={incdir}, shiftsize={shiftsize}")
        
    import pprint
    print("ranks (before):")
    pprint.pprint(ttm.loc[ttm['L2R_my_rank'].between(q_L2rank + ((incdir * shiftsize) - shiftsize)/2, 
        q_L2rank + ((incdir * shiftsize) + shiftsize)/2), 'L2R_my_rank'])
    
    #correct for edge cases
    if (q_L2rank + shiftsize > len(ttm)):
        shiftsize = len(ttm) - q_L2rank - 1
    if (q_L2rank - shiftsize < 1):
        shiftsize = q_L2rank - 1
    
    # reverse increment each question down the line
    ttm.loc[ttm['L2R_my_rank'].between(q_L2rank + ((incdir * shiftsize) - shiftsize)/2, 
        q_L2rank + ((incdir * shiftsize) + shiftsize)/2), 'L2R_my_rank'] -= incdir
        
    # increment the target question
    ttm.loc[ttm['id'] == int(q_id),'L2R_my_rank'] = int(q_L2rank + (incdir * shiftsize))
    
    print("ranks (after):")
    pprint.pprint(ttm.loc[ttm['L2R_my_rank'].between(q_L2rank + ((incdir * shiftsize) - shiftsize)/2, 
        q_L2rank + ((incdir * shiftsize) + shiftsize)/2), 'L2R_my_rank'])
    #Update the redis
    current_app.config['SESSION_REDIS'].set('TempTestMaterial', ttm.to_msgpack(compress='zlib'))
    db.session.commit()
                    
    return redirect(url_for('.adminpanel', p = request.args.get('p'), msg = "Rank Shifted!"))

##########################################
### GENERAL ROUTES
##########################################

@bp.route("/")
def home():
    return render_template('home.html')

@bp.route("/test")
def test():
    
    ###
    ### Log Answer/Score
    ###

    study = int(request.args.get('s') or 0)
    
    score = request.args.get('a')
    testmaterialid = request.args.get('q')
    
    if session.get('TestLog') is None or score is None:
        # Stash 'old test' if there was already an active one
        if session.get('TestLog') is not None:
            print('Stashing earlier test...' + str(session['TestLog'].id))
            oldtest = {}
            oldtest['TestLog'] = session['TestLog']
            oldtest['QuestionLog'] = session['QuestionLog']
            oldtest['last_touched'] = session['last_touched']
            current_app.config['SESSION_REDIS'].set('session:old' + str(session['TestLog'].id), pickle.dumps(oldtest))
            
        # New Test, new log
        session['TestLog'] = pd.Series({
                "id" : int(current_app.config['SESSION_REDIS'].get('cur_testlog_id').decode('utf-8')),
                "a" : int(current_app.config['SESSION_REDIS'].get('default_kanji')),
                "t" : float(current_app.config['SESSION_REDIS'].get('default_tightness')),
                "ip" : request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                "start_time" : datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})
        
        session['QuestionLog'] = pd.DataFrame(columns=['testmaterialid','score'], dtype='int64')
        session['last_touched'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        if study:
            session['Study'] = 1
            session['Study_List'] = pd.DataFrame(columns=['testmaterialid', 'times_right','times_wrong'], dtype='int64')
            session['learned_cnt'] = 0
            session['dropped_cnt'] = 0
        else:
            session['Study'] = 0

        current_app.config['SESSION_REDIS'].incr('cur_testlog_id')
    elif int(score) == -1:
        # Flag to just continue a test
        score = int(score)
        study = session['Study']
        #print("Continuing test")
        pass
    else:
        # Got an answer, log it (to redis session)
        score = bool(int(score))
#        print(f"logging: {testmaterialid}")
#        print(session['QuestionLog'])
#        print(session['Study_List'])
        if testmaterialid is None: 
            print("Error. Got answer with no question.")
            abort(500)
        else:
            testmaterialid = int(testmaterialid)
        
        # In study mode, log new questions and track the study list
        if study:
            if (session['QuestionLog']['testmaterialid'].astype('int') == testmaterialid).any():
                if (session['Study_List']['testmaterialid'].astype('int') == testmaterialid).any():
                    if score:
                        session['Study_List'].loc[session['Study_List']['testmaterialid'].astype('int') == testmaterialid, 'times_right'] += 1
                        if session['Study_List'][session['Study_List']['testmaterialid'].astype('int') == testmaterialid].iloc[0].times_right >= int(current_app.config['MAX_TIMES_RIGHT']):
                           session['learned_cnt'] += 1
                           session['Study_List'].drop(session['Study_List'][session['Study_List']['testmaterialid'].astype('int') == testmaterialid].index, inplace=True)
                    else:
                        session['Study_List'].loc[session['Study_List']['testmaterialid'].astype('int') == testmaterialid, 'times_wrong'] += 1
                        if session['Study_List'][session['Study_List']['testmaterialid'].astype('int') == testmaterialid].iloc[0].times_wrong >= int(current_app.config['MAX_TIMES_WRONG']):
                           session['dropped_cnt'] += 1
                           session['Study_List'].drop(session['Study_List'][session['Study_List']['testmaterialid'].astype('int') == testmaterialid].index, inplace=True)
            else:
                session['QuestionLog'] = session['QuestionLog'].append({'testmaterialid' : testmaterialid, 'score' : score}, ignore_index=True)
                if not score and len(session['QuestionLog']) > current_app.config['GRAPH_AFTER']:
                    tested_x = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))[pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))['id']==testmaterialid].iloc[0]['my_rank']
                    if (sigmoid(tested_x, session['TestLog'].t, session['TestLog'].a, 1) > current_app.config['PCT_CUTOFF']):
                        session['Study_List'] = session['Study_List'].append({'testmaterialid' : testmaterialid, 'times_right' : 0, 'times_wrong' : 0}, ignore_index=True)            
        # In test mode, log questions, for dupes, overwrite last answer
        else:
            if (session['QuestionLog']['testmaterialid'].astype('int') == testmaterialid).any():
                session['QuestionLog'][session['QuestionLog']['testmaterialid'].astype('int') == testmaterialid].score = score
            else:
                session['QuestionLog'] = session['QuestionLog'].append({'testmaterialid' : testmaterialid, 'score' : score}, ignore_index=True)

        
    ###
    ### Handle Data, Prep output
    ###
    
    history = pd.merge(session['QuestionLog'], \
                       pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')), \
                       left_on=session['QuestionLog'].testmaterialid.astype(int), \
                       right_on='id')
    
    len_history = len(history)
    
    #Get some history to show (do this before sort)
    oldquestions = history[:100]
    
    rightanswers = oldquestions[oldquestions['score']==1]
    rightanswers = [(r.my_rank, r.kanji) for i, r in rightanswers.iterrows()]
    wronganswers = oldquestions[oldquestions['score']==0]
    wronganswers = [(r.my_rank, r.kanji) for i, r in wronganswers.iterrows()]
        
    #Get updated statistics and next question
    
    xdata = []
    ydata = []
    pred = [0,0,0]
    studyword = 0
    
    active_cnt = 0
    question_variability = current_app.config['TEST_VARIABLITY']
    if study: 
        active_cnt = len(session['Study_List'])
        if len_history > current_app.config['VARIABILITY_SHIFT']:
            question_variability = current_app.config['STUDY_VARIABLITY']

    if score is None:
        #For the first question, ask a random kanji (for data gathering purposes)
        newquestion = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')).sample().iloc[0]
    else:
               
        #Resort by my_rank for faster iter
        history = history.sort_values(by=['my_rank'], ascending=True)

        for i, r in history.iterrows():
            xdata.append(r.my_rank)
            ydata.append(r.score)
        
        # Get new LOBF (a, t values)
            #minimized using Nelder-Mead, custom cost fn
            #fit to Sigmoid fn:  1/(1 + e^(t(x-a)))
            #update our db and the session data
        
        p0 = [session['TestLog'].t, session['TestLog'].a]       # use last LOBF as starting point for new one
        
        res = minimize(sigmoid_cost_regularized, p0, args=(xdata, ydata, p0[0], p0[1], float(current_app.config['SESSION_REDIS'].get('default_t') or 0.005)),method="Nelder-Mead")
            #,options={'eps': [0.0001,1]})#, bounds=[(0,10),(1,7000)])
        
        session['TestLog'].a = float(res.x[1])
        session['TestLog'].t = float(res.x[0])
        
        # Predict known kanji
        if len_history > current_app.config['GRAPH_AFTER']:
            #[mid, upper, lower]
            pred = [(quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x,1))[0]),
                        (quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x, (1 / (1 + 2**(-len_history/150)))))[0]),
                        (quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x, 1 + (2 / (1 + 2**(len_history/150)))))[0])]
            # account for all the answered values
            for i, r in history.iterrows():
                pred[0] += (r.score - sigmoid(r.my_rank, *res.x, 1))
                pred[1] += (r.score - sigmoid(r.my_rank, *res.x, .5))
                pred[2] += (r.score - sigmoid(r.my_rank, *res.x, 2))
            
            pred = list(map(int,pred))
            
        # Select next question
        
        if active_cnt > random.randrange(0, int(current_app.config['TGT_ACTIVE'])):
            x_id = int(session['Study_List'].iloc[random.randrange(0, active_cnt)]['testmaterialid'])
            while (x_id == testmaterialid) and (active_cnt > 1): # avoid repeats
                x_id = int(session['Study_List'].iloc[random.randrange(0, active_cnt)]['testmaterialid'])
            newquestion = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))[pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))['id']==x_id].iloc[0]
            studyword = 1
        else:     
            # Try a few rerolls if you land on a repeat
            rerolls = 0
            while True:
                rerolls += 1
                # left half of graph if last question wrong, right half if correct (skew selection slightly away from the middle)
                if score == 1:
                    x = int(logit((random.random()**question_variability)/2, *res.x))
                elif score == 0:
                    x = int(logit((random.random()**question_variability)/(-2) + 1, *res.x))
                elif score == -1:
                    x = int(logit(random.random(), *res.x))
                else:
                    # Score not given, fail gracefully
                    abort(500)
                
                oob = False
                if x < 1 : 
                    x = 1
                    oob = True
                if x > current_app.config['MAX_X']: 
                    x = current_app.config['MAX_X']
                    oob = True
                
                # if the question is new (hasn't been answered) and in-bounds, or we've tried random 3x, then move on
                if ((history['my_rank']==x).sum() == 0 and not oob) or rerolls > current_app.config['OOB_REROLLS']:               
                    break
            
            # Scan through if you are still on a repeat
            searchkey = 1
            while ((history['my_rank']==x).sum())\
                    or x < 1 or x > current_app.config['MAX_X']:
                
                x += searchkey
                
                if searchkey > 0:
                    searchkey = -searchkey - 1
                else:
                    searchkey = -searchkey + 1
                
                if x > current_app.config['MAX_X'] and x + searchkey < 1: 
                    print("Test # " + str(session['TestLog'].id) + " asked every question!")
                    # Go to history page when a user has completed every question... wowza
                    return "Holy crap!! You actually answered every kanji.... I don't really expect anyone to maneage this so I don't have anything ready.... uhh, check your <a href='/t/"+session['TestLog'].id+"'>results</a> and tweet them to me! Damn... good job!"
        
            newquestion = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))[pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))['my_rank']==x].iloc[0]                

    
    #Find a sensible max x value
    xmax = min(int(math.ceil((max(oldquestions['my_rank'], default=0) + 250) / 400) * 500), int(current_app.config['GRAPH_MAX_X']))
    
    #Refresh the timeout flag
    session['last_touched'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    if studyword:
        print(f"Review! Active= {active_cnt}, Learned = {session['learned_cnt']}, Dropped = {session['dropped_cnt']}")
    print(f"Test #{session['TestLog'].id}, A = {session['TestLog'].a}, T = {session['TestLog'].t} ||  #{len(session['QuestionLog'])}, Rank#: {newquestion['my_rank']}, 字: {newquestion['kanji']}")
    
    if study:
        return render_template('test.html', s = study, question = newquestion, cnt = len_history, id = session['TestLog'].id, \
            a = session['TestLog'].a, t = session['TestLog'].t, wronganswers = wronganswers, rightanswers = rightanswers, xmax = xmax, pred = pred, \
            studyword = studyword, active_cnt = active_cnt, learned_cnt = session['learned_cnt'], dropped_cnt = session['dropped_cnt'])
    else:
        return render_template('test.html', s = study, question = newquestion, cnt = len_history, id = session['TestLog'].id, \
            a = session['TestLog'].a, t = session['TestLog'].t, wronganswers = wronganswers, rightanswers = rightanswers, xmax = xmax, pred = pred)
    

@bp.route("/t/<id>")
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
        if datafound:
            break
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
            abort(404, "Test not found.")
        data['QuestionLog'] = db.session.query(QuestionLog).filter(QuestionLog.testlogid == id).all()
        data['QuestionLog'] = pd.DataFrame([s.__dict__ for s in data['QuestionLog']])
        #print("Test found in DB")

    ###        
    ### Prep output
    ###
    
    try:
        history = pd.merge(data['QuestionLog'], \
                   pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')), \
                   left_on=data['QuestionLog'].testmaterialid.astype(int), \
                   right_on='id')
    except:
        history = pd.DataFrame(columns=['score','my_rank'])
    
    
    #Get some history to show (do this before sort)
    oldquestions = history[:500].sort_values(by=['my_rank'], ascending=True)
    
    rightanswers = oldquestions[oldquestions['score']==1]
    rightanswers = [(r.my_rank, r.kanji) for i, r in rightanswers.iterrows()]
    wronganswers = oldquestions[oldquestions['score']==0]
    wronganswers = [(r.my_rank, r.kanji, r.meaning, r.onyomi, r.kunyomi, r.grade, r.jlpt, r.kanken, r.examples) for i, r in wronganswers.iterrows()]
    
    try:
        cnt = data['TestLog'].number_of_questions
    except:
        cnt = len(history)
        
    #Resort by my_rank for faster iter
    history = history.sort_values(by=['my_rank'], ascending=True)
    
    #Redo Predictions
    pred = [0,0,0]      #[mid, upper, lower]    
    x = [data['TestLog'].t, data['TestLog'].a]
    
    len_history = len(history)
    pred = [(quad(sigmoid,0,current_app.config['MAX_X'],args=(*x,1))[0]),
            (quad(sigmoid,0,current_app.config['MAX_X'],args=(*x, (1 / (1 + 2**(-len_history/150)))))[0]),
            (quad(sigmoid,0,current_app.config['MAX_X'],args=(*x, 1 + (2 / (1 + 2**(len_history/150)))))[0])]
    
    # account for all the answered values
    for i, r in history.iterrows():
        pred[0] += (r.score - sigmoid(r.my_rank, *x, 1))
        pred[1] += (r.score - sigmoid(r.my_rank, *x, .5))
        pred[2] += (r.score - sigmoid(r.my_rank, *x, 2))
    
    pred = list(map(int,pred))
    

    
    #Find a sensible max x value
    xmax = min(int(math.ceil(min(((pred[0] + 4*(pred[1]-pred[0])) + 250), current_app.config['GRAPH_MAX_X'])/500)*500), int(current_app.config['GRAPH_MAX_X']))
    
    #Calc some stats data
    jlpt_recc = {
        0    <= pred[2] < 100  : 0,
        100  <= pred[2] < 300  : 5,
        300  <= pred[2] < 650  : 4,
        650  <= pred[2] < 1000 : 3,
        1000 <= pred[2] < 2000 : 2,
        2000 <= pred[2]        : 1}[True]
    kk_recc = {
        0    <= pred[2] < 80   : 0,
        80   <= pred[2] < 240  : 10,
        240  <= pred[2] < 440  : 9,
        440  <= pred[2] < 640  : 8,
        640  <= pred[2] < 825  : 7,
        825  <= pred[2] < 1006 : 6,
        1006 <= pred[2] < 1300 : 5,
        1300 <= pred[2] < 1600 : 4,
        1600 <= pred[2] < 1950 : 3,
        1950 <= pred[2] < 2136 : -2,
        2136 <= pred[2] < 2965 : 2,
        2965 <= pred[2] < 6355 : 1,
        6355 <= pred[2]        : -1}[True]
    pct_known_by_appearance = min(max(100 * ((-180/(pred[0] + 160)) + 1.08), 0),100)   #Magic formula based on data

    
    return  render_template('history.html', id = id, \
        a = data['TestLog'].a, t = data['TestLog'].t, wronganswers = wronganswers, rightanswers = rightanswers, xmax = xmax, pred = pred,\
        curtest = curtest, cnt = cnt, \
        hist = list(zip(pd.read_msgpack(current_app.config['SESSION_REDIS'].get('Hist')).index,pd.read_msgpack(current_app.config['SESSION_REDIS'].get('Hist')))), \
        date = data['TestLog'].start_time, \
        jlpt_recc = jlpt_recc, kk_recc = kk_recc, \
        avg_answered = int(current_app.config['SESSION_REDIS'].get('avg_answered') or 0), \
        avg_known = int(current_app.config['SESSION_REDIS'].get('avg_known') or 0), \
        pct_known_by_appearance = "{:.2f}".format(pct_known_by_appearance))


@bp.route("/anki_file/<id>/<max_filter>")
def anki_file(id, max_filter):
    ###
    ### Locate/Load test data
    ###
    
    
    data = {}
    datafound = False

    #If test is in cache still, use that data.
    for sess in current_app.config['SESSION_REDIS'].scan_iter("session:*"):
        if datafound:
            break
        data = pickle.loads(current_app.config['SESSION_REDIS'].get(sess))
        try:
            if data['TestLog']['id'] == int(id):
                #print("Test found in cache")            
                datafound = True
                break
        except:
            pass
        
    #Otherwise, load data from Sql
    if not datafound:
        #print("Test not in cache")
        data['TestLog'] = db.session.query(TestLog).filter(TestLog.id == id).first()
        if not data['TestLog']:
            #if it isn't in the DB either, 404 out, test not found.
            abort(404, "Test not found.")
        data['QuestionLog'] = db.session.query(QuestionLog).filter(QuestionLog.testlogid == id).all()
        data['QuestionLog'] = pd.DataFrame([s.__dict__ for s in data['QuestionLog']])
        #print("Test found in DB")

    ###        
    ### Prep output
    ###
    
    try:
        history = pd.merge(data['QuestionLog'], \
                   pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')), \
                   left_on=data['QuestionLog'].testmaterialid.astype(int), \
                   right_on='id')
    except:
        abort(500, "Anki test failed to generate.")

    #Only wrong answers needed for study list    
    wronganswers = history[history['score']==0].sort_values(by=['my_rank'], ascending=True)
    wronganswers = wronganswers[wronganswers['my_rank'] <= int(max_filter)]
    
    ###
    ### Anki Deck Building
    ###

    my_deck = genanki.Deck(2059400111, 'JiKen Study - #'+str(id))

    my_model = genanki.Model(
      1607392219,
      'JiKen',
      fields=[
            {'name': 'my_rank'},
            {'name': 'Kanji'},
            {'name': 'meaning'},
            {'name': 'onyomi'},
            {'name': 'kunyomi'},
            {'name': 'grade'},
            {'name': 'jlpt'},
            {'name': 'kanken'},
            {'name': 'examples'}
      ],
      templates=[{
      'name': 'Card 1',
      'qfmt': '<h1 style="font-size: 100px; text-align:center;">{{Kanji}}</h1>',
      'afmt': '{{FrontSide}}<hr>\
              <div style="font-size: 20px; text-align:center;"><b>{{meaning}}</b><br><br>\
              {{onyomi}} --- {{kunyomi}}</div><br>\
              {{examples}}<hr>\
              Jiken Rank #{{my_rank}}\
              Grade: {{grade}}<br>\
              JLPT: {{jlpt}}<br>\
              Kanken: {{kanken}}'}])
    
    
    for i, r in wronganswers.iterrows():
        my_deck.add_note(genanki.Note(model=my_model, fields=[str(f or '') for f in [r.my_rank, r.kanji, r.meaning, r.onyomi, r.kunyomi, r.grade, r.jlpt, r.kanken, r.examples]]))
    
    
    tf = tempfile.NamedTemporaryFile(delete=False).name
    genanki.Package(my_deck).write_to_file(tf)
    
    return send_file(tf, mimetype='application/apkg', as_attachment=True, attachment_filename='JiKen Study - #'+str(id)+'.apkg')
    
#
# Bookcheck allows users to enter text and get back an analysis of text difficulty
#    
# Mostly done clientside (js), so not much is needed in python
# can be accessed with or without a valid test
#
@bp.route("/bookcheck")
def bookcheck():
    id = int(request.args.get('id') or 0)
    test_data = {}
    
    #If given a test number to look up
    if id:
        #If test is in cache still, scan through redis and use that data.
        for sess in current_app.config['SESSION_REDIS'].scan_iter("session:*"):
            if test_data:
                break
            tmp_data = pickle.loads(current_app.config['SESSION_REDIS'].get(sess))
            try:
                if tmp_data['TestLog']['id'] == int(id):          
                    test_data = tmp_data
                    break
            except:
                pass
        #Otherwise, load data from Sql
        if not test_data:
            test_data['TestLog'] = db.session.query(TestLog).filter(TestLog.id == id).first()
            if not test_data['TestLog']:
                #if it isn't in the DB either, test not found.
                id = 0
            test_data['QuestionLog'] = db.session.query(QuestionLog).filter(QuestionLog.testlogid == id).all()
            test_data['QuestionLog'] = pd.DataFrame([s.__dict__ for s in test_data['QuestionLog']])
    
    # default vals for a, t (cutoff needs to be done clientside to enable on the fly modification)
    if id:
        a = test_data['TestLog'].a 
        t = test_data['TestLog'].t 
    else:
        a = int(current_app.config['SESSION_REDIS'].get('default_kanji') or 1500)
        t = float(current_app.config['SESSION_REDIS'].get('default_tightness') or .01)
        
    # Get necessary kanji list / dictionary data    
    tm = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')).sort_values(by=['my_rank'], ascending=True)
    tm_list = [(r.my_rank, r.kanji, r.meaning, r.onyomi, r.kunyomi, r.grade, r.jlpt, r.kanken, r.examples) for i, r in tm.iterrows()]
    
    return render_template('bookcheck.html', tm = tm_list, 
        id = id, a = a, t = t,
        hist_bins = current_app.config['HIST_BINS'])
    
# allows initial wordlists to only have rank and kanji rather than sending full test_mat    
# https://stackoverflow.com/questions/68266400/sending-plotly-charts-in-a-dictionary-via-jquery-getjson-in-a-flask-app
# https://stackoverflow.com/questions/13081532/return-json-response-from-flask-view   
# https://stackoverflow.com/questions/20001229/how-to-get-posted-json-in-flask   
# https://towardsdatascience.com/using-python-flask-and-ajax-to-pass-information-between-the-client-and-server-90670c64d688   
#@bp.route('/more_tm', methods=['POST', 'GET'])
#def more_tm():
#    my_ranks = request.args.get('my_ranks')
#    
#    print(my_ranks)
#    
#    tm = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')).sort_values(by=['my_rank'], ascending=True)
#    tm_list = [(r.my_rank, r.kanji, r.meaning, r.onyomi, r.kunyomi, r.grade, r.jlpt, r.kanken, r.examples) for i, r in tm.iterrows()]
#
#    return tm_list
#    
    
    
    
    
    

