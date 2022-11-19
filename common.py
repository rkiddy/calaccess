
from dotenv import dotenv_values

cfg = dotenv_values(".env")

# rows is a result cursor, columns is a dictionary or key -> column number in rows.
def fill_in_table(rows, columns):
    result = list()
    for row in rows:
        found = dict()
        for key in columns.keys():
            found[key] = row[columns[key]]
        result.append(found)
    return result


def order_dicts_by_key(data, key):
    results = list()
    values = sorted(list(set([d[key] for d in data])))
    for value in values:
        for data_dict in data:
            if data_dict[key] == value:
                results.append(data_dict)
    return results


def tables():

    file = open(f"{cfg['APP_HOME']}/tableCols.txt")

    found_tables = list()

    for line in file:
        parts = line.strip().split(' ')
        if len(parts) == 1:
            found_tables.append(parts[0])

    return sorted(found_tables)


def tables_with_column(col_name):

    file = open(f"{cfg['APP_HOME']}/tableCols.txt")

    table_name = None
    found_tables = list()

    for line in file:
        parts = line.strip().split(' ')
        if len(parts) == 1:
            table_name = parts[0]
        if len(parts) > 1 and parts[0] == col_name:
            found_tables.append(table_name)

    return sorted(found_tables)


def table_has_column(table_name, col_name):

    file = open(f"{cfg['APP_HOME']}/tableCols.txt")

    found_table_name = None

    for line in file:
        parts = line.strip().split(' ')
        if len(parts) == 1:
            found_table_name = parts[0]
        if len(parts) > 1 and parts[0] == col_name:
            if found_table_name == table_name:
                return True


def table_columns():

    tables = dict()

    with open(f"{cfg['APP_HOME']}/tableCols.txt") as f:
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


def index_exists_in_table(conn, table_name, col_name):
    rows = conn.execute(f"show indexes from {table_name}").fetchall()
    for row in rows:
        if row['Column_name'] == col_name:
            return True
    return False
