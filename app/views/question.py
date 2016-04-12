from flask import flash, json, redirect, request, render_template, url_for

from .. import app
from ..services import question_service

@app.route('/questions')
def render_questions():
    questions = question_service.fetch_questions()['questions']
    return render_template('questions.djhtml', questions=questions)

@app.route('/questions/<question_id>', methods=['GET'])
def render_question(question_id):
    question = question_service.fetch_question(question_id=question_id)['question']
    return render_template('question.djhtml', question=question)
    
