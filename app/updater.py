# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: JiKen - Kanji testing site
@description: Updater
"""

from sqlalchemy import func

#Models
from app import models

#Session
from app import db

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
        
    #TODO - throw out overly short tests here

    print("Successfully Updated Meta vals")
    
# Reformat base DB taken from KANJIDIC
def initial_DB_reformat():
    data = db.session.query(models.TestMaterial).all()    
    ranks = [r for r, in db.session.query(models.TestMaterial.my_rank)]
    
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