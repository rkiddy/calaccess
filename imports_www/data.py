
import sys

from dotenv import dotenv_values
from sqlalchemy import create_engine, inspect

cfg = dotenv_values(".env")

sys.path.append(f"{cfg['APP_HOME']}")
import common

engine = create_engine(f"mysql+pymysql://ray:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
conn = engine.connect()
inspector = inspect(engine)


def build(param):

    context = dict()

    if param == 'imports':

        sql = """
        select
        f1.last_mod, f1.num_lines, f1.target, f2.num_read, f2.error_count, f2.import_dt, f2.filename 
        from _files f1, _file_imports f2 
        where f1.filename = f2.filename;
        """

        rows = conn.execute(sql).fetchall()

        cols = {
            'last_mod': 0,
            'num_lines': 1,
            'target': 2,
            'num_read': 3,
            'error_count': 4,
            'import_dt': 5,
            'filename': 6
        }
        imports = common.fill_in_table(rows, cols)

        next_imports = dict()

        for imp in imports:

            dd = imp['filename'].split('/')[1][5:]
            data_date = f"{dd[0:4]}-{dd[5:7]}-{dd[6:8]}"
            imp['data_date'] = data_date

            if imp['num_lines'] == 0:
                imp['diff'] = 0
            else:
                imp['diff'] = (imp['num_lines'] - imp['num_read']) / imp['num_lines']
            imp['diff'] = int(imp['diff'] * 1000) / 1000

            target = imp['target']
            if target not in next_imports:
                next_imports[target] = imp
            else:
                if imp['import_dt'] > next_imports[target]['import_dt']:
                    next_imports[target] = imp

        context['imports'] = common.order_dicts_by_key(list(next_imports.values()), 'target')

        file_prefixes = list()

        sql = "select filename from _files where filename like '%%TSV'"

        for row in conn.execute(sql).fetchall():
            parts = row['filename'].split('/')
            file_prefixes.append(parts[1])

        context['import_dates'] = sorted(list(set(file_prefixes)))
        context['import_dates'].reverse()

        print(f"import_dates: {context['import_dates']}")

        return context
