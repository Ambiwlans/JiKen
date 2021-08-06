# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: JiKen - Kanji testing site
@description: The config file
"""


import os
import redis
#from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
#load_dotenv(os.path.join(basedir, '.env'))
    
class DevelopmentConfig:

    # Flask
    DEBUG = True
    
    SECRET_KEY = os.environ.get('DB_SECRET_KEY') or "Ionceateawholeham"
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{user}:{password}@{host}/jiken?charset=utf8mb4'.format(**{
        'user': "Ambiwlans",
        'password' : "test",
        'host' : 'localhost',
    })
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
#    SQLALCHEMY_ECHO=True
    
    # Data
    MAX_QUESTIONS_LOGGED = 4500                                   #Max # of questions before clearing them from SQL 
    MAX_TESTS_LOGGED = 4500                                       #Max # of tests before clearing them from SQL (must be larger than questions/test_length)
    MIN_TEST_LENGTH = 1                                           #Shorter tests won't be logged
    TEST_TIMEOUT = 600                                            #Minutes inactive before tests get dumped to SQL
    
    # Flask-Session
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.from_url(os.environ.get('SESSION_REDIS'))#, decode_responses=True)
    
    # App
    GRAPH_AFTER = 0
    GRAPH_MAX_X = 6750
    MAX_X = 6750
    QUESTION_VARIABLITY = 1.0                                       # .1 = low variance from the prediction, 2 = high variance
    
    # L2R
    SHIFTSIZE_SLOPE = 500                                           # shiftsize = int(round((errorlevel * SHIFTSIZE_SLOPE) / 500) + 1)
    ERRORLEVEL_CUTOFF_PCT = .5                                      # if (errorlevel < ERRORLEVEL_CUTOFF_PCT): continue 
    
class DeploymentConfig:

    # Flask
    DEBUG = False
    
    SECRET_KEY = os.environ.get('DB_SECRET_KEY') or "Ionceateawholeham"
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('CLEARDB_DATABASE_URL').replace('?reconnect=true','?charset=utf8mb4')
    SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_recycle':60
            }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # Data
    MAX_QUESTIONS_LOGGED = 4500                                 #Max # of questions before clearing them from SQL 
    MAX_TESTS_LOGGED = 4500                                     #Max # of tests before clearing them from SQL (must be larger than questions/test_length)
    MIN_TEST_LENGTH = 10                                        #Shorter tests won't be logged
    TEST_TIMEOUT = 120                                           #Minutes inactive before tests get dumped to SQL
    
    # Flask-Session
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.from_url(os.environ.get('SESSION_REDIS'))
    
    # App
    GRAPH_AFTER = 9
    GRAPH_MAX_X = 6750
    MAX_X = 6750
    QUESTION_VARIABLITY = 1.0                                       # .1 = low variance from the prediction, 2 = high variance
        
    # L2R
    SHIFTSIZE_SLOPE = 500                                           # shiftsize = int(round((errorlevel * SHIFTSIZE_SLOPE) / 500) + 1)
    ERRORLEVEL_CUTOFF_PCT = .7                                      # if (errorlevel < ERRORLEVEL_CUTOFF_PCT): continue 
    
#Easy switch for different configs
Config = DeploymentConfig