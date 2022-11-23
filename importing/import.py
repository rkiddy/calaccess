
import argparse
import datetime as dt
import os
import re
import sys
import time
import traceback

import sqlalchemy as sa
from dotenv import dotenv_values
from p_tqdm import p_map
from sqlalchemy import create_engine

cfg = dotenv_values(".env")

sys.path.append(f"{cfg['APP_HOME']}")
import common

parser = argparse.ArgumentParser()
parser.add_argument('--include', type=str, nargs='*',
                    help='Include files that match this pattern.')
parser.add_argument('--skip', type=str, nargs='*',
                    help='Skip files that include this pattern.')
parser.add_argument('--increment', type=int, default=10000,
                    help='Data frame building increment, default 10000')
parser.add_argument('--run-checks', type=str, nargs='*',
                    help='Only check available: memo_refs')
parser.add_argument('--use-fixes', type=str, nargs='*',
                    help="Use file, from errors, where the errors are fixed.")
parser.add_argument('--include-after', action='store_true')
parser.add_argument('--only-after', action='store_true')
parser.add_argument('--include-olders', action='store_true')
parser.add_argument('--no-threads', action='store_true')

args = parser.parse_args()

table_columns_data = None


cols = common.table_columns()


def create_col_type(col_type):

    # could be 'int' or 'int NOT NULL'
    if col_type.startswith('int'):
        return sa.INTEGER
    if col_type.startswith('date'):
        return sa.DATETIME
    if col_type.startswith('datetime'):
        return sa.DATETIME

    # will be like 'decimal(10,2)
    if col_type.startswith('decimal'):
        return sa.DECIMAL()

    # will be like 'varchar(63)'
    if col_type.startswith('varchar'):
        length = int(col_type.split('(')[1].replace(')', ''))
        return sa.VARCHAR(length=length)

    # will be like 'char(9)'
    if col_type.startswith('char'):
        length = int(col_type.split('(')[1].replace(')', ''))
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
        local_max = klen
    else:
        local_max = vlen

    buf = '{\n'
    for idx in range(local_max):
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
            max_len = int(col_type.replace('varchar(', '').replace(')', ''))
            if len(value) > max_len:
                print(f"error for value: \"{value}\" of type {col_type}")
                errs += 1

        if col_type == 'int':
            if not re.match(r'^-?\d*$', value):
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
            if parts[7] == '' and re.match(r'^[CLE]?\d+$', parts[8]):
                parts.pop(7)

    if target == 'cvr_registration':
        if len(parts) == (len(cols[target]) + 1):
            # data found on 2022-11-16 rrk
            if parts[0] == '1719434' and parts[1] == '0':
                parts.pop(38)
            if parts[0] == '2329423' and parts[1] == '0':
                parts.pop(38)

    # this seems to get a variable number of tabs after, even when all the data is fine.
    # check the filing_id, trans_id, cum_ytd, cum_oth and then pop off empty fields.
    #
    if target == 'rcpt':
        if len(parts) > 63:
            if re.match (r'^\d+$', parts[20]):
                if re.match (r'^\d+$', parts[21]):
                    if re.match(r'^\d+$', parts[0]):
                        if re.match(r'^\d+$', parts[5]):
                            while len(parts) > 63 and parts[-1] == '':
                                parts.pop()

    # same thing here, variable number of tabs.
    #
    if target == 'cvr_campaign_disclosure':
        if len(parts) > 86:
            if parts[37] in ['Y', 'N']:
                if parts[38] in ['Y', 'N']:
                    if parts[39] in ['Y', 'N']:
                        if parts[40] in ['Y', 'N']:
                            while len(parts) > 86 and parts[-1] == '':
                                parts.pop()

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


def should_exclude(table):

    file = f"{table.upper()}_CD.TSV"

    if args.include is not None:
        for inc in args.include:
            if inc in file:
                return False

        return True

    if args.skip is not None:

        should = False

        for skip in args.skip:
            if re.match(skip, file):
                should = True

        return should

    return False


def add_index_for_columns_in_tables(conn, col_name):
    found_tables = common.tables_with_column(col_name)
    for table in found_tables:
        if should_exclude(table):
            continue
        if not common.index_exists_in_table(conn, table, col_name):
            print(f"adding index for '{col_name}' to {table}")
            conn.execute(f"alter table {table} add index({col_name})")


