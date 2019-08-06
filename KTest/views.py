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
    newit = TestMaterial(
            question = "弾",
            answer = "bullet")
    db.session.add(newit)
    db.session.commit()
    return render_template('home.html')

@app.route("/test")
def test():
    
    ans = request.args.get('a')
    question = request.args.get('q')
    
    print(type(ans))
    if ans is None:
        session['anslist'] = []
        print("R2")
    else:
        anslist = session['anslist']
        anslist.append(ans)
        ##TODO - do stuff with this list
        session['anslist'] = anslist
        print(session['anslist'])
        
    #print(session['anslist'])
    return render_template('test.html')