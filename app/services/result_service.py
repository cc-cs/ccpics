import os

from datetime import datetime

from flask import abort, json, jsonify, request

from .. import app

from . import submission_service

# TODO: Abstract away all the data operations into a Model interface.
# TODO: Remove all this duplication between services!!!
# TODO: Add authentication for some of these info.

DATA_DIR = os.path.join(app.config['DATA_PATH'], 'result')
ESSENTIALS = set(['user-id', 'submission-id', 'test-results', 'verdict'])
UNIQUES = set([])
PUBLIC = set(['id', 'user-id', 'submission-id', 'verdict', 'timestamp'])
HIDDEN = set([])
FIELDS = ESSENTIALS | UNIQUES | PUBLIC | set([])


##############################################################################
# Helpers
##############################################################################
def fetch_result_ids():
    '''Return all the result ids we have so far.'''

    return [f for f in os.listdir(DATA_DIR) if f.endswith('.txt')]

def fetch_max_result_id():
    '''Return the largest result id created so far AS AN INT.'''

    result_ids = fetch_result_ids()

    return int(max(result_ids)[:8]) if result_ids else -1

def fetch_result_files():
    '''Return all valid result data files.'''
    
    result_ids = fetch_result_ids()
    data_files = [os.path.join(DATA_DIR, id_) for id_ in result_ids]
    result_files = [f for f in data_files if os.path.isfile(f)]

    return result_files

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

    result_files = fetch_result_files()
    for result_file in result_files:
        with open(result_file, 'r') as f:
            file_data = json.load(f)
            for key in keys:
                if data[key] == file_data[key]:
                    return {'status': 409, 'error': "{} already in use!".format(key)}

    return {'status': 200}

def save_result(result_id, data):
    '''Save the given data for the result with the provided id.'''
    
    result_data = {k: data.get(k, None) for k in FIELDS}
    new_file_path = os.path.join(DATA_DIR, "{}.txt".format(result_id))
    try:
        with open(new_file_path, 'w') as write_file:
            json.dump(result_data, write_file)
    except EnvironmentError:
        return {'status': 500, 'error': "Internal Server Error while saving."}

    return {'status': 200}

def fetch_chronicled_results():
    '''Return all the results that are on chronicle to be processed by the grader'''

    try:
        with open(os.path.join(DATA_DIR, "grading.chronicle"), "r") as f:
            chronicle = json.load(f)
    except EnvironmentError as e:
        chronicle = {'chronicle': {}}
    except ValueError:
        return {'status': 500, 'error': 'Internal Server Error'}

    return chronicle

def chronicle_result(result_id, timestamp):
    '''Chronicle the result to be processed by the grader.'''

    chronicle = fetch_chronicled_results()
    if 'error' in chronicle:
        return chronicle
    chronicle['chronicle'][result_id] = timestamp

    try:
        with open(os.path.join(DATA_DIR, 'grading.chronicle'), 'w') as f:
            json.dump(chronicle, f)
    except EnvironmentError:
        return {'status': 500, 'error': 'Internal Server Error while adding.'}

    return {'status': 200}

##############################################################################
# Workers
##############################################################################
def fetch_results(queried_info=PUBLIC):
    '''Return a map of all results with their data enlisted.'''
    
    result_files = fetch_result_files()
    results = []
    try:
        for result_file in result_files:
            with open(result_file, 'r') as f:
                data = json.load(f)
                results.append({k: data.get(k, None) for k in queried_info})
    except EnvironmentError:
        return {'status': 500, 'error': 'Internal server error reading data.'}
    
    return {'results': results}

def fetch_result(result_id):
    result_file = os.path.join(DATA_DIR, '{}.txt'.format(result_id))
    try:
        with open(result_file, 'r') as f:
            result_data = json.load(f)
            result_data = {k: result_data[k] for k in result_data if k not in HIDDEN}
    except EnvironmentError:
        return {'status': 404, 'error': "Result doesn't exist."}

    return {'result': result_data}

def add_result(result_data):
    # Fetch the next possible id for our new result.
    max_id = fetch_max_result_id()
    result_id = "{0:08d}".format(max_id + 1)
    result_data['id'] = result_id
    
    # Check for presence of required fields.
    essentials_present = check_presence(data=result_data)
    if 'error' in essentials_present:
        return {'status': essentials_present['status'], 'error': essentials_present['error']}
    
    # Check for uniqueness on desired fields.
    uniqueness_check = check_uniqueness(data=result_data)
    if 'error' in uniqueness_check:
        return {'status': uniqueness_check['status'], 'error': uniqueness_check['error']}

    # Add a timestamp.
    result_data['timestamp'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S Z")

    # Update the submission with the result information.
    submission_updated = submission_service.update_result(result_data)
    if 'error' in submission_updated:
        return submisison_updated
    
    # Chronicle the result as graded.
    chronicle_result(result_id, result_data['timestamp'])
    result_data['status'] = 'Chronicled'

    # Store the information if no errors encountered.
    saved = save_result(result_id, result_data)
    if 'error' in saved:
        return saved

    result_data = {k: result_data[k] for k in result_data if k not in HIDDEN}
    
    return {'result': result_data}


###############################################################################
# Service API endpoints
###############################################################################
@app.route('/pics-service/api/v1.0/results', methods=['GET'])
def get_results():
    results = fetch_results()
    if 'error' in results:
        abort(results['status'], results['error'])
    return jsonify(results)

@app.route('/pics-service/api/v1.0/results/<result_id>', methods=['GET'])
def get_result(result_id):
    result = fetch_result(result_id)
    if 'error' in result:
        abort(result['status'], result['error'])
    return jsonify(result)

@app.route('/pics-service/api/v1.0/results', methods=['POST'])
def create_result():
    result_creation = add_result(result_data=request.json)
    if 'error' in result_creation:
        abort(result_creation['status'], result_creation['error'])
    return jsonify(result_creation), 201

@app.route('/pics-service/api/v1.0/results-chronicle', methods=['GET'])
def get_chronicled_results():
    results_chronicle = fetch_chronicled_results()
    if 'error' in results_chronicle:
        abort(results_chronicle['status'], results_chronicle['error'])
    return jsonify(results_chronicle)
