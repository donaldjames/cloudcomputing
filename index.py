import os
import logging
import json
import pandas as pd
from flask import Flask, request, render_template
app = Flask(__name__)

import socket
socket.getaddrinfo('127.0.0.1', 8080)

def doRender(tname, values={}):
    if not os.path.isfile(os.path.join(os.getcwd(), 'templates/'+tname)):  # No such file
        return render_template('index.html')
    return render_template(tname, **values)

# catch all other page requests - doRender checks if a page is available (shows it) or not (index)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def mainPage(path):
    return doRender(path)


@app.errorhandler(500)
def server_error(e):
    logging.exception('ERROR!')
    return """
        An error occurred: <pre>{}</pre>
        """.format(e), 500


# Defines a POST supporting calculate route
@app.route('/movingavgdata', methods=['POST'])
def calculateHandler():
    if request.method == 'POST':
        import http.client
        windowSize = request.form.get('windowSize')
        companyName = request.form.get('button')

        parameters = '{ "windowSize": "'+windowSize+'", "companyName": "'+companyName+'" }'

        c = http.client.HTTPSConnection("pwix736lp7.execute-api.us-east-1.amazonaws.com")
        c.request("POST", "/default/s3-lambda-function", parameters)
        response = c.getresponse()

        titles = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume", "Moving Average"]
        data = decode_response(response) 

        dates = []
        mvavg = []
        price = []
        datasets = []
        for d in data:
            row = d[0]
            for i in range(1, 6)
                row.append(float(d[i]))
            row.append(int(d[7]))
            datasets.append(row)
        
        print(type(dates))
        print(dates[0:5])
        print('******\n'*5)
        print(type(mvavg))
        print(mvavg[0:5])
        print('******\n'*5)
        data_dict = pd.DataFrame({'Dates': dates.to_list(), 'Movingavg': mvavg.to_list(), 'Price': price.to_list()})
        import ipdb
        ipdb.set_trace()
        print('******\n'*5)
        print('******\n'*5)
        print('******\n'*5)

        return render_template('listingpage.html', data_dict=data_dict)
        # return doRender('listingpage.html')


def decode_response(response):
    response = response.read()
    response = response.decode()    
    data = json.loads(response)
    if data['statusCode'] == 200:
        data = data['body']
        return(data)
    else:
        return false


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)