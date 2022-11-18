
import sys

from flask import Flask
from jinja2 import Environment, PackageLoader

# sys.path.append("/home/ray/opinions/")
import data

imports = Flask(__name__)
application = imports
env = Environment(loader=PackageLoader('imports', 'pages'))


@imports.route('/imports')
def list_imports():
    main = env.get_template('imports.html')
    context = data.build('imports')
    return main.render(**context)


if __name__ == '__main__':
    imports.run()

