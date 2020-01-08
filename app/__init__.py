# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: JiKen - Kanji testing site
@description: The main init, run via jiken.py
"""

#Base
from flask import Flask
from config import Config

from flask import current_app

#Data Handling
from flask_sqlalchemy import SQLAlchemy
from flask_session.__init__ import Session
import pandas as pd

#Scheduling
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

#UI
from flask_bootstrap import Bootstrap



db = SQLAlchemy()
sess = Session()

# Setup Flask App
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    sess.init_app(app)
	
    from app.views import bp as main_bp
    app.register_blueprint(main_bp)    
    
    # Setup Bootstrap 4.1.0 with jquery 3.3.1
    Bootstrap(app)

    # Scheduler set up/run
    from app.updater import update_meta, update_TestQuestionLogs, initial_DB_reformat
    with app.app_context():
#        db.create_all() 
#        initial_DB_reformat()
        app.config['SESSION_REDIS'].flushall()
        
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=update_meta, args=(current_app._get_current_object(),), trigger="interval", days=1, next_run_time=datetime.datetime.now())
        scheduler.add_job(func=update_TestQuestionLogs, args=(current_app._get_current_object(),), trigger="interval", hours=1, next_run_time=datetime.datetime.now())
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())
        
        if app.config['SESSION_REDIS'].get('TestMaterial') is None:
            app.config['SESSION_REDIS'].set('TestMaterial', pd.read_sql(db.session.query(models.TestMaterial).statement,db.engine).to_msgpack(compress='zlib'))
            print("Refreshed TestMaterial")
    return app

# Late import so modules can import their dependencies properly (proto-blueprint)
from app import models

        


        






