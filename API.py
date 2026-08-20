from flask import Flask, render_template, request, redirect, session,  json, jsonify
import subprocess
import datetime
import re

app = Flask(__name__)

def clean_bytes(data):
    return data.decode('utf-8').strip()

def get_last_user_access_time(user):
    command = "last " + user + " -F | head -n 1"
    result = subprocess.run(command, capture_output=True ,shell = True).stdout
    result = clean_bytes(result)
    #Regex fix to remove still logged in and reutrn the current time
    print(result)
    now = str(datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y'))
    result = re.sub(r"\s+still logged in\s*$",f" - {now}, ",str(result))
    result = str(result).split() 
    print(result)
    if len(result) == 1:
        return "not a user"
    result = str(result[13] + "-" +  result[10] + "-" +result[11])
    return result

def not_a_user_json():
    data = {"Error":"Bad Request","Reason":"Not a user"}
    response = jsonify(data)
    response.status_code = 400
    return response

def get_time_submit(base_command):
    command = base_command + " -o Submit | tail -n 1"
    test = subprocess.run(command, capture_output=True ,shell = True).stdout
    test = clean_bytes(test)
    test = datetime.datetime.strptime(test, '%Y-%m-%dT%H:%M:%S')
    return str(test.strftime('%Y-%m-%d'))

def get_count_jobs(base_command):
    command = base_command + "| wc -l"
    test = subprocess.run(command, capture_output=True ,shell = True).stdout
    return clean_bytes(test)

def get_job_times(base_command,count):
    command = base_command + " -P -o Start,End,Planned"
    result = subprocess.run(command, capture_output=True ,shell = True).stdout
    result = clean_bytes(result)
    print(result)
    #Turn into array
    result = result.replace("\n","|")
    result = result.split("|")
    print(result)
    #Parse array
    diff = 0
    queue = 0
    for i in range(3,len(result),3):
        diff += (datetime.datetime(result[i+1])-datetime.datetime(result[i]))
        queue += datetime.time(result[i+2])
    return diff/count,queue/count
    
@app.route('/user/<string:name>',methods=['GET'])
def get_user_metrics(name: str):
    if request.method == 'GET':
        last_access = get_last_user_access_time(name) #Check if the user has ever accessed this cluster
        if last_access == "not a user": 
            return not_a_user_json()
        else:
            last_access = datetime.datetime.strptime(last_access, '%Y,-%b-%d')
            access_str = str(last_access.strftime('%Y-%m-%d'))
            print(last_access)
        user = "-u " + name + " "
        end =  "-E " + access_str 
        start  = "-S " + str((last_access - datetime.timedelta(days = 90)).strftime('%Y-%m-%d')) + " " #90 days forced limit
        base_command = "sacct -X " + user + start + end
        submit_time = get_time_submit(base_command)
        count = get_count_jobs(base_command)
        average_time,average_queue = get_job_times(base_command,count)
        data = { "user":name,
                "last":{
                    "access":access_str,
                    "submit":submit_time
                },
                "jobs":{
                    "average_time":average_time,
                    "average_queue":average_queue,
                    "count":count
                }
        }
        response = jsonify(data)
        response.status_code = 200
        return response
    else:
        data = {"Error":"Method not allowed","Reason":"Not using get method"}
        response = jsonify(data)
        response.status_code = 405
        return response
    
@app.route('/',methods=['GET'])
def not_a_website():
    if request.method == 'GET':
        data = {"Error":"Bad Request","Reason":"No user"}
        response = jsonify(data)
        response.status_code = 400
        return response
    else:
        response = "This is an API, not a website"
        response.status_code = 405
        return response

if __name__ == "__main__":
    app.run(ssl_context="adhoc")