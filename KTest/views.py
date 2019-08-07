# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: KTest - Kanji test site JiKen
@description: Views/Routes
"""

#Flask
from flask import request, render_template, redirect, url_for, session, abort

#SQLAlch
#from sqlalchemy import desc

#Models
from .models import TestMaterial, \
    TestLog, QuestionLog

#Session
from . import app, db

##########################################
### ROUTES
##########################################

@app.route("/")
def home():
    return render_template('home.html')

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
    newquestion = db.session.query(TestMaterial).get(history.count() +1)
    
    #Get some history to show
    oldquestions = history.order_by(QuestionLog.id.desc()).limit(10)
    
#    for q in oldquestions:
#        print("Old Q:" + str(q.testmaterial.id))
    return render_template('test.html', question = newquestion, oldquestions = oldquestions)











