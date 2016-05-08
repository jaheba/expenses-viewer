import os
import sys
import tempfile

import flask
from flask import render_template, request

from lxml import etree

from parser import parse, set_status
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
    return render_template('expense.html', expenses=load(), submit="submit")

@app.route('/reimburse')
def reimburse():
    return render_template('expense.html', expenses=load(), submit="reimburse")

@app.route('/accounting')
def accounting():
    return render_template('expense.html', expenses=load(), submit="accounting")


@app.route('/new')
def new():
    return render_template('new.html')

@app.route('/submit', methods=['POST'])
def submit_post():
    set_status(sys.argv[1], request.json, 'submitted')
    return 'ok'


@app.route('/reimburse', methods=['POST'])
def reimburse_post():
    set_status(sys.argv[1], request.json, 'reimbursed')
    return 'ok'

@app.route('/accounting', methods=['POST'])
def accounting_post():
    set_status(sys.argv[1], request.json, 'accounted')
    return 'ok'

@app.route('/new', methods=["POST"])
def new_post():
    node = etree.Element("expense")
    etree.SubElement(node, "desc").text = request.json['description']
    fields = 'paidby', 'buget', 'date', 'gbp', 'for'
    for item in request.json['items']:
        sub = etree.SubElement(node, item['type'])
        for field in fields:
            if item.get(field):
                sub.set(field, item.get(field))

    return etree.tostring(node, pretty_print=True)


def main():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    global json_file

    with tempfile.NamedTemporaryFile() as fobj:
        json_file = fobj
        app.run()

if __name__ == '__main__':
    main()