
import sys

from flask import Flask
from jinja2 import Environment, PackageLoader

from dotenv import dotenv_values

cfg = dotenv_values(".env")

sys.path.append(f"{cfg['APP_HOME']}")
import data

imports = Flask(__name__)
application = imports
env = Environment(loader=PackageLoader('imports', 'pages'))


@imports.route('/')
def list_imports():
    main = env.get_template('imports.html')
    context = data.build('imports')
    return main.render(**context)


if __name__ == '__main__':
    imports.run()

