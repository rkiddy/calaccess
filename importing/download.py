import datetime as dt
import os
import os.path
import shutil
import subprocess
import time
import traceback

import pandas as pd
from dotenv import dotenv_values
from sqlalchemy import create_engine

cfg = dotenv_values(".env")

dir = dt.datetime.now().strftime("data/data_%Y%m%d/")
print(f"dir: {dir}")

if not os.path.isdir(dir):
    print("dir does NOT exist, creating.")
    os.mkdir(dir)
else:
    print("dir EXISTS")

os.chdir(dir)

if not os.path.isfile(f"dbwebexport.zip"):
    print("file NOT found: dbwebexport.zip. downloading.")
    r = subprocess.run(["/usr/bin/wget", "https://campaignfinance.cdn.sos.ca.gov/dbwebexport.zip"])
else:
    print("file FOUND dbwebexport.zip.")

if not os.path.isdir("DATA") and not os.path.isdir("CalAccess/DATA"):
    print("DATA directory NOT found")
    r = subprocess.run(["/usr/bin/unzip", "dbwebexport.zip"])
else:
    print("DATA directory FOUND")

if not os.path.isdir("DATA") and os.path.isdir("CalAccess/DATA"):
    print("moving DATA directory")
    shutil.move("CalAccess/DATA", ".")
else:
    print("NOT moving DATA directory")

if os.path.isdir("CalAccess"):
    print("removing directory CalAccess")
    shutil.rmtree("CalAccess")
else:
    print("NOT removing directory CalAccess")

os.chdir("../..")

hostname="localhost"
dbname="ca_calaccess"
uname="ray"
pwd="alexna11"

engine = create_engine(f"mysql+pymysql://ray:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")

conn = engine.connect()

sql = "select max(pk) as pk from _files;"
row = conn.execute(sql).fetchone()
max_pk = int(row['pk'])

idx = 0

found = list()

for row in conn.execute(f"select filename from _files where filename like '{dir}%%';").fetchall():
    found.append(row['filename'])

files = [f"{dir}dbwebexport.zip"]

for file in os.listdir(f"{dir}DATA"):
    files.append(f"{dir}DATA/{file}")

added = 0

for file in files:

    if file in found:
        continue

    if file.endswith('zip') or file.endswith('TSV'):

        idx += 1

        mtime = os.path.getmtime(file)
        mod_time = time.strftime('%Y-%m-%d', time.localtime(mtime))

        result = subprocess.run(["/usr/bin/wc", "-l", file], capture_output=True)
        lines_str = result.stdout.decode(encoding='utf-8').split(' ')[0]
        lines_num = int(lines_str)

        result = subprocess.run(['/usr/bin/openssl', 'dgst', '-sha1', file], capture_output=True)
        sha1_dgst = result.stdout.decode(encoding='utf-8').split(' ')[-1].strip()

        target = file.lower().replace('_cd.tsv', '').split('/')[-1]

        sql = "insert into _files values (_PK_, '_FILENAME_', _BYTES_, '_LASTMOD_', _LINES_, '_DGST_', _TGT_);"

        sql = sql.replace('_PK_', str(max_pk+idx))
        sql = sql.replace('_FILENAME_', file)
        sql = sql.replace('_BYTES_', str(os.path.getsize(file)))
        sql = sql.replace('_LASTMOD_', mod_time)
        sql = sql.replace('_DGST_', sha1_dgst)

        if file.endswith('TSV'):
            sql = sql.replace('_LINES_', str(lines_num))
            sql = sql.replace('_TGT_', f"'{target}'")
        else:
            sql = sql.replace('_LINES_', 'NULL')
            sql = sql.replace('_TGT_', 'NULL')

        added += 1

        engine.execute(sql)

print(f"Files added to db # {added}")

print("DONE!")
