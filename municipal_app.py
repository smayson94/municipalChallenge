from flask import Flask, request, render_template
from datetime import datetime
import sqlite3
import os
import requests
import json
import json
import urllib2
import time

os.system('clear')

openfigi_url = 'https://api.openfigi.com/v2/mapping'
header = {'Content-Type': 'application/json'}

app = Flask(__name__)

conn = sqlite3.connect('cusip.db')
c = conn.cursor()

Ids = []

openfigi_apikey = '27707711-1d3d-428e-86ff-69890b247fd2' # Put API Key here

def map_jobs(jobs):
    '''
    Send an collection of mapping jobs to the API in order to obtain the
    associated FIGI(s).
    Parameters
    ----------
    jobs : list(dict)
        A list of dicts that conform to the OpenFIGI API request structure. See
        https://www.openfigi.com/api#request-format for more information. Note
        rate-limiting requirements when considering length of `jobs`.
    Returns
    -------
    list(dict)
        One dict per item in `jobs` list that conform to the OpenFIGI API
        response structure.  See https://www.openfigi.com/api#response-fomats
        for more information.
    '''
    handler = urllib2.HTTPHandler()
    opener = urllib2.build_opener(handler)
    openfigi_url = 'https://api.openfigi.com/v1/mapping'
    request = urllib2.Request(openfigi_url, data=json.dumps(Ids))
    request.add_header('Content-Type','application/json')
    if openfigi_apikey:
        request.add_header('X-OPENFIGI-APIKEY', openfigi_apikey)
    request.get_method = lambda: 'POST'
    connection = opener.open(request)
    if connection.code != 200:
        raise Exception('Bad response code {}'.format(str(response.status_code)))
    return json.loads(connection.read())

@app.route('/invalid')
def invalid_id(error):
    return render_template('404.html')


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/greet')

def get_cusip_info():
    del Ids[:]
    username = request.args.get('username', 'World')
    CUSIPS = request.args['cusip']
    IDlist = CUSIPS.split(',')

    for temp in IDlist:
        my_dict = {}
        my_dict["idType"] = 'ID_CUSIP'
        my_dict["idValue"] = temp
        Ids.append(my_dict)

    job_results = map_jobs(Ids)

    for counter, item in enumerate(job_results, start=0):
        if 'data' in job_results[counter].keys():
            cusip_code = Ids[counter].get('idValue')
            ticker = job_results[counter].get('data')[0].get('ticker')
            name = job_results[counter].get('data')[0].get('name')
            market_sector = job_results[counter].get('data')[0].get('marketSector')
            security_type = job_results[counter].get('data')[0].get('securityType')
            exchange_code = job_results[counter].get('data')[0].get('exchCode')
            current_time = time.time()

            # Connect to Database and create database session
            conn = sqlite3.connect('cusip.db')

            # Create a cursor
            c = conn.cursor()

            c.execute("INSERT INTO cusip VALUES (?, ?, ?, ?, ?, ?, ?)", 
                (cusip_code, ticker, name, market_sector, security_type, exchange_code, time.time()))
            c.execute("SELECT * FROM cusip")
            print(c.fetchall())
            #commit changes
            conn.commit()
            return render_template('greet.html', username = username, jobResults = job_results,  Ids = Ids, len = len(job_results), IDlist = IDlist, 
                ticker = ticker, name = name, market_sector= market_sector)
        else:
            return render_template('home.html')

# Launch the FlaskPy dev server
app.run(host="localhost", debug=True)