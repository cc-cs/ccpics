'''Entry point for the flask app. Store system wide configurations here.'''

from flask import Flask

app = Flask(__name__)
app.secret_key = b"\x9d\x00\xb1\x80b\xd6\t'\x853V\xbf\xac2\xcd\x98Y\x88\xf3BKO\x9c\xa3"

from app import index
from app import registration
from app import login
from app import questions
