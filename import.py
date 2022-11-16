
import argparse
import datetime as dt
import os
import re
import time
import traceback

import sqlalchemy as sa
from sqlalchemy import create_engine

parser = argparse.ArgumentParser()
parser.add_argument('--include', type=str, help='Include files that match this pattern.')
parser.add_argument('--skip', type=str, help='Skip files that include this pattern.')
parser.add_argument('--increment', type=int, default=10000, help='Data frame building increment, default 10000')
args = parser.parse_args()

table_columns_data = None


def table_columns():

    tables = dict()

    with open("tableCols.txt") as f:
        for line in f:
            parts = line.strip().split(' ')
            if len(parts) == 1:
                tname = parts[0]
                tables[tname] = dict()
            if len(parts) > 1:
                cname = parts[0]
                cdef = ' '.join(parts[1:])
                tables[tname][cname] = cdef

    f.close()

    tables.pop('')

    for table in tables:
        tables[table].pop('pk')

    return tables


cols = table_columns()


col_types = {
    'int': sa.INTEGER,
    'varchar': sa.String,
    'char': sa.String,
    'date': sa.DATETIME,
    'datetime': sa.DATETIME}


def create_col_type(col_type):

    # could be 'int' or 'int NOT NULL'
    if col_type.startswith('int'):
        return col_types['int']
    if col_type.startswith('date'):
        return col_types['date']
    if col_type.startswith('datetime'):
        return col_types['datetime']

    # will be like 'decimal(10,2)
    if col_type.startswith('decimal'):
        return sa.DECIMAL()

    # will be like 'varchar(63)'
    if col_type.startswith('varchar'):
        length = int(col_type.split('(')[1].replace(')',''))
        return sa.VARCHAR(length=length)

    # will be like 'char(9)'
    if col_type.startswith('char'):
        length = int(col_type.split('(')[1].replace(')',''))
        return sa.CHAR(length=length)

    raise Exception(f"Unregnized type fo column: {col_type}")


def create_table(engine, table_name, head):

    meta = sa.MetaData()
    table = sa.Table(table_name, meta)
    for col_head in head:
        col_type = cols[table_name][col_head]
        if col_type.endswith('primary key'):
            # TODO the primary_key parameter in the Column() call is not creating a pk. why?
            table.append_column(sa.Column(col_head, create_col_type(col_type), primary_key=True))
        else:
            table.append_column(sa.Column(col_head, create_col_type(col_type)))

    meta.create_all(engine)

    return table


def as_dict(keys, values):

    klen = len(keys)
    vlen = len(values)
    if klen > vlen:
        max = klen
    else:
        max = vlen

    buf = '{\n'
    for idx in range(max):
        if idx < klen and idx < vlen:
            buf = f"{buf}    {idx} {keys[idx]}: |{values[idx]}|\n"
        if klen > idx >= vlen:
            buf = f"{buf}    {idx} {keys[idx]}: MISSING\n"
        if klen <= idx < vlen:
            buf = f"{buf}    {idx} MISSING: |{values[idx]}|\n"
    buf = buf + '}\n'
    return buf


def data_dir():
    d = sorted([dir for dir in os.listdir("data/") if dir.startswith('data_')])[-1]
    return f"data/{d}/DATA"


def fix_empty_naml(targeted, target, line_parts, idx):
    if target == targeted:
        if len(line_parts) == (len(cols[target]) + 1):
            if line_parts[idx].strip(' ') == '' and line_parts[idx+1] != '':
                line_parts.pop(idx)


def check_types(target, line_parts):

    errs = 0

    for idx in range(len(line_parts)):

        col_type = list(cols[target].values())[idx]
        if line_parts[idx] is None:
            continue

        value = line_parts[idx].strip()

        if col_type == 'date':
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                print(f"error for value: \"{value}\" of type {col_type}")
                errs += 1

        if col_type.startswith('varchar'):
            max_len = int(col_type.replace('varchar(','').replace(')',''))
            if len(value) > max_len:
                print(f"error for value: \"{value}\" of type {col_type}")
                errs += 1

        if col_type == 'int':
            if not re.match(r'^[\-]?\d*$', value):
                print(f"error for value: \"{value}\" of type {col_type}")
                errs += 1

        if col_type == 'decimal':
            parts = value.split('.')
            if len(parts) != 2 or not re.match(r'^\d*$', parts[0]) or not re.match(r'^\d*$', parts[1]):
                print(f"error for value: \"{value}\" of type {col_type}")
                errs += 1

    return errs


