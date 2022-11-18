
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


def tables_with_column(col_name):

    file = open("tableCols.txt")

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

    file = open("tableCols.txt")

    found_table_name = None

    for line in file:
        parts = line.strip().split(' ')
        if len(parts) == 1:
            found_table_name = parts[0]
        if len(parts) > 1 and parts[0] == col_name:
            if found_table_name == table_name:
                return True


def index_exists_in_table(conn, table_name, col_name):
    rows = conn.execute(f"show indexes from {table_name}").fetchall()
    for row in rows:
        if row['Column_name'] == col_name:
            return True
    return False
