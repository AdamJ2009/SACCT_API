from flask import Flask, render_template, request, redirect, session,  json, jsonify
import subprocess
import datetime

app = Flask(__name__)
    
@app.route('/user/<string:name>') 
def get_user_metrics(name: str):
    user = "-u " + name + " "
    end = "-E " + str(datetime.date.today().strftime('%Y-%m-%d')) + " "
    start  = "-S " + str((datetime.date.today() - datetime.timedelta(days = 90)).strftime('%Y-%m-%d')) + " "
    test = subprocess.Popen(["ping","-W","2","-c", "1", "127.0.0.1"], stdout=subprocess.PIPE)
    output = test.communicate()[0]
    output = "sacct " + user + start + end
    print(output)
    response = jsonify(str(output))
    response.status_code = 200
    return response

@app.route('/')
def not_a_website():
    output = '400 Bad Request:This is an API, not a website'
    response = jsonify(str(output))
    response.status_code = 400
    return response

if __name__ == "__main__":
    app.run(ssl_context="adhoc")
