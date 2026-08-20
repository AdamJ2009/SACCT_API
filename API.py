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
    now = str(datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y'))
    result = re.sub(r"\s+still logged in\s+\\n'$",f" - {now}, ",str(result))
    result = str(result).split()
    if len(result) == 1:
        return "not a user"
    result = str(result[13] + "-" +  result[10] + "-" +result[11])
    return result

def not_a_user_json():
    response = jsonify("Bad Request:Not a user")
    response.status_code = 400
    return response
    
@app.route('/user/<string:name>') 
def get_user_metrics(name: str):
    last_access = get_last_user_access_time(name) #Check if the user has ever accessed this cluster
    if last_access == "not a user": 
        return not_a_user_json()
    else:
        last_access = datetime.datetime.strptime(last_access, '%Y,-%b-%d')
        print(last_access)
    user = "-u " + name + " "
    end =  "-E " + str(last_access)
    start  = "-S " + str((last_access - datetime.timedelta(days = 90)).strftime('%Y-%m-%d')) + " " #90 days forced limit
    base_command = "sacct -X " + user + start + end
    print(base_command)
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