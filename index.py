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

############################################################################################
@app.route('/varcalc', methods=['GET', 'POST'])
def varcalculationwindow():
    if request.method == 'GET':
        companyName = request.args.get("cn")
        # cwindowSize = request.args("windowSize")
        date = request.args.get("date")
        parameters = {'companyName': companyName, 'date': date}
        return render_template("varcalculator_popupwindow.html", parameters=parameters)
############################################################################################

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
        sample = str(round(int(sampleSize)/resource_count))
        parameters = '{"windowSize": "'+windowSize+'", "companyName": "'+companyName+'", "date": "'+date+'", "confdn_intrvl": "'+confdn_intrvl+'", "sampleSize": "'+sample+'"}'
        pool = mp.Pool(processes = resource_count)
        var=pool.map(var_calc_lambda_function, [parameters for x in range(1,resource_count+1)])
        print(type(var[0]))
        var_val_list = [float(v) for v in var]
        var_avg = sum(var_val_list)/resource_count
        var_percentage = var_avg * int(sample)
        message = {
            "var_list": var,
            "average_var_value": var_avg,
            "companyName": companyName,
            "windowSize": windowSize,
            "resources": resource_count,
            "confdn_intrvl": confdn_intrvl,
            "sampleSize": sampleSize,
            "var_percentage": var_percentage
        }
    return render_template('varcalctemplate.html', message=message)

def var_calc_lambda_function(parameters):
    c = http.client.HTTPSConnection(amazon_instance)
    c.request("POST", newSeries, parameters)
    response = c.getresponse()
    response = decode_response(response)
    return response

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
        headers = ["Date", "Adj Close", "Moving Average", "Signal", "Current Position"]
        # Extracting the data from lambda response
        data = decode_response(response)
        # sorting the data and updating the table fields
        dataset = listing_page_data(data)
        # dictionary for plotting the graph
        dataFrame = pd.DataFrame(dataset, columns=headers)
        graph_data = {'Dates': dataFrame["Date"].to_list(), 'Movingavg': dataFrame["Moving Average"].to_list(), 'Price': dataFrame["Adj Close"].to_list()}
        return render_template('listingpage.html', dataArray=dataset, headers=headers, graphData=graph_data, companyName=companyName)


# listing page table values
def listing_page_data(data):
    dataset = []
    # transforming the data
    init_case = 1;
    for d in data:
        row = []
        row.append(encode_date(d[0])) # Date
        adj_close = float(d[5]) 
        mov_avg = float(d[6])
        bs_signal = int(d[8])
        row.append(adj_close) # Adj closing
        row.append(mov_avg) # Moving Average
        row.append(bs_signal)
        if init_case == 1:
            cur_position = adj_close * 1000
            init_case = 0
        elif bs_signal != 0:
            cur_position = adj_close * 1000 * bs_signal
        else:
            pass
        row.append(cur_position)
        dataset.append(row)
    return dataset

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
