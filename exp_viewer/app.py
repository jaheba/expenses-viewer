import sys
import tempfile

import flask
from flask import render_template

from parser import parse
import json

app = flask.Flask(__name__)
json_path = None

def load():
    with open(json_path) as fobj:
        return json.load(fobj)

@app.route('/')
def index():
    return render_template('expense.html', expenses=load())

@app.route('/new')
def new():
    return render_template('new.html')


def main():
    global json_path
    path = sys.argv[1]
    expenses = parse(path)
    data = list(reversed([exp.to_json() for exp in expenses.expenses]))

    with tempfile.NamedTemporaryFile() as fobj:
        json_path = fobj.name
        json.dump(data, fobj)
        fobj.flush()
        app.run()

if __name__ == '__main__':
    main()