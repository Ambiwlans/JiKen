# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: KTest - Kanji test site JiKen
@description: The init, run via 'flask run' as an installed package
"""

#General Python
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

from flask_bootstrap import Bootstrap


# Setup Flask App
app = Flask(__name__)
app.config.from_object('KTest.config.Config')
    
db = SQLAlchemy(app)
 

# Setup Bootstrap 4.1.0 with jquery 3.3.1
Bootstrap(app)

# Late import so modules can import their dependencies properly (proto-blueprint)
from . import views, models

db.create_all()

# Reformat base DB taken from KANJIDIC
def initial_DB_reformat():
    data = db.session.query(models.TestMaterial).all()    
    for item in data:
        if "Kyōiku-Jōyō (1st" in item.grade:
            item.grade = 1
        elif "Kyōiku-Jōyō (2nd" in item.grade:
            item.grade = 2
        elif "Kyōiku-Jōyō (3rd" in item.grade:
            item.grade = 3
        elif "Kyōiku-Jōyō (4th" in item.grade:
            item.grade = 4
        elif "Kyōiku-Jōyō (5th" in item.grade:
            item.grade = 5
        elif "Kyōiku-Jōyō (6th" in item.grade:
            item.grade = 6
        elif "Jōyō (1st" in item.grade:
            item.grade = 7
        elif "Jōyō (2nd" in item.grade:
            item.grade = 8
        elif "Jōyō (3rd" in item.grade:
            item.grade = 9
        elif "Kyōiku-Jōyō (high" in item.grade:
            item.grade = 10
        elif "Hyōgaiji (former Jinmeiyō candidate)" in item.grade:
            item.grade = 11
        elif "Jinmeiyō (used in names)" in item.grade:
            item.grade = 13
        elif "i" in item.grade:
            item.grade = 14
            
        if "1" in (item.jlpt or ""):
            item.jlpt = 1
        elif "2" in (item.jlpt or ""):
            item.jlpt = 2
        elif "3" in (item.jlpt or ""):
            item.jlpt = 3
        elif "4" in (item.jlpt or ""):
            item.jlpt = 4
        elif "5" in (item.jlpt or ""):
            item.jlpt = 5
        else:
            item.jlpt = 6
            
        item.meaning = item.meaning.replace(";","; ")

#initial_DB_reformat

# Setup cron/scheduler to update kanji ranks and defaults
def update_meta():
    # update our meta values
    db.session.query(models.MetaStatistics).first().default_kanji = db.session.query(func.avg(models.TestLog.a)) \
        .outerjoin(models.TestLog.questions) \
        .group_by(models.TestLog) \
        .having(func.count_(models.TestLog.questions)>25)[0][0]
    db.session.query(models.MetaStatistics).first().default_tightness = db.session.query(func.avg(models.TestLog.t)) \
        .outerjoin(models.TestLog.questions) \
        .group_by(models.TestLog) \
        .having(func.count_(models.TestLog.questions)>25)[0][0]
    db.session.commit()
    
    # update our ranks
    data = db.session.query(models.TestMaterial).all()    
    ranks = [r for r, in db.session.query(models.TestMaterial.my_rank)]
    
#    cur_rank = db.session.query(TestMaterial).filter(TestMaterial.frequency is not None).count()
#    print("Cur rank: " + str(cur_rank))
    
    for i in range(len(data)):
        # Use the frequency rates as a base
        ranks[i] = int(data[i].frequency or 0)
        
        if data[i].frequency is None:
            ranks[i] = 7000
        
        # Penalize based on JLPT, kanken, jouyou levels
        
        #
        data[i].my_rank = ranks[i]
    db.session.commit()
        
    print("Successfully Updated Ranks, Meta vals")
        
update_meta() 
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_meta, trigger="interval", days=10)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())





