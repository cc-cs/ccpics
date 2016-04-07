#!venv/bin/python

from flask import url_for

from app import app

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
