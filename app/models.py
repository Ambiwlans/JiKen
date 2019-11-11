# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: JiKen - Kanji testing site
@description: Models
"""

#Base model
from app import db

# Data Types
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey, Text, Numeric    

# Database
from sqlalchemy.orm import relationship, backref
    

###############################################################################
### Tests
###############################################################################
    
#TODO ? include metauser data for ML
class TestLog(db.Model):
    __tablename__ = 'testlog'
    
    #Meta
    id = Column(Integer, primary_key=True)
    
    #Core
    a = Column(Integer)                   # predicted number of kanji known
    t = Column(Numeric(asdecimal=False))  # predicted spread
    
#    timezone = 
#    browserdata =
#    ip = 
#    start_time
    
    #Related
    questions = relationship("QuestionLog", back_populates="testlog")

#TODO ? include time data for ML
#TODO ? Switch to a composite key to qnum + testlogid the primary key, and ditch the id
class QuestionLog(db.Model):
    __tablename__ = 'questionlog'
    
    #Meta
    id = Column(Integer, primary_key=True)
    #qnum = Column(Integer)                      
    
    #Core
    testlogid = Column(Integer, ForeignKey('testlog.id'), nullable=False)
    testmaterialid = Column(Integer, ForeignKey('testmaterial.id'), nullable=False)
    score = Column(Boolean)
    
#    timegiven = 
#    timeanswered = 
#    timeelapsed = 
    
    #Related
    testlog = relationship("TestLog", back_populates="questions")
    testmaterial = relationship("TestMaterial")

#TODO ? Include statistical data here? Leave it in ML binary blob?
#TODO ? Expand for answers in other languages/forms (kana vs English vs French) 
# List of all the questions
    # ie. "字 - ji", "蝙 - kou"
class TestMaterial(db.Model):
    __tablename__ = 'testmaterial'
    
    #Meta
    id = Column(Integer, primary_key=True)
    
    #Core
    kanji = Column(String)       # 剣
    meaning =  Column(String)        # blade
    
    onyomi = Column(String)
    kunyomi = Column(String)
    grade = Column(String)
    jlpt = Column(String)
    kanken = Column(String)
    
    #Statistical
    frequency = Column(Integer)
    my_rank = Column(Integer)

# Meta information
    # Only 1 row, stored in DB for convenience
class MetaStatistics(db.Model):
    __tablename__ = 'metastatistics'
    
    #Meta
    id = Column(Integer, primary_key=True)
    
    #Core
    default_kanji = Column(Integer, default= 400)       # Number of kanji people know on avg
    default_tightness = Column(Numeric(asdecimal=False), default= 0.05)  # typical knowledge spread








#db.create_all() 
#db.session.commit() 


