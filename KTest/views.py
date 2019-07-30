# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: KTest - Kanji test site JiKen
@description: Views/Routes
"""

#Flask
from flask import request, render_template, redirect, url_for, session, abort

#Models
#from .Models.models import Question, QuestionLog, TestLog

#Session
from . import app, db



##########################################
### VIEWS
##########################################
@app.route("/")
def home():
    return render_template('home.html')
