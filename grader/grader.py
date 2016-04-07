import json
import os
import re
import requests
import subprocess
import urllib

queue_url = 'http://localhost:5000/pics-service/api/v1.0/submissions-queue'
dequeue_url = 'http://localhost:5000/pics-service/api/v1.0/submissions-dequeue'
chronicle_url = 'http://localhost:5000/pics-service/api/v1.0/results-chronicle'
submission_url = 'http://localhost:5000/pics-service/api/v1.0/submissions/{}'
question_url = 'http://localhost:5000/pics-service/api/v1.0/questions/{}'
solution_url = 'http://localhost:5000/pics-service/api/v1.0/solutions/{}/{}'
result_url = 'http://localhost:5000/pics-service/api/v1.0/results'

data_dir = os.path.join(os.getcwd(), '../data/results/')

def get_new_submissions():
    queue_request_response = requests.get(url=queue_url)
    if queue_request_response:
        queue = queue_request_response.json()['queue']
    else:
        return {'status': 400, 'error': "Failed to fetch the submissions queue."}

    chronicle_request_response = requests.get(url=chronicle_url)
    if chronicle_request_response:
        chronicle = chronicle_request_response.json()['chronicle']
    else:
        return {'status': 400, 'error': "Failed to fetch the results chronicle."}

    new_submission_ids = set(queue) - set(chronicle)

    return {'new-submission-ids': new_submission_ids}

def get_resource(resource_url, resource_params):
    request_url = resource_url.format(*[urllib.parse.quote(param) for param in resource_params])
    resource_request_response = requests.get(url=request_url)
    if resource_request_response:
        resource = resource_request_response.json()
    else:
        return {'status': 400, 'error': "Failed to fetch the resource details."}
    return resource

def submit_result(data):
    result_submission_response = requests.post(url=result_url, json=data)
    if result_submission_response == 201:
        return {'status': 201}
    return result_submission_response    

def process_submissions():
    submission_ids = get_new_submissions()['new-submission-ids']
    result_submission_responses = []
    for submission_id in submission_ids:
        submission = get_resource(submission_url, [submission_id])
        if 'error' in submission:
            return submission
        else:
            submission = submission['submission']
        
        question = get_resource(question_url, [submission['question-id']])
        if 'error' in question:
            return question
        else:
            question = question['question']

        solution = get_resource(solution_url, [submission['question-id'], submission['language']])
        if 'error' in solution:
            return solution
        else:
            solution = solution['solution']
        
        test_results = grade_submission(submission=submission, solution=solution, question=question)
        verdict = 'fail' if 'fail' in test_results else 'pass'
        result = {'user-id': submission['user-id'],
                  'submission-id': submission['id'],
                  'question-id': question['id'],
                  'test-results': test_results,
                  'verdict': verdict
                  }
        result_submission_responses.append(submit_result(data=result))

    return result_submission_responses        

def run_cpp(filename, test_cases,time_out):
    subprocess.Popen('g++ %s -o %s' % (filename + '.cpp', filename + '.exe'), shell=True, stdout=subprocess.PIPE).stdout.read()
    outputs = []
    # run test cases scenario (input)
    if test_cases:
        for test in test_cases:
            p = subprocess.Popen('./%s' % (filename + '.exe'), shell=True,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
            output = p.communicate(input=bytearray(test, 'utf-8'), timeout=time_out)[0]
            outputs.append(output)
    # run no input scenario
    else:
        p = subprocess.Popen('./%s' % (filename + '.exe'), shell=True,
                                  stdout=subprocess.PIPE)
        output = p.communicate(timeout=time_out)[0]
        outputs.append(output)
    return outputs

def get_java_name(s):
    pclass = "(public(\s+)class(\s+))[A-Za-z0-9_]+"
    z = re.search(pclass, s)
    return z.group(0).split()[2]

def run_java(filename, test_cases, time_out):
    subprocess.Popen('javac %s' % (filename + '.java'), shell=True, stdout=subprocess.PIPE).stdout.read()
    outputs = []
    if test_cases:
        for test in test_cases:
            p = subprocess.Popen('java %s' % (filename), shell=True,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
            output = p.communicate(input=bytearray(test, 'utf-8'), timeout=time_out)[0]
            outputs.append(output)
    # run no input scenario
    else:
        p = subprocess.Popen('java %s' % (filename), shell=True,
                                  stdout=subprocess.PIPE)
        output = p.communicate(timeout=time_out)[0]
        outputs.append(output)
    return outputs
        
def load_code(source_json, test_cases, time_out):
    extension = '.'
    language = source_json['language'].lower()
    if language == 'c++':
        extension = '.cpp'
        filename = 'source_json' + source_json['id']
    elif language == 'java':
        extension = '.java'
        filename = get_java_name(source_json['source-code'])
    with open(filename + extension, 'w') as tmp_file:
        tmp_file.write(source_json['source-code'])
    if language == 'c++':
        z = run_cpp(filename, test_cases, time_out)
        os.system('rm %s' % (filename + '.cpp'))
        os.system('rm %s' % (filename + '.exe'))
        return z
    elif language == 'java':
        z = run_java(filename, test_cases, time_out)
        os.system('rm %s' % (filename + '.java'))
        os.system('rm %s' % (filename + '.class'))
        return z
        
def grade_submission(submission, solution, question):
    test_cases = question['test-cases']
    time_out = question['time-out']
    outputs = load_code(submission, test_cases, time_out)
    expecteds = load_code(solution, test_cases, time_out)
    grades = []
    if outputs == 'Unsupported Language':
        return outputs
    for output, expected in zip(outputs, expecteds):
        if output == expected:
            grades.append('pass')
        else:
            grades.append('fail')
    return grades

if __name__ == '__main__':
    print(process_submissions())