def afters():

    engine = create_engine(f"mysql+pymysql://ray:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")

    conn = engine.connect()

    add_index_for_columns_in_tables(conn, 'filing_id')
    add_index_for_columns_in_tables(conn, 'amend_id')
    add_index_for_columns_in_tables(conn, 'line_item')
    add_index_for_columns_in_tables(conn, 'filer_id')
    add_index_for_columns_in_tables(conn, 'rec_type')
    add_index_for_columns_in_tables(conn, 'form_type')
    add_index_for_columns_in_tables(conn, 'filing_date')


def check_memo_refs():

    engine = create_engine(f"mysql+pymysql://ray:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")

    conn = engine.connect()

    conn.execute("drop table if exists _memo_ref_nos")
    conn.execute("create table _memo_ref_nos (ref_no varchar(20))")
    conn.execute("alter table _memo_ref_nos add unique (ref_no)")

    for table in common.tables_with_column('memo_refno'):
        print(f"starting {table}...")
        sql = f"select distinct(memo_refno) as ref_no from {table}"
        for row in conn.execute(sql).fetchall():
            sql = f"insert ignore into _memo_ref_nos values('{row['ref_no']}')"
            conn.execute(sql)

    row = conn.execute("""
        select (
            select count(0) from text_memo t1 left outer join _memo_ref_nos m1
                on t1.ref_no = m1.ref_no
                where t1.ref_no is not NULL and
                    m1.ref_no is NULL) as missing,
            (
            select count(0) from _memo_ref_nos) as target;
        """).fetchone()

    print("memo_refno:")
    print(f"    missing: {row['missing']}")
    print(f"     target: {row['target']}")


