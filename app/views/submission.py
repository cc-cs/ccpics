from flask import flash, json, redirect, request, render_template, url_for, session

from .. import app
from ..services import question_service
from ..services import submission_service

ALLOWED_EXTENSIONS = set(['cpp', 'java', 'txt'])

@app.route('/submission-upload/<question_id>')
def submission_upload(question_id):
    question = question_service.fetch_question(question_id=question_id)['question']
    return render_template('submission-upload.html', question=question)

@app.route('/submission-result', methods=['POST'])
def submission_result():
    error = None

    source_code = request.form['source-code']
    if not source_code:
        source_file = request.files['source-file']
        if source_file:
            file_extension = source_file.filename.rsplit('.', 1)[-1]
            if file_extension in ALLOWED_EXTENSIONS:
                source_code = source_file.read().decode()
            else:
                error = "Unsupported file extension: {}".format(file_extension)
        else:
            error = "Please provide source code for your submission."

    if not error:
        form_data = json.loads(json.dumps(request.form))
        form_data['source-code'] = source_code
        form_data['user-id'] = session['user_id']
        form_data.pop("submit", None)
        submission_request_response = submission_service.add_submission(submission_data=form_data)
        if 'error' in submission_request_response:
            error = submission_request_response['error']
        else:
            flash("Your submission has been saved!", "success")
            flash("Please check the submission page for update on the status.", "message")
            return redirect(url_for('render_submissions'))

    error = error if error else "Sorry, something went wrong. Please try again later."
    flash(error, 'error')

    return redirect(url_for('submission_upload', question_id=request.form['question-id']))

@app.route('/submissions')
def render_submissions():
    submissions = submission_service.fetch_submissions()['submissions']
    submissions = [submission for submission in submissions if submission['user-id'] == session['user_id']]
    return render_template('submissions.html', submissions=submissions)

@app.route('/submissions/<submission_id>', methods=['GET'])
def render_submission(submission_id):
    submission = submission_service.fetch_submission(submission_id=submission_id)['submission']
    return render_template('submission.html', submission=submission)
