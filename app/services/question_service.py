import os

from flask import abort, json, jsonify

from .. import app

# TODO: Remove all this duplication between services!!!

DATA_DIR = os.path.join(app.config['DATA_PATH'], 'question')
ESSENTIALS = set(['id', 'title', 'languages'])
UNIQUES = set([])
PUBLIC = set(['id', 'title', 'languages'])
HIDDEN = set([])
FIELDS = ESSENTIALS | UNIQUES | PUBLIC | set([])


##############################################################################
# Helpers
##############################################################################
def fetch_question_ids():
    '''Return all the question ids we have so far.'''
    
    return os.listdir(DATA_DIR)

def fetch_max_question_id():
    '''Return the largest question id created so far AS AN INT.'''

    question_ids = fetch_question_ids()
    
    return int(max(question_ids)[:-4])

def fetch_question_files():
    '''Return all valid question data files.'''
    
    question_ids = fetch_question_ids()
    data_files = [os.path.join(DATA_DIR, id_) for id_ in question_ids]
    question_files = [f for f in data_files if os.path.isfile(f)]

    return question_files

def check_presence(keys=ESSENTIALS, data=None):
    '''Check if the given data contains information for the required set of keys.'''

    if not data or keys - set(data):
        return {'status': 400, 'error': "Required fields not present."}
    
    for key in keys:
        if not data[key]:
            return {'status': 400, 'error': "{} is required.".format(key)}

    return {'status': 200}

def check_uniqueness(keys=UNIQUES, data=None):
    '''Check if the given data is unique in the DB for the provided keys.'''

    question_files = fetch_question_files()
    for question_file in question_files:
        with open(question_file, 'r') as f:
            file_data = json.load(f)
            for key in keys:
                if data[key] == file_data[key]:
                    return {'status': 409, 'error': "{} already in use!".format(key)}

    return {'status': 200}

def save_question(question_id, data):
    '''Save the given data for the question with the provided id.'''
    
    question_data = {k: data.get(k, None) for k in FIELDS}
    new_file_path = os.path.join(DATA_DIR, "{}.txt".format(question_id))
    try:
        with open(new_file_path, 'w') as write_file:
            json.dump(question_data, write_file)
    except EnvironmentError:
        return {'status': 500, 'error': "Internal Server Error while saving."}


##############################################################################
# Workers
##############################################################################
def fetch_questions(queried_info=PUBLIC):
    '''Return a map of all questions with their data enlisted.'''
    
    question_files = fetch_question_files()
    questions = []
    try:
        for question_file in question_files:
            with open(question_file, 'r') as f:
                data = json.load(f)
                questions.append({k: data.get(k, None) for k in queried_info})
    except EnvironmentError:
        return {'status': 500, 'error': 'Internal server error reading data.'}
    
    return {'questions': questions}

def fetch_question(question_id):
    question_file = os.path.join(DATA_DIR, '{}.txt'.format(question_id))
    try:
        with open(question_file, 'r') as f:
            question_data = json.load(f)
            question_data = {k: question_data[k] for k in question_data if k not in HIDDEN}
    except EnvironmentError:
        return {'status': 404, 'error': "Question doesn't exist."}

    return {'question': question_data}

def add_question(question_data):
    # Fetch the next possible id for our new question.
    max_id = fetch_max_question_id()
    question_id = "{0:08d}".format(max_id + 1)
    question_data['id'] = question_id
    
    # Check for presence of required fields.
    essentials_present = check_presence(data=question_data)
    if 'error' in essentials_present:
        return {'status': essentials_present['status'], 'error': essentials_present['error']}
    
    # Check for uniqueness on desired fields.
    uniqueness_check = check_uniqueness(data=question_data)
    if 'error' in uniqueness_check:
        return {'status': uniqueness_check['status'], 'error': uniqueness_check['error']}
    
    # Store the information if no errors encountered.
    save_question(question_id, question_data)

    question_data = {k: question_data[k] for k in question_data if k not in HIDDEN}
    
    return {'question': question_data}


###############################################################################
# Service API endpoints
###############################################################################
@app.route('/pics-service/api/v1.0/questions', methods=['GET'])
def get_questions():
    questions = fetch_questions()
    if 'error' in questions:
        abort(questions['status'], questions['error'])
    return jsonify(questions)

@app.route('/pics-service/api/v1.0/questions/<question_id>', methods=['GET'])
def get_question(question_id):
    question = fetch_question(question_id)
    if 'error' in question:
        abort(question['status'], question['error'])
    return jsonify(question)

@app.route('/pics-service/api/v1.0/questions', methods=['POST'])
def create_question():
    question_creation = add_question(question_data=request.json)
    if 'error' in question_creation:
        abort(question_creation['status'], question_creation['error'])
    return jsonify(question_creation), 201
