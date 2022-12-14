
import sys

import data
from dotenv import dotenv_values
from flask import Flask
from jinja2 import Environment, PackageLoader

cfg = dotenv_values(".env")

calaccess = Flask(__name__)
application = calaccess
env = Environment(loader=PackageLoader('calaccess', 'pages'))


@calaccess.route(f"/{cfg['WWW']}")
def contracts_front():
    main = env.get_template('calaccess.html')
    context = data.calacess_front()
    return main.render(**context)


@calaccess.route(f"/{cfg['WWW']}<filing_date_low>/<filing_date_hi>")
def contracts_front_dates(filing_date_low, filing_date_hi):
    main = env.get_template('calaccess.html')
    context = data.calacess_front(filing_date_low, filing_date_hi)
    return main.render(**context)


@calaccess.route(f"/{cfg['WWW']}filingdate/<filing_date>")
def contracts_filingdate(filing_date):
    main = env.get_template('calaccess_filings.html')
    context = data.calaccess_filing_date(filing_date)
    return main.render(**context)


@calaccess.route(f"/{cfg['WWW']}filingdate/<filing_date>/<form_id>")
def contracts_filingdate_form_id(filing_date, form_id):
    main = env.get_template('calaccess_filings.html')
    context = data.calaccess_filing_date(filing_date, form_id=form_id)
    return main.render(**context)


@calaccess.route(f"/{cfg['WWW']}filingdates/<filing_date_1>/<filing_date_2>")
def contracts_filingdates(filing_date_1, filing_date_2):
    main = env.get_template('calaccess_filings.html')
    context = data.calaccess_filing_date(filing_date_1, filing_date_2)
    return main.render(**context)


@calaccess.route(f"/{cfg['WWW']}filingdates/<filing_date_1>/<filing_date_2>/<form_id>")
def contracts_filingdates_form_id(filing_date_1, filing_date_2, form_id):
    main = env.get_template('calaccess_filings.html')
    context = data.calaccess_filing_date(filing_date_1, filing_date_2, form_id)
    return main.render(**context)


@calaccess.route(f"/{cfg['WWW']}filing_raw/<filing_id>")
def contracts_filing_raw(filing_id):
    main = env.get_template('calaccess_filing_raw.html')
    context = data.filing_raw(filing_id)
    return main.render(**context)


@calaccess.route(f"/{cfg['WWW']}filer_raw/<filer_id>")
def contracts_filer_raw(filer_id):
    main = env.get_template('calaccess_filer_raw.html')
    context = data.filer_raw(filer_id)
    return main.render(**context)


if __name__ == '__main__':
    calaccess.run()
