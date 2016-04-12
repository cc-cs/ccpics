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
        else:
            submission = submission['submission']
        
        question = get_resource(urls['question_url'], [submission['question-id']])
        if 'error' in question:
            return question
        else:
            question = question['question']

        solution = get_resource(urls['solution_url'], [submission['question-id'], submission['language']])
        if 'error' in solution:
            return solution
        else:
            solution = solution['solution']
        
        test_results = grade_submission(submission=submission, solution=solution, question=question)
        #verdict = 'fail' if 'fail' in test_results else 'pass'
        result = {'user-id': submission['user-id'],
                  'submission-id': submission['id'],
                  'question-id': question['id'],
                  'test-results': test_results,
                  'verdict': test_results['verdict'],
                  'test-cases': test_results['test-cases'],
                  'outputs': test_results['outputs'],
                  'expecteds': test_results['expecteds'],
                  }
        
        result_submission_responses.append(submit_result(data=result))

    return result_submission_responses        

TIMEOUT_ERROR = 'TO'
COMPILATION_ERROR = 'CE'

def run_cpp(filename, test_cases,time_out):
    subprocess.Popen('g++ %s -o %s' % (filename + '.cpp', filename + '.exe'), shell=True, stdout=subprocess.PIPE).stdout.read()
    results = {}
    outputs = []
    times = []
    # run test cases scenario (input)
    if test_cases:
        for test in test_cases:
            if not os.path.exists(filename + '.exe'):
                results['ERROR'] = COMPILATION_ERROR
                #outputs.append(("CE", "TO", ''))
                break
            else:
                p = subprocess.Popen('./%s' % (filename + '.exe'), shell=True,
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
                    #outputs.append(("", "TO", ''))
    # run no input scenario
    else:
        if not os.path.exists(filename + '.exe'):
            results['ERROR'] = COMPILATION_ERROR
            #outputs.append(("CE", "TO", ''))
        else:
            p = subprocess.Popen('./%s' % (filename + '.exe'), shell=True,
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
                #outputs.append(("", "TO", ''))
    results['outputs'] = outputs
    results['times'] = times   
    return results

def get_java_name(s):
    pclass = "(public(\s+)class(\s+))[A-Za-z0-9_]+"
    z = re.search(pclass, s)
    return z.group(0).split()[2]

def run_java(filename, test_cases, time_out):
    subprocess.Popen('javac %s' % (filename + '.java'), shell=True, stdout=subprocess.PIPE).stdout.read()
    outputs = []
    times = []
    results = {}
    if test_cases:
        for test in test_cases:
            if not os.path.exists(filename + '.class'):
                results['ERROR'] = COMPILATION_ERROR
                outputs.append(("CE", "TO", ''))
                break
            else:
                try:
                    p = subprocess.Popen('java %s' % (filename), shell=True,
                                         stdout=subprocess.PIPE,
                                         stdin=subprocess.PIPE)
                    usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
                    output = p.communicate(input=bytearray(test, 'utf-8'), timeout=time_out)[0]
                    usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
                    cpu_time = usage_end.ru_utime - usage_start.ru_utime
                    times.append(cpu_time)
                    outputs.append(output)
                except subprocess.TimeoutExpired:
                    results['ERROR'] = TIMEOUT_ERROR
                    #outputs.append(("", "TO", ''))
    # run no input scenario
    else:
        if not os.path.exists(filename + '.class'):
            results['ERROR'] = COMPILATION_ERROR
            outputs.append(("CE", "Timed-out", ''))
        else:
            try:
                p = subprocess.Popen('java %s' % (filename), shell=True,
                                     stdout=subprocess.PIPE,
                                     stdin=subprocess.PIPE)
                usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
                output = p.communicate(timeout=time_out)[0]
                usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
                cpu_time = usage_end.ru_utime - usage_start.ru_utime
                times.append(cpu_time)
                outputs.append(output)
            except subprocess.TimeoutExpired:
                results['ERROR'] = TIMEOUT_ERROR
                #outputs.append(("", "", ''))
    results['outputs'] = outputs
    results['times'] = times
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
    result = {}
    submission_results = load_code(submission, test_cases, time_out)
    expected_results = load_code(solution, test_cases, time_out)
    expecteds = expected_results['outputs']
    outputs = submission_results['outputs']
    result['outputs'] = outputs
    result['times'] = submission_results['times']
    result['expecteds'] = expecteds
    result['test-cases'] = question['test-cases']
    grades = []
    # if outputs == 'Unsupported Language':
    #     return outputs
    # if outputs[0][0] == 'CE': # will be true if program didn't compile
    #     result['verdict'] = 'Compilation Error'
    #     result['grades'] = grades
    #     return result
    if 'ERROR' in submission_results:
        if submission_results['ERROR'] == COMPILATION_ERROR:
            result['verdict'] = 'Compilation Error'
        elif submission_results['ERROR'] == TIMEOUT_ERROR:
            result['verdict'] = 'Time-out'
        result['grades'] = grades
        return result
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
