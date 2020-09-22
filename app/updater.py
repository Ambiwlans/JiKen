# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: JiKen - Kanji testing site
@description: Updater
"""

from flask import current_app

import pickle
from sqlalchemy import func
from sqlalchemy.sql import exists
import numpy as np

import datetime

import traceback

#Models
from .models import TestMaterial, \
    TestLog, QuestionLog, \
    MetaStatistics
    
#DB
from app import db

def update_TestQuestionLogs(app):
    #move stuff from redis to SQL (Ql,Tl)
    with app.app_context():
        print("--------LOG UPDATE------------")
#        x = current_app.config['SESSION_REDIS'].scan()
#        print(x)
        for sess in current_app.config['SESSION_REDIS'].scan_iter("session:*"):
            try:
                #print("Moving to SQL DB -- " + str(sess))
                data = pickle.loads(current_app.config['SESSION_REDIS'].get(sess))
                
                # Skip sessions without attached tests after adding a timeout to clear out old sessions faster
                if (data.get('last_touched', -1) == -1):
                    data['last_touched'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    current_app.config['SESSION_REDIS'].set(sess, pickle.dumps(data))
                    print("Added time to empty session")
                    continue
                
                #Check timestamp to see if we should move it to SQL (>TEST_TIMEOUT mins since last touched)
                if datetime.datetime.utcnow() - \
                        datetime.datetime.strptime(data.get('last_touched', datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')), '%Y-%m-%d %H:%M:%S')\
                        < datetime.timedelta(minutes=current_app.config['TEST_TIMEOUT']):
                    print("Skipping active test from: " + str(datetime.datetime.utcnow() - datetime.datetime.strptime(data.get('last_touched', datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')), '%Y-%m-%d %H:%M:%S')))
                    continue
                
                #Don't bother recording incomplete tests
                if len(data.get('QuestionLog', 0)) < current_app.config['MIN_TEST_LENGTH']:
                    current_app.config['SESSION_REDIS'].delete(sess)
                    print("Trashing pointless short/non test")
                    continue
                
                #Don't save tests with duplicted ids
                if db.session.query(exists().where(TestLog.id == data['TestLog']['id'])).scalar():
                    current_app.config['SESSION_REDIS'].delete(sess)
                    print("Trashing already saved test #"+ str(data['TestLog']['id']))
                    continue
                
                #Create new test
                addTest = TestLog(
                    id = data['TestLog']['id'],
                    a = int(data['TestLog']['a']),
                    t =  data['TestLog']['t'],
                    ip =  data['TestLog']['ip'],
                    start_time =  data['TestLog']['start_time'],
                    number_of_questions = len(data['QuestionLog']))
                db.session.add(addTest)
                db.session.commit()
                
                #Bulk dump the question log
                db.engine.execute(
                        QuestionLog.__table__.insert(),
                        [{"testlogid" : addTest.id,
                          "testmaterialid" : q.testmaterialid,
                          "score" : q.score} for i, q in data['QuestionLog'].iterrows()])
    
                print("Upped Test #: " + str(addTest.id) + " with " + str(len(data.get('QuestionLog', 0))) + " questions.")
#                print(data['QuestionLog'])
                
            except Exception: 
                import pprint
                print("Failed to save test to SQL. Session content:")
                pprint.pprint(data)
                traceback.print_exc()
                pass
                
            #Delete session (fail or succeed)
            current_app.config['SESSION_REDIS'].delete(sess)
            
        print("Updated Logs")
        
    
# Setup cron/scheduler to update kanji ranks and defaults
def update_meta(app):
    # update our meta values
    with app.app_context():
        # get the averages after filtering out outliers, tend towards the middle
        current_app.config['SESSION_REDIS'].set('default_tightness', 
            (db.session.query(func.avg(TestLog.t)) \
            .filter(TestLog.number_of_questions > 25) \
            .filter(TestLog.t > 0.001) \
            .filter(TestLog.t < 0.08)[0][0] + .005)/2
            )
        db.session.query(MetaStatistics).first().default_tightness = float(current_app.config['SESSION_REDIS'].get('default_tightness'))
        
        current_app.config['SESSION_REDIS'].set('default_kanji', 
            int((db.session.query(func.avg(TestLog.a)) \
            .filter(TestLog.number_of_questions > 25) \
            .filter(TestLog.a > 100) \
            .filter(TestLog.a < 5000)[0][0] + 2000)/2)
            )
        db.session.query(MetaStatistics).first().default_kanji = int(current_app.config['SESSION_REDIS'].get('default_kanji'))

        avg_known = int(db.session.query(func.avg(TestLog.a)).filter(TestLog.number_of_questions > 10)[0][0])
        current_app.config['SESSION_REDIS'].set('avg_known', avg_known)
        db.session.query(MetaStatistics).first().default_kanji = avg_known

        avg_answered = int(db.session.query(func.avg(TestLog.number_of_questions)).filter(TestLog.number_of_questions > 10)[0][0])
        current_app.config['SESSION_REDIS'].set('avg_answered', avg_answered)
        db.session.query(MetaStatistics).first().default_kanji = avg_answered
        
        db.session.commit()
        
        print("Successfully Updated Meta vals")
        print("A = " + str(int(current_app.config['SESSION_REDIS'].get('default_kanji'))))
        print("T = " + str(float(current_app.config['SESSION_REDIS'].get('default_tightness'))))
        print("Known = " + str(avg_known))
        print("Answered = " + str(avg_answered))
        
# Clear ancient logs
def clear_old_logs(app):
    with app.app_context():
        print("--------LOG CLEANUP------------")
        #Delete old questions first to avoid orphaned questions
        cutoff = max(db.session.query(QuestionLog.id).count() - current_app.config['MAX_QUESTIONS_LOGGED'], 0)
        cutoff_id = db.session.query(QuestionLog).order_by(QuestionLog.id)[cutoff].id
        db.session.query(QuestionLog).filter(QuestionLog.id < cutoff_id).delete()
        print(str(cutoff) + " old questions deleted")
        
        cutoff = max(db.session.query(TestLog.id).count() - current_app.config['MAX_TESTS_LOGGED'], 0)
        cutoff_id = db.session.query(TestLog).order_by(TestLog.id)[cutoff].id
        db.session.query(TestLog).filter(TestLog.id < cutoff_id).delete()
        print(str(cutoff) + " old tests deleted")
        
        db.session.commit()
        
# Reformat base DB taken from KANJIDIC
def initial_DB_reformat():
    data = db.session.query(TestMaterial).all()    
    ranks = [r for r, in db.session.query(TestMaterial.my_rank)]
    
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
            
#        item.meaning = item.meaning.replace(";","; ")
        
    # Find some good starting point for rankings of kanji
    for i in range(len(data)):
        # Use the frequency rates as a base
        ranks[i] = int(data[i].frequency or 0)
        
        if data[i].frequency is None:
            ranks[i] = 4000
        
        # Penalize based on JLPT, kanken, jouyou levels
        ranks[i] += int(data[i].grade) * 50
        ranks[i] -= (int(data[i].jlpt)-6) * 50
        if data[i].kanken:
            ranks[i] -= (int(data[i].kanken)+1) * 50 if data[i].kanken.isdigit() else 0
            if data[i].kanken == "pre-2":
                ranks[i] -= 3 * 50
            elif data[i].kanken == "2":
                ranks[i] += 50
            elif data[i].kanken == "pre-1":
                ranks[i] -= 1 * 50
    
    t = np.array(ranks).argsort()
    ranks = (t.argsort() + 1).tolist()
    
    for i in range(len(data)):
        data[i].my_rank = ranks[i]
    
    print("Initial DB reform complete!")