
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


def index_exists_in_table(conn, table_name, col_name):
    rows = conn.execute(f"show indexes from {table_name}").fetchall()
    for row in rows:
        if row['Column_name'] == col_name:
            return True
    return False


class MyTable():

    _COLUMNS: dict

    @property
    def table_columns_info(self):
        if getattr(self, '_COLUMNS', None) is None:

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

            self._COLUMNS = tables

        return self._COLUMNS

    def tables(self):
        return self.table_columns_info

    def tables_with_column(self, col_name):

        info = self.table_columns_info

        found = list()

        for table_name in info.keys():
            if col_name in info[table_name].keys():
                found.append(table_name)

        return sorted(found)

    def table_has_column(self, table_name, col_name):

        info = self.table_columns_info

        if table_name in info:
            if col_name in info[table_name]:
                return True

        return False

    def table_columns(self):
        return self.table_columns_info
