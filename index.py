import os
import logging
from flask import Flask, request, render_template
app = Flask(__name__)


def doRender(tname, values={}):
    if not os.path.isfile(os.path.join(os.getcwd(), 'templates/'+tname)):  # No such file
        return render_template('index.html')
    return render_template(tname, **values)


# @app.route('/hello')
# def hello():
#     return 'Hello World!'

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
@app.route('/calculate', methods=['POST'])
def calculateHandler():
    if request.method == 'POST':
        l = request.form.get('labour')
        c = request.form.get('conservative')

        if l == '' or c == '':
            return doRender('index.html',
                    {'note': 'Please specify a number for each group!'})
        else:
            total = float(l) + float(c)
            lP = int(float(l) / total * 100)
            cP = int(float(c) / total * 100)
            return doRender('chart.html', {'data': str(lP) + ',' + str(cP)})
        return 'Should not ever get here'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)