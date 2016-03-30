#!venv/bin/python

import os

from app import app
app.config['ROOT_PATH'] = os.path.dirname(os.path.abspath(__file__))
app.config['DATA_PATH'] = os.path.join(app.config['ROOT_PATH'], "data")

if __name__ == "__main__":
    app.run(debug=True)
