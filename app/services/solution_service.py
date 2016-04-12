import os

from datetime import datetime

from flask import abort, json, jsonify, request

from .. import app

# TODO: Abstract away all the data operations into a Model interface.
# TODO: Remove all this duplication between services!!!
# TODO: Add authentication for some of these info.

DATA_DIR = os.path.join(app.config['DATA_PATH'], 'solution')
ESSENTIALS = set(['question-id', 'language', 'source-code'])
UNIQUES = set([])
PUBLIC = set(['id', 'language', 'question-id', 'question-title'])
HIDDEN = set([])
FIELDS = ESSENTIALS | UNIQUES | PUBLIC | set([])


##############################################################################
# Helpers
##############################################################################
def fetch_solution_ids():
    '''Return all the solution ids we have so far.'''

    return [f for f in os.listdir(DATA_DIR) if f.endswith('.txt')]

def fetch_max_solution_id():
    '''Return the largest solution id created so far AS AN INT.'''

    solution_ids = fetch_solution_ids()

    return int(max(solution_ids)[:8]) if solution_ids else -1

def fetch_solution_files():
    '''Return all valid solution data files.'''
    
    solution_ids = fetch_solution_ids()
    data_files = [os.path.join(DATA_DIR, id_) for id_ in solution_ids]
    solution_files = [f for f in data_files if os.path.isfile(f)]

    return solution_files

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

    solution_files = fetch_solution_files()
    for solution_file in solution_files:
        with open(solution_file, 'r') as f:
            file_data = json.load(f)
            for key in keys:
                if data[key] == file_data[key]:
                    return {'status': 409, 'error': "{} already in use!".format(key)}

    return {'status': 200}

def save_solution(solution_id, data):
    '''Save the given data for the solution with the provided id.'''
    
    solution_data = {k: data.get(k, None) for k in FIELDS}
    new_file_path = os.path.join(DATA_DIR, "{}.txt".format(solution_id))
    try:
        with open(new_file_path, 'w') as write_file:
            json.dump(solution_data, write_file)
    except EnvironmentError:
        return {'status': 500, 'error': "Internal Server Error while saving."}

    return {'status': 200}

##############################################################################
# Workers
##############################################################################
def fetch_solutions(queried_info=PUBLIC):
    '''Return a map of all solutions with their data enlisted.'''
    
    solution_files = fetch_solution_files()
    solutions = []
    try:
        for solution_file in solution_files:
            with open(solution_file, 'r') as f:
                data = json.load(f)
                solutions.append({k: data.get(k, None) for k in queried_info})
    except EnvironmentError:
        return {'status': 500, 'error': 'Internal server error reading data.'}
    
    return {'solutions': solutions}

def fetch_solution(solution_id):
    solution_file = os.path.join(DATA_DIR, '{}.txt'.format(solution_id))
    try:
        with open(solution_file, 'r') as f:
            solution_data = json.load(f)
            solution_data = {k: solution_data[k] for k in solution_data if k not in HIDDEN}
    except EnvironmentError:
        return {'status': 404, 'error': "Solution doesn't exist."}

    return {'solution': solution_data}

def add_solution(solution_data):
    # Fetch the next possible id for our new solution.
    max_id = fetch_max_solution_id()
    solution_id = "{0:08d}".format(max_id + 1)
    solution_data['id'] = solution_id
    
    # Check for presence of required fields.
    essentials_present = check_presence(data=solution_data)
    if 'error' in essentials_present:
        return {'status': essentials_present['status'], 'error': essentials_present['error']}
    
    # Check for uniqueness on desired fields.
    uniqueness_check = check_uniqueness(data=solution_data)
    if 'error' in uniqueness_check:
        return {'status': uniqueness_check['status'], 'error': uniqueness_check['error']}

    # Store the information if no errors encountered.
    save_solution(solution_id, solution_data)

    solution_data = {k: solution_data[k] for k in solution_data if k not in HIDDEN}
    
    return {'solution': solution_data}


###############################################################################
# Service API endpoints
###############################################################################
@app.route('/pics-service/api/v1.0/solutions', methods=['GET'])
def get_solutions():
    solutions = fetch_solutions()
    if 'error' in solutions:
        abort(solutions['status'], solutions['error'])    
    return jsonify(solutions)

@app.route('/pics-service/api/v1.0/solutions/<question_id>/<language>', methods=['GET'])
def get_parametrized_solution(question_id, language):
    solutions = fetch_solutions()
    if 'error' in solutions:
        abort(solutions['status'], solutions['error'])

    solutions['solutions'] = [solution for solution in solutions['solutions']
                              if solution['question-id'] == question_id and
                              solution['language'] == language]
    solution_id = solutions['solutions'][0]['id']

    solution = fetch_solution(solution_id)
    if 'error' in solution:
        abort(solution['status'], solution['error'])
    return jsonify(solution)

@app.route('/pics-service/api/v1.0/solutions/<solution_id>', methods=['GET'])
def get_solution(solution_id):
    solution = fetch_solution(solution_id)
    if 'error' in solution:
        abort(solution['status'], solution['error'])
    return jsonify(solution)

@app.route('/pics-service/api/v1.0/solutions', methods=['POST'])
def create_solution():
    solution_creation = add_solution(solution_data=request.json)
    if 'error' in solution_creation:
        abort(solution_creation['status'], solution_creation['error'])
    return jsonify(solution_creation), 201
