import json
import os
import re
import requests
import subprocess
import urllib
import resource

data_dir = os.path.join(os.getcwd(), '../data/results/')

remote_url = 'http://ccpics42.pythonanywhere.com/'
local_url = 'http://localhost:5000/'
urls = {}

def set_urls(url_root):
    urls['queue_url'] = url_root + 'pics-service/api/v1.0/submissions-queue'
    urls['dequeue_url'] = url_root + 'pics-service/api/v1.0/submissions-dequeue'
    urls['chronicle_url'] = url_root + 'pics-service/api/v1.0/results-chronicle'
    urls['submission_url'] = url_root + 'pics-service/api/v1.0/submissions/{}'
    urls['question_url'] = url_root + 'pics-service/api/v1.0/questions/{}'
    urls['solution_url'] = url_root + 'pics-service/api/v1.0/solutions/{}/{}'
    urls['result_url'] = url_root + 'pics-service/api/v1.0/results'

def get_new_submissions():
    queue_request_response = requests.get(url=urls['queue_url'])
    if queue_request_response:
        queue = queue_request_response.json()['queue']
    else:
        return {'status': 400, 'error': "Failed to fetch the submissions queue."}

    chronicle_request_response = requests.get(url=urls['chronicle_url'])
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
        print(request_url)
        print(resource_request_response)
        resource = resource_request_response.json()
    else:
        return {'status': 400, 'error': "Failed to fetch the resource details."}
    return resource

def submit_result(data):
    result_submission_response = requests.post(url=urls['result_url'], json=data)
    if result_submission_response == 201:
        return {'status': 201}
    return result_submission_response    

def process_submissions():
    submission_ids = get_new_submissions()['new-submission-ids']
    result_submission_responses = []
    for submission_id in submission_ids:
        submission = get_resource(urls['submission_url'], [submission_id])
        if 'error' in submission:
            return submission
        submission = submission['submission']
        
        question = get_resource(urls['question_url'], [submission['question-id']])
        if 'error' in question:
            return question
        question = question['question']

        solution = get_resource(urls['solution_url'], [submission['question-id'], submission['language']])
        if 'error' in solution:
            return solution
        solution = solution['solution']

        test_results = grade_submission(submission=submission, solution=solution, question=question)
        result = {
            'user-id': submission['user-id'],
            'submission-id': submission['id'],
            'test-results': test_results,
            'verdict': test_results['verdict'],
        }
        result_submission_responses.append(submit_result(data=result))

        return result_submission_responses        

TIMEOUT_ERROR = 'TO'
COMPILATION_ERROR = 'CE'

def file_create(source_json):
    os.system('rm -rf temp')
    os.system('mkdir temp')
    extension = '.'
    language = source_json['language'].lower()
    
    if language == 'c++':
        extension = '.cpp'
        filename = 'temp/source_json' + source_json['id']
    elif language == 'java':
        extension = '.java'
        filename = 'temp/' + get_java_name(source_json['source-code'])

    with open(filename + extension, 'w') as tmp_file:
        tmp_file.write(source_json['source-code'])

    return filename

