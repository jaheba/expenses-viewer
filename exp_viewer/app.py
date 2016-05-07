import os
import sys
import tempfile

import flask
from flask import render_template, request

from parser import parse, set_submitted
import json

app = flask.Flask(__name__)
json_file = None

version = 0

def load():
    global version
    time = os.path.getmtime(sys.argv[1])
    if time != version:
        version = time

        expenses = parse(sys.argv[1])
        data = list(reversed([exp.to_json(i) for i, exp in enumerate(expenses.expenses)]))
        json_file.seek(0)
        json.dump(data, json_file)
        json_file.flush()

        return data

    with open(json_file.name) as fobj:
        return json.load(fobj)

@app.route('/')
def index():
    return render_template('expense.html', expenses=load(), submit="false")

@app.route('/submit')
def submit():
    return render_template('expense.html', expenses=load(), submit="true")

@app.route('/new')
def new():
    return render_template('new.html')

@app.route('/submit', methods=['POST'])
def submit_post():
    set_submitted(sys.argv[1], request.json)
    return 'ok'


def main():
    global json_file

    with tempfile.NamedTemporaryFile() as fobj:
        json_file = fobj
        app.run()

if __name__ == '__main__':
    main()