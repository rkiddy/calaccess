
import sys

from sqlalchemy import create_engine, inspect

import datetime as dt

sys.path.append('..')
import common

engine = create_engine('mysql+pymysql://ray:alexna11@localhost/calaccess')
conn = engine.connect()
inspector = inspect(engine)


def tables_with_column(col_name):

    file = open("../importing/tableCols.txt")

    table_name = None
    found_tables = list()

    for line in file:
        parts = line.strip().split(' ')
        if len(parts) == 1:
            table_name = parts[0]
        if len(parts) > 1 and parts[0] == col_name:
            found_tables.append(table_name)

    return sorted(found_tables)


def full_name(naml, namf, namt, nams):
    if namt is not None:
        buf = f"{namt} "
    else:
        buf = ""
    if naml is not None and namf is not None:
        buf = f"{buf} {namf} {naml}"
    if naml is not None and namf is None:
        buf = f"{buf} {naml}"
    if naml is None and namf is not None:
        buf = f"{buf} {namf}"
    if nams is not None:
        buf = f"{buf} {nams}"
    return buf


def build(param, extra=None, param2=None, extra2=None ):

    context = dict()

    if param == 'calaccess_front':

        sql = """
        select date(filing_date) as filing_date, count(0) as count from filer_filings
        where filing_date < '2030-01-01'
        group by filing_date order by filing_date desc limit 30
        """

        rows = conn.execute(sql).fetchall()
        next_rows = list()
        for row in rows:
            next_rows.append(
                {
                    'filing_date': row['filing_date'].strftime('%Y-%m-%d'),
                    'count': row['count']
                }
            )

        context['front_dates'] = next_rows

        least_date = min([r['filing_date'] for r in next_rows])

        sql = f"""
        select filing_date, filing_id, form_id
        from filer_filings
        where filing_date >= '{least_date}' and
            filing_date < '2030-01-01'
        """

        cols = {
            'filing_date': 0,
            'filing_id': 1,
            'form_id': 2
        }

        rows = conn.execute(sql).fetchall()
        data = common.fill_in_table(rows, cols)

        # filings -> [filing_date] -> [form_id] -> # for the filing_date

        filings = dict()
        form_ids = list()

        for datum in data:
            form_ids.append(datum['form_id'])
            filing_date = datum['filing_date'].strftime('%Y-%m-%d')
            if filing_date not in filings:
                filings[filing_date] = dict()
            if datum['form_id'] not in filings[filing_date]:
                filings[filing_date][datum['form_id']] = 1
            else:
                filings[filing_date][datum['form_id']] += 1

        form_ids = sorted(list(set(form_ids)))

        context['form_ids'] = form_ids

        for filing_date in filings:
            for form_id in form_ids:
                if form_id not in filings[filing_date]:
                    filings[filing_date][form_id] = 0

        context['filing_counts'] = filings

        return context

    if param == 'calaccess_filingdate':

        if extra2 is None:
            sql = f"""
            select f1.filing_id, f1.filer_id, f1.period_id, f1.form_id,
                f1.filing_sequence as filing_seq, date(f1.rpt_start) as rpt_start,
                date(f1.rpt_end) as rpt_end, f2.filer_type, f2.naml, f2.namf, f2.namt,
                f2.nams, f2.city, f2.st, f2.zip4, f2.effect_dt, f3.start_date, f3.period_desc
            from filer_filings f1 left join filername f2 on f1.filer_id = f2.filer_id
                left join filing_period f3 on f1.period_id = f3.period_id
                    where f1.filing_date = '{extra}'
            """
        else:
            sql = f"""
            select f1.filing_id, f1.filer_id, f1.period_id, f1.form_id,
                f1.filing_sequence as filing_seq, date(f1.rpt_start) as rpt_start,
                date(f1.rpt_end) as rpt_end, f2.filer_type, f2.naml, f2.namf, f2.namt,
                f2.nams, f2.city, f2.st, f2.zip4, f2.effect_dt, f3.start_date, f3.period_desc
            from filer_filings f1 left join filername f2 on f1.filer_id = f2.filer_id
                left join filing_period f3 on f1.period_id = f3.period_id
                    where f1.filing_date = '{extra}' and
                        f1.form_id = '{extra2}'
            """

        rows = conn.execute(sql).fetchall()

        cols = {
            'filing_id': 0,
            'filer_id': 1,
            'period_id': 2,
            'form_id': 3,
            'filing_seq': 4,
            'rpt_start': 5,
            'rpt_end': 6,
            'filer_type': 7,
            'naml': 8,
            'namf': 9,
            'namt': 10,
            'nams': 11,
            'city': 12,
            'st': 13,
            'zip4': 14,
            'effect_dt': 15,
            'period_start': 16,
            'period_desc': 17
        }

        data = common.fill_in_table(rows, cols)

        next_data = dict()

        for datum in data:
            filer_id = datum['filer_id']

            if filer_id not in next_data:
                next_data[filer_id] = datum
            else:
                effect_dt = datum['effect_dt']
                if effect_dt > next_data[filer_id]['effect_dt']:
                    next_data[filer_id] = datum

        for filer_id in next_data:
            entry = next_data[filer_id]
            entry['full_name'] = full_name(entry['naml'], entry['namf'], entry['namt'], entry['nams'])

            # either the period_start or desc might be NULL, or both.
            if entry['period_start'] is not None and entry['period_desc'] is not None:
                start_date = entry['period_start'].strftime("%Y")
                entry['period'] = f"{start_date}&nbsp;Q{entry['period_desc'][-1]}"
            if entry['period_start'] is not None and entry['period_desc'] is None:
                start_date = entry['period_start'].strftime("%Y")
                entry['period'] = f"{start_date}&nbsp;Q?"
            if entry['period_start'] is None and entry['period_desc'] is not None:
                entry['period'] = f"????&nbsp;Q{entry['period_desc'][-1]}"
            if entry['period_start'] is None and entry['period_desc'] is None:
                entry['period'] = None

        context['filing_date'] = extra
        context['form_id'] = extra2

        context['calaccess_filing_date'] = common.order_dicts_by_key(list(next_data.values()), 'filing_id')

        return context

    if param == 'calaccess_filing_raw':

        filing_id = extra
        amend_id = 0

        context['filing_id'] = filing_id

        url_start = "https://cal-access.sos.ca.gov/PDFGen/pdfgen.prg"

        tables = list()

        for table in tables_with_column('filing_id'):

            sql = f"desc {table}"

            rows = conn.execute(sql).fetchall()
            column_names = list()
            sideways = dict()
            cols = dict()
            idx = 0

            for row in rows:
                column_names.append(row[0])
                cols[row[0]] = idx
                sideways[row[0]] = list()
                idx += 1

            sql = f"select * from {table} where filing_id = {filing_id}"

            rows = conn.execute(sql).fetchall()
            data = common.fill_in_table(rows, cols)

            if len(data) > 0:
                for datum in data:
                    for col_name in column_names:
                        sideways[col_name].append(datum[col_name])

                if 'amend_id' in sideways and len(sideways['amend_id']) > 0:
                    amend_id = max(sideways['amend_id'])

                buf = f"<table border=\"1\">\n    <caption>Table: {table}</caption>\n"

                for col_name in column_names:
                    buf = f"{buf}    <tr>\n        <th>{col_name}</th>\n"

                    for value in sideways[col_name]:
                        buf = f"{buf}        <td>&nbsp;&nbsp;</td><td>{value}</td>\n"

                    buf = f"{buf}    </tr>"

                buf = f"{buf}</table>\n"

                tables.append(buf)

        context['pdf'] = f"{url_start}?filingid={filing_id}&amendid={amend_id}"

        context['tables'] = tables

        return context

    if param == 'calaccess_filer_raw':

        filer_id = extra

        context['filer_id'] = filer_id

        tables = list()

        for table in tables_with_column('filer_id'):

            sql = f"desc {table}"

            rows = conn.execute(sql).fetchall()
            column_names = list()
            sideways = dict()
            cols = dict()
            idx = 0

            for row in rows:
                column_names.append(row[0])
                cols[row[0]] = idx
                sideways[row[0]] = list()
                idx += 1

            sql = f"select * from {table} where filer_id = {filer_id}"

            rows = conn.execute(sql).fetchall()
            data = common.fill_in_table(rows, cols)

            if len(data) > 0:
                for datum in data:
                    for col_name in column_names:
                        sideways[col_name].append(datum[col_name])

                buf = f"<table border=\"1\">\n    <caption>Table: {table}</caption>\n"

                for col_name in column_names:
                    buf = f"{buf}    <tr>\n        <th>{col_name}</th>\n"

                    for value in sideways[col_name]:
                        buf = f"{buf}        <td>&nbsp;&nbsp;</td><td>{value}</td>\n"

                    buf = f"{buf}    </tr>"

                buf = f"{buf}</table>\n"

                tables.append(buf)

        context['tables'] = tables

        return context
