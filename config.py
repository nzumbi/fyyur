import os
SECRET_KEY = os.urandom(32)
WTF_CSRF_ENABLED = False
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


# TODO IMPLEMENT DATABASE 
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:abcd@localhost:5432/fyyur_db'

SQLALCHEMY_TRACK_MODIFICATIONS = False