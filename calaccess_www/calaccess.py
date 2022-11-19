
import sys

from flask import Flask
from jinja2 import Environment, PackageLoader

#sys.path.append('/home/ray/opencalaccess-data/calaccess_www')
sys.path.append('..')
import data

calaccess = Flask(__name__)
application = calaccess
env = Environment(loader=PackageLoader('calaccess', 'pages'))


@calaccess.route('/')
def contracts_front():
    main = env.get_template('calaccess.html')
    context = data.build('calaccess_front')
    return main.render(**context)


@calaccess.route('/filingdate/<param>')
def contracts_filingdate(param):
    main = env.get_template('calaccess_filingdate.html')
    context = data.build('calaccess_filingdate', param)
    return main.render(**context)


@calaccess.route('/filingdate/<param>/form_id/<param2>')
def contracts_filingdate_form_id(param, param2):
    main = env.get_template('calaccess_filingdate.html')
    context = data.build('calaccess_filingdate', param, 'form_id', param2)
    return main.render(**context)


@calaccess.route('/filing_raw/<param>')
def contracts_filing_raw(param):
    main = env.get_template('calaccess_filing_raw.html')
    context = data.build('calaccess_filing_raw', param)
    return main.render(**context)


@calaccess.route('/filer_raw/<param>')
def contracts_filer_raw(param):
    main = env.get_template('calaccess_filer_raw.html')
    context = data.build('calaccess_filer_raw', param)
    return main.render(**context)


if __name__ == '__main__':
    calaccess.run()