def run(filename, test_cases, time_out, settings, source_json):
    results = {}
    outputs = []
    times = []
    if test_cases:
        for test in test_cases:
            if 'compile' in settings:
                file_create(source_json)
                p = subprocess.Popen(settings['compile'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                results['compiler-stderr'] = str(p.stderr.read())
                if not os.path.exists(settings['CompiledFile']):
                    results['ERROR'] = COMPILATION_ERROR
                    break

            p = subprocess.Popen(settings['run'], shell=True,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
            try:
                usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
                output = str(p.communicate(input=bytearray(test, 'utf-8'), timeout=time_out)[0])
                usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
                cpu_time = usage_end.ru_utime - usage_start.ru_utime
                times.append(cpu_time)
                outputs.append(output)
            except subprocess.TimeoutExpired:
                results['ERROR'] = TIMEOUT_ERROR
    else: # run no input scenario
        if 'compile' in settings:
            file_create(source_json)
            p = subprocess.Popen(settings['compile'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            results['compiler-stderr'] = str(p.stderr.read())
            if not os.path.exists(filename + '.exe'):
                results['ERROR'] = COMPILATION_ERROR
            else:
                p = subprocess.Popen(settings['run'], shell=True,
                                     stdout=subprocess.PIPE)
                try:
                    usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
                    output = str(p.communicate(timeout=time_out)[0])
                    usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
                    cpu_time = usage_end.ru_utime - usage_start.ru_utime
                    times.append(cpu_time)
                    outputs.append(output)
                except subprocess.TimeoutExpired:
                    results['ERROR'] = TIMEOUT_ERROR

    results['outputs'] = outputs
    results['times'] = times   

    return results

def run_cpp(filename, test_cases,time_out, source_json):
    settings = {}
    settings['compile'] = 'g++ %s -o %s' % (filename + '.cpp', filename + '.exe')
    settings['CompiledFile'] = filename + '.exe'
    settings['run'] = './%s' % (filename + '.exe')

    return run(filename, test_cases, time_out, settings, source_json)
    

def get_java_name(s):
    pclass = "(public(\s+)class(\s+))[A-Za-z0-9_]+"
    z = re.search(pclass, s)

    return z.group(0).split()[2]

def run_java(filename, test_cases, time_out, source_json):
    settings = {}
    settings['compile'] = 'javac %s' % (filename + '.java')
    settings['CompiledFile'] = filename + '.class'
    settings['run'] = 'java %s' % (filename)

    return run(filename, test_cases, time_out, settings, source_json)
    
                
def load_code(source_json, test_cases, time_out):
    language = source_json['language'].lower()
    filename = file_create(source_json)
    file_create(source_json)

    if language == 'c++':
        result = run_cpp(filename, test_cases, time_out, source_json)
        os.system('rm -rf temp')
    elif language == 'java':
        result = run_java(filename, test_cases, time_out, source_json)
        os.system('rm -rf temp')

    return result
            
def grade_submission(submission, solution, question):
    test_cases = question['test-cases']
    time_out = question['time-out']
    result = {}
    submission_results = load_code(submission, test_cases, time_out)
    expected_results = load_code(solution, test_cases, time_out)
    expecteds = expected_results['outputs']
    outputs = submission_results['outputs']
    result['compiler-stderr'] = submission_results['compiler-stderr']
    grades = []
    result['test-cases'] = {'__default__': {}}

    if 'ERROR' in submission_results:
        if submission_results['ERROR'] == COMPILATION_ERROR:
            result['verdict'] = 'Compilation failure'
        elif submission_results['ERROR'] == TIMEOUT_ERROR:
            result['verdict'] = 'Timed out'
            result['grades'] = grades

        return result

    print(submission_results)
    print(expected_results)
    for i, test_case in enumerate(question['test-cases']):
        result['test-cases'][test_case] = {}
        result['test-cases'][test_case]['time-taken'] = submission_results['times'][i]
        result['test-cases'][test_case]['output'] = submission_results['outputs'][i]
        result['test-cases'][test_case]['expected'] = expected_results['outputs'][i]
        
    if not question['test-cases']:
        result['test-cases']['__default__']['time-taken'] = submission_results['times'][0]
        result['test-cases']['__default__']['output'] = submission_results['outputs'][0]
        result['test-cases']['__default__']['expected'] = expected_results['outputs'][0]
        
    grades = []
    for output, expected in zip(outputs, expecteds): # if compiled go through list
        if output[2] == expected[2]:
            grades.append('pass') # this test case passed
        else:
            grades.append('fail') # this test case failed
            
    result['verdict'] = 'fail' if 'fail' in grades else 'pass'
    result['grades'] = grades

    return result

if __name__ == '__main__':
    set_urls(url_root=local_url)
    #set_urls(url_root=remote_url)
    print(process_submissions())
