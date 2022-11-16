
Code for downloading data from Cal-Access and setting up access thereof.
Consists of scripts for downloading and importing the data, and a flask
application for displaying the data.

The download.py script is fairly simple. It will download the file from the
California Secretary of State's site, un-tar it and get rid of the extra
files.

The import.py script will delete the existing tables and add the new data.
It takes a long time to run.

TODO: It would be nice to add only the new data added. Theoretically, the files
only get added to and one can see that the daily changes are usually very small.

Works with Python 3.10.6 and a virtualenv set up with the requirements.txt given.

     % virtualenv .venv
     % .venv/bin/activate
     % pip install -r requirements.txt
     % python -m flask run

