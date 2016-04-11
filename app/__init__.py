'''Entry point for the flask app. Store system wide configurations here.'''

import os

from flask import Flask

app = Flask(__name__)
app.secret_key = b"\x9d\x00\xb1\x80b\xd6\t'\x853V\xbf\xac2\xcd\x98Y\x88\xf3BKO\x9c\xa3"
app.config['ROOT_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
app.config['DATA_PATH'] = os.path.join(app.config['ROOT_PATH'], "data")
app.config['SERVICE_URL'] = 'pics-service/api/v1.0/'
app.config['ADMINS'] = ['00000000', '00000001', '00000002', '00000003', '00000004']

# For nicer time display
# from .lib.momentjs import momentjs # This didn't work on Ryan's computer, why?
from . import lib
app.jinja_env.globals['momentjs'] = lib.momentjs.momentjs

from . import errorhandler
from . import services
from . import views


