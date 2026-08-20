from flask import Flask, render_template, request, redirect, session,  json, jsonify
import subprocess
import datetime
import re

app = Flask(__name__)

def get_last_user_access_time(user):
    command = "last " + user + " -F | head -n 1"
    result = subprocess.run(command, capture_output=True ,shell = True).stdout
    #Regex fix to remove still logged in and reutrn the current time
    print(result)
    now = str(datetime.datetime.now().strftime('%H:%M'))
    result = re.sub(r"\s+still logged in\s+\\n'$",f" - {now}",str(result))
    result = str(result).split()
    """
    if len(result) == 11:
        result.pop(-1)
    elif len(result) == 9:
        time = result[6].split(":")
        entry = datetime.datetime(year=datetime.date.today().year,month=result[4],day=result[5],hour=time[0],minute=time[1])
        exit = datetime.datetime.now().strftime('%m-%d %H:%M')
        print(entry,exit)
    else:
        return "not a user"
    """
    return result
    
@app.route('/user/<string:name>') 
def get_user_metrics(name: str):
    print(get_last_user_access_time(name))
    user = "-u " + name + " "
    end = "-E " + str(datetime.date.today().strftime('%Y-%m-%d')) + " "
    start  = "-S " + str((datetime.date.today() - datetime.timedelta(days = 90)).strftime('%Y-%m-%d')) + " "
    base_command = "sacct -X " + user + start + end
    test = subprocess.run(base_command, capture_output=True ,shell = True).stdout
    response = jsonify(str(test))
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