# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: JiKen - Kanji testing site
@description: The main init, run via jiken.py
"""

#Base
from flask import Flask
from config import Config

#Data Handling
from flask_sqlalchemy import SQLAlchemy
from flask_session.__init__ import Session

import atexit
from apscheduler.schedulers.background import BackgroundScheduler

#import pickle
from sqlalchemy.ext.serializer import loads, dumps

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
    #db.create_all()
	
    from app.views import bp as main_bp
    app.register_blueprint(main_bp)    
	 
    # Setup Bootstrap 4.1.0 with jquery 3.3.1
    Bootstrap(app)

    # Scheduler set up/run
    from app.updater import update_meta, initial_DB_reformat
    with app.app_context():
        update_meta()
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=update_meta, trigger="interval", days=1)
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())
        
        app.config['SESSION_REDIS'].flushall()

        app.config['SESSION_REDIS'].set('TestMaterial', dumps(db.session.query(models.TestMaterial)))
        #initial_DB_reformat()
    return app

# Late import so modules can import their dependencies properly (proto-blueprint)
from app import models

        


        






