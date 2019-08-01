# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: KTest - Kanji test site JiKen
@description: The config file
"""


import os
basedir = os.path.abspath(os.path.dirname(__file__))
    
class DevelopmentConfig:

    # Flask
    DEBUG = True
    
    SECRET_KEY = 'Ionceateawholeham'
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    
#Easy switch for different configs
Config = DevelopmentConfig