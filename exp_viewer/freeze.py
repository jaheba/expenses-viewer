import sys
from flask_frozen import Freezer
import app
from flask import Flask, render_template

frozen_app = Flask(__name__)

@frozen_app.route('/')
def index():
    return render_template('expense.html', expenses=app.load(),
        read_only=True, submit="false")


freezer = Freezer(frozen_app)

if __name__ == '__main__':
    app.expenses_path = sys.argv[1]
    frozen_app.config['FREEZER_DESTINATION'] = '/Users/jbs/tmp/freeze'
    freezer.freeze()
    # frozen_app.run(debug=True)