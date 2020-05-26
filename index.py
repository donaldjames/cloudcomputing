import os
import logging
import json
import pandas as pd
import http.client
import multiprocessing as mp
from flask import Flask, request, render_template
app = Flask(__name__)

import socket
socket.getaddrinfo('127.0.0.1', 8080)

amazon_instance = "pwix736lp7.execute-api.us-east-1.amazonaws.com"
startEc2Instance = "/default/startEc2Instance"
dataFetchLambda = "/default/s3-lambda-function"
newSeries = "/default/varCalculation"


def doRender(tname, values={}):
    if not os.path.isfile(os.path.join(os.getcwd(), 'templates/'+tname)):  # No such file
        return render_template('index.html')
    return render_template(tname, **values)


@app.errorhandler(500)
def server_error(e):
    logging.exception('ERROR!')
    return """
        An error occurred: <pre>{}</pre>
        """.format(e), 500

@app.route('/varcalculator', methods=['GET', 'POST'])
def varcalculation():
    if request.method == 'POST':
        companyName = request.form.get("companyName")
        windowSize = request.form.get("windowSize")
        confdn_intrvl = request.form.get("confdn_intrvl")
        sampleSize = request.form.get("sampleSize")
        resources = request.form.get("resources")
        date = request.form.get("date")
        date = decode_date(date)
        resource_count = int(resources)
        sample = str(round(int(sampleSize)/int(resources)))
        parameters = '{"windowSize": "'+windowSize+'", "companyName": "'+companyName+'", "date": "'+date+'", "confdn_intrvl": "'+confdn_intrvl+'", "sampleSize": "'+sample+'"}'        
        c = http.client.HTTPSConnection(amazon_instance)
        c.request("POST", newSeries, parameters)
        response = c.getresponse()
        response = decode_response(response)
        message = {
            "var": response
        }
        # # Parallel processing using multiprocessing
        # mp_parallel = mp.Queue()
        # # Defining the number of resources to be used
        # # pool = mp.Pool(processes=resource_count)
        # # mp_parallel=[pool.map(lambda_process, args=[parameters]) for x in range(0,resource_count)]
        # print('-------------\n'*5)
        # print(mp_parallel)
        #result = [r.get() for r in mp_parallel]
        #response = decode_response(response)
    return render_template('varcalctemplate.html', message=message)

# def lambda_process(arguments):
#     print('*********\n'*5)
#     c = http.client.HTTPSConnection(amazon_instance)
#     c.request("POST", newSeries, arguments)
#     response = c.getresponse()
#     # response = decode_response(response)
#     response1 = response.read()
#     response = response.decode()    
#     data = json.loads(response)
#     print(data['body'])
#     return data['body']

# post the window size and the company name calls lambda and shows the
# graph and table in template
@app.route('/movingavgdata', methods=['POST'])
def movingaveragecalculation():
    if request.method == 'POST':
        # calling the lambda function s3-lambda-function which calculaates and returns the data along with moving average
        windowSize = request.form.get('windowSize')
        companyName = request.form.get('button')
        parameters = '{ "windowSize": "'+windowSize+'", "companyName": "'+companyName+'" }'
        # calling lambda function to get the data
        c = http.client.HTTPSConnection(amazon_instance)
        c.request("POST", dataFetchLambda, parameters)
        response = c.getresponse()
        # startting the ec2 instance using aws lambda function
        d = http.client.HTTPSConnection(amazon_instance)
        d.request("POST", startEc2Instance)
        d.getresponse()
        headers = ["Date", "Open", "High", "Low", "Close", "AdjClose", "MovingAverage", "Volume"]
        data = decode_response(response)
        datasets = []
        # transforming the data
        for d in data:
            row = []
            row.append(encode_date(d[0]))
            for i in range(1, 7):
                row.append(float(d[i]))
            row.append(int(d[7]))
            datasets.append(row)
        # dictionary for plotting the graph
        dataFrame = pd.DataFrame(datasets, columns=headers)
        graph_data = {'Dates': dataFrame.Date.to_list(), 'Movingavg': dataFrame.MovingAverage.to_list(), 'Price': dataFrame.AdjClose.to_list()}
        return render_template('listingpage.html', dataArray=datasets, headers=headers, graphData=graph_data, companyName=companyName)


def encode_date(date):
    dd, mm, yyyy = date.split('/')
    return (yyyy+'-'+mm+'-'+dd)

def decode_date(date):
    yyyy, mm, dd = date.split('-')
    return (dd+'/'+mm+'/'+yyyy)

def decode_response(response):
    response = response.read()
    response = response.decode()    
    data = json.loads(response)
    if data['statusCode'] == 200:
        data = data['body']
        return(data)
    else:
        return false


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def mainPage(path):
    return doRender(path)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
