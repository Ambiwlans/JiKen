# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: KTest - Kanji test site JiKen
@description: The init, run via 'flask run' as an installed package
"""

#General Python
#import atexit
#from apscheduler.schedulers.background import BackgroundScheduler

from flask import Flask

from flask_sqlalchemy import SQLAlchemy

from flask_bootstrap import Bootstrap



# Setup Flask App
app = Flask(__name__)
app.config.from_object('KTest.config.Config')
    
db = SQLAlchemy(app)
 

# Setup Bootstrap 4.1.0 with jquery 3.3.1
Bootstrap(app)

# Setup cron/scheduler
#def update_top_1000():
#    users = User.query.all()
#
#    for user in users:
#        uviews = 0
#        tabs = user.tabs
#        for tab in tabs:
#            uviews = uviews + tab.views
#        user.views = uviews
#    db_session.commit()
#    print("Successfully Updated Top 1000")
        
#scheduler = BackgroundScheduler()
#scheduler.add_job(func=update_top_1000, trigger="interval", hours=1)
#scheduler.start()
#atexit.register(lambda: scheduler.shutdown())

# Late import so modules can import their dependencies properly (proto-blueprint)
from . import views, models

db.create_all()
