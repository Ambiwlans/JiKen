# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: KTest - Kanji test site JiKen
@description: Models
"""

#Base model
from . import db

# Data Types
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey, Text    

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
#    timezone = 
#    browserdata =
    
    #Related
    questions = relationship("QuestionLog", back_populates="testlog")

#TODO ? include time data for ML
class QuestionLog(db.Model):
    __tablename__ = 'questionlog'
    
    #Meta
    id = Column(Integer, primary_key=True)
    
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

#TODO - Include statistical data here? Leave it in ML binary blob?
#TODO ? Expand for answers in other languages/forms (kana vs English vs French) 
# List of all the questions
    # ie. "字 - ji", "蝙 - kou"
class TestMaterial(db.Model):
    __tablename__ = 'testmaterial'
    
    #Meta
    id = Column(Integer, primary_key=True)
    
    #Core
    question = Column(String)       # 剣
    answer =  Column(String)        # blade
    













