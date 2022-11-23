
import sys

from dotenv import dotenv_values
from flask import Flask
from jinja2 import Environment, PackageLoader

cfg = dotenv_values(".env")

import data

imports = Flask(__name__)
application = imports
env = Environment(loader=PackageLoader('imports', 'pages'))


@imports.route(f"/{cfg['WWW']}")
def list_imports():
    main = env.get_template('imports.html')
    context = data.build('imports')
    return main.render(**context)


if __name__ == '__main__':
    imports.run()

