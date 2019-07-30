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
    
class TestLog(db.Model):
    __tablename__ = 'testlog'
    
    #Meta
    id = Column(Integer, primary_key=True)
    
    #Related
    questions = relationship("Test")

class QuestionLog(db.Model):
    __tablename__ = 'questionlog'
    
    #Meta
    id = Column(Integer, primary_key=True)
    
#    testlogid = Column(ForeignKey)
    
    #Core
#    questionid = Column(ForeignKey)
    answer = Column(Boolean)
    
# List of all the questions
    # ie. "字", "蝙"
class Question(db.Model):
    __tablename__ = 'question'
    
    #Meta
    id = Column(Integer, primary_key=True)
    
    #Core
    body = Column(String)














