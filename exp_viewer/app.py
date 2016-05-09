import os
import sys
import tempfile

import flask
from flask import render_template, request

from lxml import etree

from parser import parse, set_status, item_requirements
import json

app = flask.Flask(__name__)
json_file = None
expenses_path = None
version = 0
CACHING = False

def get_expenses():
    expenses = parse(expenses_path)
    return list(reversed([exp.to_json(i) for i, exp in enumerate(expenses.expenses)]))

def load():
    if not CACHING:
        return get_expenses()

    global version
    time = os.path.getmtime(expenses_path)
    if CACHING and time != version:
        version = time
        data = get_expenses()
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
    set_status(expenses_path, request.json, 'submitted')
    return 'ok'


@app.route('/reimburse', methods=['POST'])
def reimburse_post():
    set_status(expenses_path, request.json, 'reimbursed')
    return 'ok'

@app.route('/accounting', methods=['POST'])
def accounting_post():
    set_status(expenses_path, request.json, 'accounted')
    return 'ok'

@app.route('/new', methods=["POST"])
def new_post():
    node = etree.Element("expense")
    etree.SubElement(node, "desc").text = request.json['description']
    fields = 'paidby', 'buget', 'date', 'gbp', 'for'
    _cache = None

    for item in request.json['items']:
        sub = etree.SubElement(node, item['type'])
        for field in fields:
            if field in item:
                sub.set(field, item.get(field))
        if not sub.get('for'):
            if _cache is None:
                _cache = parse(expenses_path)
            sub.set('for', _cache.people[item['paidby']].name)

        if item['type'] in item_requirements:
            sub.set(item_requirements[item['type']], item['description'])
        else:
            sub.text = item['description']

        if item['alt']['amount']:
            sub.set(item['alt']['cur'], item['alt']['amount'])





    return etree.tostring(node, pretty_print=True)


def make_app(expenses):
    global expenses_path
    expenses_path = expenses

def run(debug=True):
    # import logging
    # log = logging.getLogger('werkzeug')
    # log.setLevel(logging.ERROR)
    global json_file

    with tempfile.NamedTemporaryFile() as fobj:
        json_file = fobj
        app.run(debug=debug)

def main():
    make_app(sys.argv[1])
    run()

if __name__ == '__main__':
    main()