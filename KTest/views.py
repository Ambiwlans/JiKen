# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: KTest - Kanji test site JiKen
@description: Views/Routes
"""

#Flask
from flask import request, render_template, redirect, url_for, session, abort

#Models
from .models import TestMaterial

#Session
from . import app, db


@app.route("/")
def home():
#    newit = TestMaterial(
#            question = "弾",
#            answer = "bullet")
#    db.session.add(newit)
#    db.session.commit()
    return render_template('home.html')

#TODO - replace anslist/session storage with DB usage
@app.route("/test")
def test():
    
    #Get previous answer/score
    score = request.args.get('a')
    testmaterialid = request.args.get('q')
    
    if score is None:
        # New Session
        session['anslist'] = []
        print("R2")
    else:
        # Add score to existing session
        anslist = session['anslist']
        anslist.append(score)
        ##TODO - do stuff with this list
        session['anslist'] = anslist
        print(session['anslist'])
        
    #Get updated statistics and next question
    newquestion = db.session.query(TestMaterial).get(len(session['anslist'])+1)
    
    session['anslist']
    ##print(session['anslist'])
    return render_template('test.html', question = newquestion)