def fix_parts(target, head, parts):

    if target == 'cvr2_registration':
        if len(parts) == (len(cols[target]) + 1):
            if parts[7] == '' and re.match(r'^[CLE]?\d\d*$', parts[8]):
                parts.pop(7)

    if target == 'cvr_registration':
        if len(parts) == (len(cols[target]) + 1):
            # data found on 2022-11-16 rrk
            if parts[0] == '1719434' and parts[1] == '0':
                parts.pop(38)
            if parts[0] == '2329423' and parts[1] == '0':
                parts.pop(38)

    # why is memo_code set to length 1 and memo_refno set to length 2?
    # if target == 'debt':
    #     if parts[29].startswith('PAY') and parts[28] == '':
    #         parts.pop(28)
    #         parts.append('')

    # these all target missing NAML values when this got pushed up.
    #
    fix_empty_naml('cvr_campaign_disclosure', target, parts, 6)
    fix_empty_naml('cvr_campaign_disclosure', target, parts, 26)
    fix_empty_naml('cvr_campaign_disclosure', target, parts, 61)
    fix_empty_naml('cvr_e530', target, parts, 5)
    fix_empty_naml('cvr_e530', target, parts, 16)
    fix_empty_naml('cvr_lobby_disclosure', target, parts, 7)
    fix_empty_naml('cvr_lobby_disclosure', target, parts, 28)
    fix_empty_naml('cvr_lobby_disclosure', target, parts, 32)
    fix_empty_naml('cvr_lobby_disclosure', target, parts, 46)
    fix_empty_naml('cvr_registration', target, parts, 7)
    fix_empty_naml('cvr_registration', target, parts, 29)
    fix_empty_naml('cvr_registration', target, parts, 33)
    fix_empty_naml('cvr_so', target, parts, 6)
    fix_empty_naml('cvr_so', target, parts, 26)
    fix_empty_naml('cvr2_campaign_disclosure', target, parts, 13)
    fix_empty_naml('cvr2_campaign_disclosure', target, parts, 23)
    fix_empty_naml('cvr2_lobby_disclosure', target, parts, 4)
    fix_empty_naml('cvr2_registration', target, parts, 8)
    fix_empty_naml('cvr2_so', target, parts, 7)
    fix_empty_naml('cvr3_verification_info', target, parts, 9)
    fix_empty_naml('debt', target, parts, 7)
    fix_empty_naml('debt', target, parts, 21)
    fix_empty_naml('expn', target, parts, 7)
    fix_empty_naml('expn', target, parts, 21)
    fix_empty_naml('expn', target, parts, 26)
    fix_empty_naml('expn', target, parts, 33)
    fix_empty_naml('f501_502', target, parts, 13)
    fix_empty_naml('f501_502', target, parts, 26)
    fix_empty_naml('filername', target, parts, 5)
    fix_empty_naml('latt', target, parts, 7)
    fix_empty_naml('lccm', target, parts, 7)
    fix_empty_naml('lccm', target, parts, 15)
    fix_empty_naml('lemp', target, parts, 6)
    fix_empty_naml('lexp', target, parts, 8)
    fix_empty_naml('loan', target, parts, 8)
    fix_empty_naml('loan', target, parts, 26)
    fix_empty_naml('loan', target, parts, 33)
    fix_empty_naml('lobby_amendments', target, parts, 9)
    fix_empty_naml('lobby_amendments', target, parts, 15)
    fix_empty_naml('lobby_amendments', target, parts, 21)
    fix_empty_naml('lobby_amendments', target, parts, 27)
    fix_empty_naml('loth', target, parts, 11)
    fix_empty_naml('lpay', target, parts, 7)
    fix_empty_naml('names', target, parts, 1)
    fix_empty_naml('names', target, parts, 9)
    fix_empty_naml('rcpt', target, parts, 7)
    fix_empty_naml('rcpt', target, parts, 25)
    fix_empty_naml('rcpt', target, parts, 32)
    fix_empty_naml('rcpt', target, parts, 42)
    fix_empty_naml('s401', target, parts, 6)
    fix_empty_naml('s401', target, parts, 10)
    fix_empty_naml('s401', target, parts, 20)
    fix_empty_naml('s497', target, parts, 7)
    fix_empty_naml('s497', target, parts, 22)
    fix_empty_naml('s498', target, parts, 8)
    fix_empty_naml('s498', target, parts, 17)


    if len(parts) != len(cols[target]):
        return None
        # raise Exception(f"target: {target}, incorrect # columns")

    for idx in range(len(head)):
        col_name = head[idx]
        col_type = cols[target][col_name]
        col_value = parts[idx]

        if col_type in ['date', 'datetime']:
            if col_value != '':
                m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4}).*$', col_value)
                if m:
                    month, day, year = m.groups()
                    col_value = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    parts[idx] = col_value

        if col_value == '':
            parts[idx] = None

    return parts


