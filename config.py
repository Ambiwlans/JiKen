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
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{user}:{password}@{host}/jiken?charset=utf8'.format(**{
        'user': "Ambiwlans",
        'password' : "test",
        'host' : 'localhost',
    })
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_ECHO=True
    
    # Flask-Session
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.from_url(os.environ.get('SESSION_REDIS'))
    
    # App
    GRAPH_MAX_X = 4000
    MAX_X = 6183
    
class DeploymentConfig:

    # Flask
    DEBUG = True
    
    SECRET_KEY = os.environ.get('DB_SECRET_KEY') or "Ionceateawholeham"
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('CLEARDB_DATABASE_URL').replace('?reconnect=true','')
    SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_recycle':60
            }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    
    # Flask-Session
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.from_url(os.environ.get('SESSION_REDIS'))
    
    # App
    GRAPH_MAX_X = 6000
    MAX_X = 6183
    
#Easy switch for different configs
Config = DeploymentConfig