def import_fixes(filenames):

    engine = create_engine(f"mysql+pymysql://ray:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
    conn = engine.connect()

    rows = dict()
    errors_seen = 0
    in_dict = False

    for filename in filenames:

        file = open(filename, 'r')
        for line in file:
            line = line.strip()
            parts = line.split(' ')

            if in_dict and len(parts) == 3 and re.match(r'^\d*', parts[0]):
                key = parts[1]
                value = parts[2].strip('|')
                rows[table_name][-1][key] = value

            if parts[0] == 'target:':
                table_name = parts[1]
                print(f"table_name: {table_name}")

            if parts[0] == '{':
                errors_seen += 1

            if parts[0] == '{' and parts[-1] == 'FIXED':
                in_dict = True
                if table_name not in rows:
                    rows[table_name] = list()
                    rows[table_name].append(dict())

            if line == '}':
                in_dict = False

    print(f"errors_seen: {errors_seen}")
    print(f"rows: {rows}")


def import_data(info):

    now = int(time.time())

    engine = create_engine(f"mysql+pymysql://ray:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
    conn = engine.connect()

    filename = info['file']
    import_pk = info['pk']

    target = filename.replace('_CD.TSV', '').lower()

    out_file = open(f"{data_dir()}/{target}_{import_pk}.txt", 'w')

    conn.execute(f"DROP TABLE IF EXISTS {target};")
    conn.execute(f"DROP TABLE IF EXISTS {target}_older;")

    conn.execute(f"""
        insert into _file_imports values (
             {import_pk},
             '{data_dir()}/{filename}',
             0, 0,
             from_unixtime({now}));""")

    lines_read = 0
    head = None

    last_parts = []

    try:
        # if we read as 'r', then lines with '\r\r\n' come out as 2 lines.
        data_file = open(f"{data_dir()}/{filename}", 'rb')
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

            # FILERNAME_CD.TSV has problems with broken lines. Like this:
            # ERROR: 1131228
            # {
            #     0 XREF_FILER_ID: |1449339|
            #     1 FILER_ID: |1449339|
            #     2 FILER_TYPE: |RECIPIENT COMMITTEE|
            #     3 STATUS: |ACTIVE|				        ERROR: 1131229
            #     4 EFFECT_DT: |07/15/2022|			        {
            #     5 NAML: |MARROCCO FOR TRUSTEE 2022; RENA|	    0 XREF_FILER_ID: ||
            #     6 NAMF: MISSING				                1 FILER_ID: ||
            #     7 NAMT: MISSING				                2 FILER_TYPE: ||
            #     8 NAMS: MISSING				                3 STATUS: ||
            #     9 ADR1: MISSING				                4 EFFECT_DT: ||
            #     10 ADR2: MISSING				                5 NAML: ||
            #     11 CITY: MISSING				                6 NAMF: |VISTA |
            #     12 ST: MISSING				                7 NAMT: |CA|
            #     13 ZIP4: MISSING				                8 NAMS: |92084    |
            #     14 PHON: MISSING				                9 ADR1: |7603328398|
            #     15 FAX: MISSING				                10 ADR2: ||
            #     16 EMAIL: MISSING				                11 CITY: |readyforrena@gmail.com|
            #
            # The two records need to be knit back together again.
            #
            if target == 'filername':

                if len(last_parts) == 0 and len(line_parts) == 6:
                    last_parts = line_parts.copy()
                    lines_read += 1
                    continue

                if len(line_parts) != 6 and len(line_parts) != 12:
                    last_parts = []

                if len(last_parts) == 6 and len(line_parts) == 12:
                    next_line_parts = last_parts
                    next_line_parts.extend(line_parts[1:])
                    last_parts = []
                    line_parts = next_line_parts

            # NAMES_CD.TSV also has problem with broken lines, like:
            # ERROR: 467496
            # {
            #     0 NAMID: |1576948|
            #     1 NAML: |SACRAMENTO VOTER PROJECT|   0 NAMID: ||
            #     2 NAMF: MISSING                      1 NAML: ||
            #     3 NAMT: MISSING                      2 NAMF: ||
            #     4 NAMS: MISSING                      3 NAMT: ||
            #     5 MONIKER: MISSING                   4 NAMS: ||
            #     6 MONIKER_POS: MISSING               5 MONIKER: ||
            #     7 NAMM: MISSING                      6 MONIKER_POS: ||
            #     8 FULLNAME: MISSING                  7 NAMM: ||
            #     9 NAML_SEARCH: MISSING               8 FULLNAME: |SACRAMENTO VOTER PROJECT|
            # }                                        9 NAML_SEARCH: MISSING
            #
            # this next fix is not working...
            if target == 'name':

                if len(last_parts) == 0 and len(line_parts) == 2:
                    last_parts = line_parts.copy()
                    lines_read += 1
                    continue

                if len(line_parts) != 2 and len(line_parts) != 9:
                    last_parts = []

                if len(last_parts) == 2 and len(line_parts) == 9:
                    next_line_parts = last_parts
                    next_line_parts.extend(line_parts[1:8])
                    last_parts = []
                    line_parts = next_line_parts

            # done with knitting together lines for now.

            line_parts = fix_parts(target, lhead, line_parts)

            if line_parts is None:
                out_file.write(f"ERROR: {lines_read}\n")
                out_file.write(as_dict(head, line.decode(encoding='utf-8').strip('\n').strip('\r').split('\t')) + '\n')
                errors += 1
                lines_read += 1
                continue

            line_errors = check_types(target, line_parts)

            if line_errors > 0:
                errors += line_errors
                out_file.write(f"ERROR: {lines_read}\n")
                out_file.write(as_dict(head, line_parts)+'\n')

            else:
                data_dict = dict(zip(lhead, line_parts))
                data_lines.append(data_dict)
                if len(data_lines) >= args.increment:
                    out_file.write(f"now: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    conn.execute(sa.insert(table, data_lines))
                    data_lines.clear()

            lines_read += 1

        # handle rows left-over from the last incremenr
        if len(data_lines) > 0:
            conn.execute(sa.insert(table, data_lines))
            data_lines.clear()

    except:
        out_file.write("EXCEPTION df:\n")
        traceback.print_exc(file=out_file)
        out_file.write("\n")

    finally:
        conn.execute(f"""
            update _file_imports
            set num_read = {lines_read}, error_count = {errors}
            where pk = {import_pk};""")

    out_file.close()


def import_all_data():

    engine = create_engine(f"mysql+pymysql://ray:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
    conn = engine.connect()

    row = conn.execute("select max(pk) as pk from _file_imports;").fetchone()

    if row['pk'] is None:
        import_pk = 1
    else:
        import_pk = int(row['pk']) + 1

    filenames = list()

    for file in os.listdir(data_dir()):

        target = file.replace('_CD.TSV', '').lower()

        if not re.match(r".*_CD.TSV", file):
            continue

        if should_exclude(target):
            continue

        filenames.append({'pk': import_pk, 'file': file})
        import_pk += 1

    print(f"filenames: {filenames}")

    if args.no_threads or len(filenames) == 1:
        for entry in filenames:
            import_data(entry)
    else:
        p_map(import_data, filenames)


if __name__ == '__main__':

    if args.run_checks is not None:
        if 'memo_refs' in args.run_checks:
            check_memo_refs()
        print("quitting...")
        quit()

    if args.use_fixes is not None:
        print("use fixes YES")
        import_fixes(args.use_fixes)
        quit()

    if not args.only_after:
        import_all_data()

    if args.include_after or args.only_after:
        afters()