def import_data():

    engine = create_engine("mysql+pymysql://ray:alexna11@localhost/calaccess")

    conn = engine.connect()

    row = conn.execute("select max(pk) as pk from file_imports;").fetchone()

    if row['pk'] is None:
        import_pk = 1
    else:
        import_pk = int(row['pk']) + 1

    now = int(time.time())

    for file in os.listdir(data_dir()):

        if not re.match(r".*_CD.TSV", file):
            continue

        if args.include is not None:
            if args.include not in file:
                continue

        if args.skip is not None:
            if re.match(args.skip, file):
                continue

        print(f"\nfile: {file}")

        target = file.replace('_CD.TSV', '').lower()
        print(f"target: {target}")

        engine.execute(f"DROP TABLE IF EXISTS {target};")

        engine.execute(f"""
            insert into file_imports values (
                 {import_pk},
                 '{data_dir()}/{file}',
                 0, 0,
                 from_unixtime({now}));""")

        lines_read = 0
        head = None

        try:
            # if we read as 'r', then lines with '\r\r\n' come out as 2 lines.
            data_file = open(f"{data_dir()}/{file}", 'rb')
            data_lines = list()
            errors = 0

            for line in data_file:

                # there are lines that end in, for instance, '\r\r\n'.
                line_parts = line.decode(encoding='utf-8').strip('\n').strip('\r').split('\t')

                if line.decode(encoding='utf-8').startswith('2203954\t2\t11\tCVR2\tF603'):
                    pass

                if head is None:
                    head = line_parts
                    lhead = [x.lower() for x in head]
                    table = create_table(engine, target, lhead)
                    lines_read += 1
                    continue

                line_parts = fix_parts(target, lhead, line_parts)

                if line_parts is None:
                    print(f"ERROR: {lines_read}")
                    print(as_dict(head, line.decode(encoding='utf-8').strip('\n').strip('\r').split('\t')))
                    errors += 1
                    continue

                line_errors = check_types(target, line_parts)

                if line_errors > 0:
                    errors += line_errors
                    print(f"ERROR: {lines_read}")
                    print(as_dict(head, line_parts))

                else:
                    data_dict = dict(zip(lhead, line_parts))
                    data_lines.append(data_dict)
                    if len(data_lines) >= args.increment:
                        print(f"now: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        conn.execute(sa.insert(table, data_lines))
                        data_lines.clear()

                lines_read += 1

            # handle rows left-over from the last incremenr
            if len(data_lines) > 0:
                conn.execute(sa.insert(table, data_lines))
                data_lines.clear()

        except:
            print("EXCEPTION df:")
            traceback.print_exc()

        finally:
            engine.execute(f"""
                update file_imports
                set num_read = {lines_read}, error_count = {errors}
                where pk = {import_pk};""")

            import_pk += 1

    # to be done after:
    #    sql_engine.execute(f"ALTER TABLE {target} ADD COLUMN pk INT FIRST;")
    #    sql_engine.execute(f"UPDATE {target} CROSS JOIN (SELECT @pk:=0) AS init SET {target}.pk=@pk:=@pk+1;")
    #    sql_engine.execute(f"ALTER TABLE {target} ADD PRIMARY KEY (pk);")


if __name__ == '__main__':
    import_data()