import sys
from flask_frozen import Freezer
import app
from flask import Flask, render_template

frozen_app = Flask(__name__)

@frozen_app.route('/index.html.notemplate')
def index():
    return render_template('expense.html', expenses=app.load(),
        read_only=True, submit="false")


freezer = Freezer(frozen_app)

def freeze(expenses, destination):
    app.expenses_path = expenses
    frozen_app.config['FREEZER_DESTINATION'] = destination
    freezer.freeze()