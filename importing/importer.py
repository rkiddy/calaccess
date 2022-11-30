
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

verbose = False


def dprint(msg):
    if verbose:
        print(msg)


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


def setup():

    engine = create_engine(f"mysql+pymysql://ray:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
    conn = engine.connect()

    sql = """
    create table if not exists _file_imports (
        pk int primary key,
        filename varchar(127),
        num_read int,
        error_count int,
        import_dt datetime)
    """

    conn.execute(sql)

    sql = """
    create table if not exists _files (
        pk int primary key,
        filename varchar(128),
        num_bytes bigint,
        last_mod varchar(31),
        num_lines bigint,
        sha1_digest varchar(63),
        target varchar(63))
    """

    conn.execute(sql)


def create_table(engine, table_name, head):

    meta = sa.MetaData()
    table = sa.Table(table_name, meta)
    for col_head in head:
        col_type = common.table_columns()[table_name][col_head]
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
    # d = sorted([d for d in os.listdir("data/") if re.match(r'^data_.*\.TSV', d)])[-1]
    return f"data/data_20221126/DATA"


# FIX005
def fix_empty_naml(targeted, target, head, line_parts, idx):
    if target == targeted:
        if len(line_parts) == (len(head) + 1):
            if line_parts[idx].strip(' ') == '' and line_parts[idx+1] != '':
                dprint(f"FIX0005: fixing {target}: {line_parts}")
                line_parts.pop(idx)
    return line_parts


def check_types(target, line_parts):

    errs = 0

    for idx in range(len(line_parts)):

        col_type = list(common.table_columns()[target].values())[idx]
        if line_parts[idx] is None:
            continue

        value = line_parts[idx].strip()

        if col_type == 'date':
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                print(f"error for value {target}: \"{value}\" of type {col_type}")
                errs += 1

        if col_type.startswith('varchar'):
            max_len = int(col_type.replace('varchar(', '').replace(')', ''))
            if len(value) > max_len:
                print(f"error for value {target}: \"{value}\" of type {col_type}")
                errs += 1

        if col_type == 'int':
            if not re.match(r'^-?\d*$', value):
                print(f"error for value {target}: \"{value}\" of type {col_type}")
                errs += 1

        if col_type == 'decimal':
            parts = value.split('.')
            if len(parts) != 2 or not re.match(r'^\d*$', parts[0]) or not re.match(r'^\d*$', parts[1]):
                print(f"error for value {target}: \"{value}\" of type {col_type}")
                errs += 1

    return errs


def fix_parts(target, head, lines):

    parts = lines[0]

    # FIX0001
    if target == 'cvr2_registration':
        if len(parts) == (len(common.table_columns()[target]) + 1):
            if parts[7] == '' and re.match(r'^[CLE]?\d+$', parts[8]):
                dprint(f"FIX0001: fixing {target}: {parts}")
                parts.pop(7)

    # FIX0002
    if target == 'cvr_registration':
        if len(parts) == (len(common.table_columns()[target]) + 1):
            # data found on 2022-11-16 rrk
            if parts[0] == '1719434' and parts[1] == '0':
                print(f"FIX0002: fixing {target}: {parts}")
                parts.pop(38)
            if parts[0] == '2329423' and parts[1] == '0':
                dprint(f"FIX0002: fixing {target}: {parts}")
                parts.pop(38)

    # this seems to get a variable number of tabs after, even when all the data is fine.
    # check the filing_id, trans_id, cum_ytd, cum_oth and then pop off empty fields.
    #
    # FIX0003
    if target == 'rcpt':
        if len(parts) > 63:
            if re.match (r'^\d+$', parts[20]):
                if re.match (r'^\d+$', parts[21]):
                    if re.match(r'^\d+$', parts[0]):
                        if re.match(r'^\d+$', parts[5]):
                            while len(parts) > 63 and parts[-1] == '':
                                dprint(f"FIX0003: fixing {target}: {parts}")
                                parts.pop()

    # same thing here, variable number of tabs.
    #
    # FIX004
    if target == 'cvr_campaign_disclosure':
        if len(parts) > 86:
            if parts[37] in ['Y', 'N']:
                if parts[38] in ['Y', 'N']:
                    if parts[39] in ['Y', 'N']:
                        if parts[40] in ['Y', 'N']:
                            while len(parts) > 86 and parts[-1] == '':
                                dprint(f"FIX0004: fixing {target}: {parts}")
                                parts.pop()

    # these all target missing NAML values when this got pushed up.
    #
    parts = fix_empty_naml('cvr_campaign_disclosure', target, head, parts, 6)
    parts = fix_empty_naml('cvr_campaign_disclosure', target, head, parts, 26)
    parts = fix_empty_naml('cvr_campaign_disclosure', target, head, parts, 61)
    parts = fix_empty_naml('cvr_e530', target, head, parts, 5)
    parts = fix_empty_naml('cvr_e530', target, head, parts, 16)
    parts = fix_empty_naml('cvr_lobby_disclosure', target, head, parts, 7)
    parts = fix_empty_naml('cvr_lobby_disclosure', target, head, parts, 28)
    parts = fix_empty_naml('cvr_lobby_disclosure', target, head, parts, 32)
    parts = fix_empty_naml('cvr_lobby_disclosure', target, head, parts, 46)
    parts = fix_empty_naml('cvr_registration', target, head, parts, 7)
    parts = fix_empty_naml('cvr_registration', target, head, parts, 29)
    parts = fix_empty_naml('cvr_registration', target, head, parts, 33)
    parts = fix_empty_naml('cvr_so', target, head, parts, 6)
    parts = fix_empty_naml('cvr_so', target, head, parts, 26)
    parts = fix_empty_naml('cvr2_campaign_disclosure', target, head, parts, 13)
    parts = fix_empty_naml('cvr2_campaign_disclosure', target, head, parts, 23)
    parts = fix_empty_naml('cvr2_lobby_disclosure', target, head, parts, 4)
    parts = fix_empty_naml('cvr2_registration', target, head, parts, 8)
    parts = fix_empty_naml('cvr2_so', target, head, parts, 7)
    parts = fix_empty_naml('cvr3_verification_info', target, head, parts, 9)
    parts = fix_empty_naml('debt', target, head, parts, 7)
    parts = fix_empty_naml('debt', target, head, parts, 21)
    parts = fix_empty_naml('expn', target, head, parts, 7)
    parts = fix_empty_naml('expn', target, head, parts, 21)
    parts = fix_empty_naml('expn', target, head, parts, 26)
    parts = fix_empty_naml('expn', target, head, parts, 33)
    parts = fix_empty_naml('f501_502', target, head, parts, 13)
    parts = fix_empty_naml('f501_502', target, head, parts, 26)
    parts = fix_empty_naml('filername', target, head, parts, 5)
    parts = fix_empty_naml('latt', target, head, parts, 7)
    parts = fix_empty_naml('lccm', target, head, parts, 7)
    parts = fix_empty_naml('lccm', target, head, parts, 15)
    parts = fix_empty_naml('lemp', target, head, parts, 6)
    parts = fix_empty_naml('lexp', target, head, parts, 8)
    parts = fix_empty_naml('loan', target, head, parts, 8)
    parts = fix_empty_naml('loan', target, head, parts, 26)
    parts = fix_empty_naml('loan', target, head, parts, 33)
    parts = fix_empty_naml('lobby_amendments', target, head, parts, 9)
    parts = fix_empty_naml('lobby_amendments', target, head, parts, 15)
    parts = fix_empty_naml('lobby_amendments', target, head, parts, 21)
    parts = fix_empty_naml('lobby_amendments', target, head, parts, 27)
    parts = fix_empty_naml('loth', target, head, parts, 11)
    parts = fix_empty_naml('lpay', target, head, parts, 7)
    parts = fix_empty_naml('names', target, head, parts, 1)
    parts = fix_empty_naml('names', target, head, parts, 9)
    parts = fix_empty_naml('rcpt', target, head, parts, 7)
    parts = fix_empty_naml('rcpt', target, head, parts, 25)
    parts = fix_empty_naml('rcpt', target, head, parts, 32)
    parts = fix_empty_naml('rcpt', target, head, parts, 42)
    parts = fix_empty_naml('s401', target, head, parts, 6)
    parts = fix_empty_naml('s401', target, head, parts, 10)
    parts = fix_empty_naml('s401', target, head, parts, 20)
    parts = fix_empty_naml('s497', target, head, parts, 7)
    parts = fix_empty_naml('s497', target, head, parts, 22)
    parts = fix_empty_naml('s498', target, head, parts, 8)
    parts = fix_empty_naml('s498', target, head, parts, 17)

    if len(parts) != len(head):
        dprint(f"FIX0006: aborting {target}: {parts}")
        return None
        # raise Exception(f"target: {target}, incorrect # columns")

    for idx in range(len(head)):
        col_name = head[idx]
        col_type = common.table_columns()[target][col_name.lower()]
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
    add_index_for_columns_in_tables(conn, 'form_id')
    add_index_for_columns_in_tables(conn, 'filing_date')

    # filer_filings header received_filings


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


def importable_lines(out_file, target, columns, lines):
    """
    :param out_file: for debugging, can be None for testing.
    :param target: the table for which the lines are intended.
    :param columns: for the target table.
    :param lines: an array of the last 6 lines of the input.
    :return: either None or the last line with fixes.
    """

    # FILERNAME_CD.TSV has problems with broken lines. Like this:
    # ERROR: 1131228
    # {   lines[1]                                  lines[0]
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

        if len(lines[1]) == 6 and len(lines[0]) == 12:
            next_line = lines[1].copy()
            next_line.extend(lines[0][1:])
            lines[0] = next_line

    # NAMES_CD.TSV also has problem with broken lines, like:
    #
    # ERROR: 467496
    # {   lines[1]                             lines[0]
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
    if target == 'names':

        if len(lines[1]) == 2 and len(lines[0]) == 9:
            next_parts = lines[1].copy()
            next_parts.extend(lines[0][1:8])
            lines[0] = next_parts

    next_parts = fix_parts(target, columns, lines)

    if next_parts is None:
        if out_file:
            out_file.write(f"ERROR: {lines[0]}\n")
            out_file.write(as_dict(columns, lines[0]) + '\n')
        return None

    line_errors = check_types(target, lines[0])

    if line_errors > 0 and out_file:
        out_file.write(f"ERROR: {lines[0]}\n")
        out_file.write(as_dict(columns, lines[0])+'\n')

    else:
        data_dict = dict(zip(columns, lines[0]))
        return data_dict


def import_data(info):
    """
    For each file, preps the tables, gathers lines and sends them to import.
    :param info: pk -> import_pk, file: a filename.
    :return:
    """

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

    parts_list = [[],[],[],[],[],[]]

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

            parts_list.insert(0, line_parts)
            parts_list.pop()

            next_parts = importable_lines(out_file, target, lhead, parts_list)

            if next_parts is None:
                out_file.write(f"ERROR: {lines_read}\n")
                out_file.write(as_dict(head, line.decode(encoding='utf 8').strip('\n').strip('\r').split('\t')) + '\n')
                errors += 1
                lines_read += 1
                continue

            line_errors = check_types(target, line_parts)

            if line_errors > 0:
                errors += line_errors
                out_file.write(f"ERROR: {lines_read}\n")
                out_file.write(as_dict(head, line_parts) + '\n')

            else:
                data_dict = dict(zip(lhead, line_parts))
                data_lines.append(data_dict)
                if len(data_lines) >= args.increment:
                    out_file.write(f"now: {dt.datetime.now().strftime('%Y %m %d %H:%M:%S')}\n")
                    conn.execute(sa.insert(table, data_lines))
                    data_lines.clear()

        if len(data_lines) >= 0:
            out_file.write(f"now: {dt.datetime.now().strftime('%Y %m %d %H:%M:%S')}\n")
            conn.execute(sa.insert(table, data_lines))
            data_lines.clear()

    except:
        out_file.write("EXCEPTION df:\n")
        traceback.print_exc(file=out_file)
        out_file.write("\n")

    finally:
        # conn.execute(f"""
        #     update _file_imports
        #     set num_read = {lines_read}, error_count = {errors}
        #     where pk = {import_pk};""")
        pass

    out_file.close()


def data_file_jobs():
    """
    :return: list of dictionaries with a import pk and a filename.
    """

    engine = create_engine(f"mysql+pymysql://ray:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
    conn = engine.connect()

    row = conn.execute("select max(pk) as pk from _file_imports").fetchone()

    if row['pk'] is None:
        import_pk = 1
    else:
        import_pk = int(row['pk']) + 1

    found = list()

    for file in os.listdir(data_dir()):

        target = file.replace('_CD.TSV', '').lower()

        if not re.match(r".*_CD.TSV", file):
            continue

        if should_exclude(target):
            continue

        found.append({'pk': import_pk, 'file': file})
        import_pk += 1

    # print(f"filenames: {found}")
    return found


if __name__ == '__main__':

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

    setup()

    if args.run_checks is not None:
        if 'memo_refs' in args.run_checks:
            check_memo_refs()
        print("quitting...")
        quit()

    if not args.only_after:
        for file_info in data_file_jobs():
            import_data(file_info)

    if args.include_after or args.only_after:
        afters()
