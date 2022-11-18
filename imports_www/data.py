
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
#
#    if param == 'files' and args['prefix'] is None and args['file'] is None:
#
#        # only list the data prefixes
#        sql = """
#        select filename from files;
#        """
#        rows = conn.execute(sql).fetchall()
#        files = dict()
#        for row in rows:
#            prefix = row['filename'][:13]
#            if prefix not in files:
#                files[prefix] = 1
#            else:
#                files[prefix] = files[prefix] + 1
#        print(f"files: {files}")
#
#        next_files = list()
#        for key in files:
#            row = {
#                'filename': key,
#                'count': files[key]
#            }
#            next_files.append(row)
#        print(f"next_files: {next_files}")
#
#        context['prefixes'] = next_files
#        return context
#
#    if param == 'files' and args['prefix'] is not None:
#
#        sql = """
#        select * from files where filename like '%%__PREFIX__%%';
#        """
#        sql = sql.replace('__PREFIX__', args['prefix'])
#
#        rows = conn.execute(sql).fetchall()
#
#        files = dict()
#        for row in rows:
#            file_leaf = row['filename'].split('/')[-1]
#            row_entry = {
#                'filename': file_leaf,
#                'prefix': row['filename'].split('/')[0],
#                'num_lines': row['num_lines']
#            }
#            files[file_leaf] = row_entry
#
#        next_files = list()
#
#        for key in sorted(list(files.keys())):
#            next_files.append(files[key])
#
#        context['files'] = next_files
#        return context
#
#    if param == 'files' and args['file'] is not None:
#
#        bad_lines = list()
#
#        prefix = '_'.join(args['file'].split('_')[0:1])
#        filename = '_'.join(args['file'].split('_')[2:])
#
#        sql = """
#        select * from files where filename like '%%/__FILE__' and filename like '__PREFIX__%%';
#        """
#        sql = sql.replace('__FILE__', filename)
#        sql = sql.replace('__PREFIX__', prefix)
#
#        file_info = dict(conn.execute(sql).fetchone())
#
#        fn = file_info['filename']
#
#        head_result = subprocess.run(["/usr/bin/head", "-1", f"data/{fn}"], capture_output=True)
#        columns = head_result.stdout.decode(encoding='utf-8')
#        columns = ' '.join(columns.split('\t'))
#        file_info['columns'] = columns
#
#        file_info['columns_count'] = len(columns.split(' '))
#
#        fields_result = subprocess.run(["/usr/bin/bash", "field_counts.sh", f"data/{fn}"], capture_output=True)
#        file_info['fields_count'] = fields_result.stdout.decode(encoding='utf-8')
#
#        df = pd.read_csv(f"data/{fn}", sep='\t', on_bad_lines=bad_line_finder, engine='python')
#
#        buffer = io.StringIO()
#        df.info(buf=buffer)
#        str_summary = buffer.getvalue()
#
#        file_info['pd'] = str_summary
#
#        file_info['bad_lines_count'] = len(bad_lines)
#
#        if len(bad_lines) == 0:
#            file_info['bad_lines'] = None
#        else:
#            bad_lines_list = "\n".join(bad_lines)
#            bad_lines_list = str(columns.split(' ')) + '\n' + bad_lines_list
#
#            file_info['bad_lines'] = bad_lines_list
#
#        context['file'] = file_info
#        return context
#
#    raise Exception("what happened?")
#
#
