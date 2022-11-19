
import sys

from sqlalchemy import create_engine, inspect

sys.path.append('..')
import common

engine = create_engine('mysql+pymysql://ray:alexna11@localhost/calaccess')
conn = engine.connect()
inspector = inspect(engine)


def build(param):

    context = dict()

    if param == 'imports':

        sql = """
        select
        f1.last_mod, f1.num_lines, f1.target, f2.num_read, f2.error_count, f2.import_dt, f2.filename 
        from files f1, file_imports f2 
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
        for imported in imports:

            dd = imported['filename'].split('/')[1][5:]
            data_date = f"{dd[0:4]}-{dd[5:7]}-{dd[6:8]}"
            imported['data_date'] = data_date

            target = imported['target']
            if target not in next_imports:
                next_imports[target] = imported
            else:
                if imported['import_dt'] > next_imports[target]['import_dt']:
                    next_imports[target] = imported

        context['imports'] = common.order_dicts_by_key(list(next_imports.values()), 'target')

        return context
