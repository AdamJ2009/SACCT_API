from flask import Flask, render_template, request, redirect, session,  json, jsonify
from werkzeug.exceptions import HTTPException
import subprocess
import datetime
import re
import os
import sys

app = Flask(__name__)

def get_last_user_access_time(user: str) -> str:
    # Pass arguments safely as a list with shell=False
    command = ["last", user, "-F"]
    
    # Run the command safely without shell execution
    completed_process = subprocess.run(
        command, 
        capture_output=True, 
        shell=False, 
        text=True
    )
    
    # Extract stdout and safely mimic 'head -n 1' in Python
    raw_output = completed_process.stdout
    result = raw_output.splitlines()[0] if raw_output.splitlines() else ""
    
    # Process output
    now = str(datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y'))
    result = re.sub(r"\s+still logged in\s*$", f" - {now}", str(result))
    result = str(result).split() 
    
    if len(result) < 14:
        return "not a user"
        
    return f"{result[13]}-{result[10]}-{result[11]}"

def not_a_user_json():
    data = {"Error":"Not Found","Reason":"Not a user"}
    response = jsonify(data)
    response.status_code = 404
    return response

def no_data_json(name,access_str,time = 90):
    last = "Not within " + str(time) + " days"
    data = { "user":name,
                "last":{
                    "access":access_str,
                    "submit":last
                }
    }
    response = jsonify(data)
    response.status_code = 404
    return response


def get_time_submit(base_command):
    command= base_command + ["-o", "Submit","-n"]
    result = subprocess.run(command, capture_output=True, text=True, shell=False)
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return "Nothing in last 90 days"
    # Python equivalent of 'tail -n 1'
    last_line = lines[-1]
    return last_line

def get_count_jobs(base_command):
    result = subprocess.run(base_command, capture_output=True, text=True, shell=False)
    return len(result.stdout.splitlines())

def get_job_times(base_command,count: int):
    command = base_command + ["-P", "-o", "Start,End,Planned"]
    result = subprocess.run(command, capture_output=True, text=True, shell=False).stdout
    #Turn into array
    result = result.replace("\n","|")
    result = result.split("|")
    #Parse array
    diff = datetime.timedelta(seconds=0)
    queue = datetime.timedelta(hours=0,minutes=0,seconds=0)
    for i in range(3,len(result),3):
        try:
            start = datetime.datetime.strptime(result[i], '%Y-%m-%dT%H:%M:%S')
            end = datetime.datetime.strptime(result[i+1], '%Y-%m-%dT%H:%M:%S')
            diff += (end-start)
            local_queue = result[i+2]
            (h, m, s) = local_queue.split(':')
            d = datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            queue += d
        except:
            count -= 1
    return diff/count,queue/count

def get_shape(base_command,count):
    base_command.pop(1)
    command = base_command + ["-P", "-o", "JobID,NNodes,NCPUS,Ntasks,Nodelist"]
    result = subprocess.run(command, capture_output=True, text=True, shell=False).stdout
    result = result.replace("\n","|")
    result = result.split("|")
    node = 0
    cpu = 0 
    task = 0
    nodelist = {}
    shape_ver = {}
    shapelist = {}
    single_core = {
        "count":0
    }
    multi_core = {
        "count":0,
        "avg_cpu":0
    }
    multi_node = {
        "count": 0,
        "avg_cpu":0,
        "avg_node":0,
        "avg_cpu_per_node":0
    }
    shapes = 0
    last = 0
    last_task = 0
    for i in range(5,len(result),5):
        current = (result[i].split("."))[0]
        if re.search(r"\d+\.(batch|0)$",result[i]) and last_task != current:
            last_task = current
            task += int(result[i+3])
        if re.search(r"\d+$",result[i]) and last != current:
            last = current
            #node i+1, cpu i+2, task i+3, nodelist i+4
            node += int(result[i+1])
            cpu += int(result[i+2])
            if result[i+4] not in nodelist:
                nodelist[result[i+4]] = 1
            else:
                nodelist[result[i+4]] += 1
            text_shape = str(result[i+1])+"|"+str(result[i+2])+"|"+"|"+(str(result[i+4]))
            if text_shape not in shape_ver:
                shape_ver[text_shape] = shapes
                shapelist[shapes] = {}
                shapelist[shapes]["count"] = 1
                shapelist[shapes]["nodes"] = int(result[i+1])
                shapelist[shapes]["cpu"] = int(result[i+2])
                shapelist[shapes]["nodelist"] = result[i+4]
                shapes += 1
            else:
                v = shape_ver[text_shape]
                shapelist[v]["count"] += 1
            if int(result[i+1]) == 1 and int(result[i+2]) == 1:
                single_core["count"] +=1
            elif int(result[i+2])>  1 and int(result[i+1]) == 1:
                multi_core['count'] += 1
                multi_core["avg_cpu"] += int(result[i+2])
            elif int(result[i+1]) > 1:
                multi_node['count'] += 1
                multi_node["avg_cpu"] += int(result[i+2])
                multi_node["avg_node"] += int(result[i+1])
                multi_node["avg_cpu_per_node"] += int(result[i+2]) / int(result[i+1])
    return node/count,cpu/count,task/count,nodelist,shapelist,single_core,multi_core,multi_node

def format_shapes(single,multi,node):
    shape = {}
    if single["count"] >= 1:
        shape["single_core"] = single
    if multi["count"] >= 1:
        multi["avg_cpu"] = multi["avg_cpu"] / multi["count"]
        shape["multi_core"] = multi
    if node["count"] >= 1:
        node["avg_cpu"] = node["avg_cpu"] / node["count"]
        node["avg_node"] = node["avg_node"] / node["count"]
        node["avg_cpu_per_node"] = node["avg_cpu_per_node"] / node["count"]
        shape["multi_node"] = node
    return shape #will give at least one shape if any job exists

def get_partition_list(base_command):
    command = base_command + ["-P","-o","Partition"]
    result = subprocess.run(command, capture_output=True, text=True, shell=False).stdout
    result = result.replace("\n","|")
    result = result.split("|")
    partitions = {}
    for i in range(1,len(result)):
        if result[i] not in partitions:
            partitions[result[i]] = 1
        else:
            partitions[result[i]] += 1
    return partitions

def convert_mb(value):
    if len(value) == 0:
        return 0
    letter = value[-1]
    value = int(value[0:len(value)-1])
    if letter == "G":
        return value * 1024
    elif letter == "M":
        return value
    elif letter == "K":
        return value / 1024
    else:
        return value / (1024*1024)

def time_converter(value):
    if re.search(r"^\d+:\d+:\d+$",value):
        days = 0
        ms = 0
        time = datetime.datetime.strptime(value, '%H:%M:%S')
    #d-h:m:s
    elif re.search(r"^\d+-\d+:\d+:\d+$",value):
        value = value.split("-")
        days = int(value[0])
        ms = 0
        time = datetime.datetime.strptime(value[1], '%H:%M:%S')
    #m:s.ms
    elif re.search(r"^\d+:\d+.\d+$",value):
        value = value.split(".")
        days = 0
        ms = int(value[1])
        time = datetime.datetime.strptime(value[0], '%M:%S')
    delta = datetime.timedelta(days=days,hours=time.hour,minutes=time.minute,seconds=time.second)
    return int(delta.total_seconds()*1000 + ms) #doesn't matter the time as long as its the same

def get_cpueff(base_command,count):
    command = base_command + ["-P","-o","JobID,TotalCPU,Elapsed,AllocCPUS"]
    result = subprocess.run(command, capture_output=True, text=True, shell=False).stdout
    result = result.replace("\n","|")
    result = result.split("|")
    cpueffsum = 0
    last = 0
    for i in range(4,len(result),4):
        current = (result[i].split("."))[0]
        if re.search(r"\d+\.(batch|0)$",result[i]) and last != current:
            last = current
            try:
                cpueffsum += (time_converter(result[i+1]) / ((time_converter(result[i+2])) * int(result[i+3])))
            except: 
                count -= 1
    return cpueffsum/count, #Will only fail if all metrics fail

def get_memeff(base_command,count):
    command = base_command + ["-P","-o","JobID,ReqMem,MaxRSS"]
    result = subprocess.run(command, capture_output=True, text=True, shell=False).stdout
    result = result.split("\n")
    result.pop(-1)
    memeff = 0
    reqmem = None
    max_rss = None
    last = 0
    count += 1
    for i in range(1,len(result)):
        result_l= result[i].split("|")
        current = (result_l[0].split("."))[0]
        if last != current:
            last = current
            if reqmem is None or max_rss is None:
                count -= 1
            reqmem = None
            max_rss = None
        if re.search(r"\d+$",result_l[0]) and last == current:
            reqmem = result_l[1]
            if reqmem == "":
                max_rss = None
        elif re.search(r"\d+\.(batch|0)$",result_l[0]) and last == current:
            max_rss = result_l[2]
            if max_rss == "":
                max_rss = None
        if reqmem is not None and max_rss is not None:
            try:
                memeff += convert_mb(max_rss) / convert_mb(reqmem)
                reqmem = None
                max_rss = None
            except: 
                count -= 1
    return memeff/count, #Will only fail if all metrics fail

def diskquota(user):
    try:
        command = ["sudo", "quota", "-w", "-u", user]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            command = ["quota", "-w", "-u", user]
            completed = subprocess.run(command, capture_output=True, text=True)
        stdout = completed.stdout.strip()
        if not stdout or completed.returncode != 0:
            return {}
        lines = [' '.join(line.split()) for line in stdout.splitlines() if line.strip()]
        quotanet = {}
        for line in lines[2:]:
            quota = line.split(" ")
            if len(quota) < 7:
                continue   
            quotanet[quota[0]] = { 
                "blocks": {
                    "used_bytes": quota[1],
                    "quota_bytes": quota[2],
                    "limit_bytes": quota[3]
                },
                "files": {
                    "used": quota[4],
                    "quota": quota[5],
                    "limit": quota[6]
                }
            }
        return quotanet
    except Exception:
        return {}

def time_metrics(name,access_str,last_access,days_back):
    start_date = (last_access - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
    base_command = [
        "sacct",
        "-X",
        "-u", name,
        "-S", start_date,
        "-E", access_str
    ]
    submit_time = get_time_submit(base_command)
    if submit_time == "Nothing in last 90 days":
        return "none"
    count = get_count_jobs(base_command)
    count = int(count) - 2 #Table header needs to go as well
    average_time,average_queue = get_job_times(base_command,count)
    node,cpu,tasks,nodelist,shapelist,single,multi,node_shape = get_shape(base_command,count)
    shape = format_shapes(single,multi,node_shape)
    partitions = get_partition_list(base_command)
    try:
        cpueff = float(get_cpueff(base_command,count)[0]) * 100
    except:
        cpueff= "Missing"
    try:
        memeff = float(get_memeff(base_command,count)[0]) * 100
    except:
        memeff = "Missing"
    data = {
            "jobs":{
                    "average_time":str(average_time),
                    "average_queue":str(average_queue),
                    "count":count,
                    "partitions":partitions,
                    "shapes":shape,
            },
            "gen_avg":
            {
                "avg_nodes":node,
                "avg_cpu":cpu,
                "avg_tasks":tasks,
                "nodelist":nodelist,
                "shapelist":shapelist
            },
            "efficiency": {
                "cpu%": cpueff,
                "mem%": memeff
            }
        }
    return data

@app.route('/user/<string:name>/<int:time>',methods=['GET'])
def get_user_metrics_days(name: str, time:int):
    epoch_start = datetime.date(1970, 1, 1)
    today = datetime.date.today()
    max_days = (today - epoch_start).days
    if time < 0 or time > max_days:
        response = jsonify({
            "Error": "Bad Request",
            "Reason": f"Invalid Time:Time must be between 0 and {max_days} days."
        })
        response.status_code = 400
        return response
    elif request.method == 'GET':
        last_access = get_last_user_access_time(name) #Check if the user has ever accessed this cluster
        if last_access == "not a user": 
            return not_a_user_json()
        else:
            last_access = datetime.datetime.strptime(last_access, '%Y-%b-%d')
            tomorrow = last_access + datetime.timedelta(days=1)
            access_str = str(tomorrow .strftime('%Y-%m-%d'))
        start_date = (last_access - datetime.timedelta(days=time)).strftime('%Y-%m-%d')
        base_command = [
            "sacct",
            "-X",
            "-u", name,
            "-S", start_date,
            "-E", access_str
        ]
        submit_time = get_time_submit(base_command)
        if submit_time == "Nothing in last 90 days":
            return no_data_json(name,access_str,time)
        data = { "user":name,
                        "last":{
                            "access":access_str,
                            "submit":submit_time
                        },
                        "days_back":{
                            time :None
                        }
                }
        data["days_back"][time] = time_metrics(name,access_str,last_access,time)
        data["quota_filesystem"] = diskquota(name)
        response = jsonify(data)
        response.status_code = 200
        return response
    else:
        data = {"Error":"Method not allowed","Reason":"Not using get method"}
        response = jsonify(data)
        response.status_code = 405
        return response
            
    
@app.route('/user/<string:name>',methods=['GET'])
def get_user_metrics(name: str):
    if request.method == 'GET':
        last_access = get_last_user_access_time(name) #Check if the user has ever accessed this cluster
        if last_access == "not a user": 
            return not_a_user_json()
        else:
            last_access = datetime.datetime.strptime(last_access, '%Y-%b-%d')
            tomorrow = last_access + datetime.timedelta(days=1)
            access_str = str(tomorrow .strftime('%Y-%m-%d'))
        start_date = (last_access - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
        base_command = [
            "sacct",
            "-X",
            "-u", name,
            "-S", start_date,
            "-E", access_str
        ]
        submit_time = get_time_submit(base_command)
        if submit_time == "Nothing in last 90 days":
            return no_data_json(name,access_str)
        data = { "user":name,
                "last":{
                    "access":access_str,
                    "submit":submit_time
                },
                "days_back":{
                    7:None,
                    30:None,
                    90:None
                }
        }
        days_back = [7,30,90]
        for day in days_back:
            data["days_back"][day] = time_metrics(name,access_str,last_access,day)
        data["quota_filesystem"] = diskquota(name)
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
        response = {"Error":"Method not allowed","Reason":"Not using get method"}
        response.status_code = 405
        return response

@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    data = {"Error":e.name,"Reason":e.description}
    response = jsonify(data)
    response.status_code = e.code
    return response
    

def main():
    cert_file = 'cert.pem'
    key_file = 'key.pem'

    # Check for certificates before starting the socket
    if os.path.exists(cert_file) and os.path.exists(key_file):
        ssl_ctx = (cert_file, key_file)
        print("Starting server with custom SSL certificates...")
    else:
        print("No certificate found, running with adhoc, do not deploy with adhoc")
        ssl_ctx = 'adhoc'

    try:
        app.run(
            port=5000,
            ssl_context=ssl_ctx,
        )
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        sys.exit(0)
    except OSError as e:
        if "Address already in use" in str(e):
            print("\n[Error] Port 5000 is already in use. Run 'pkill -f API.py' or pick another port.")
        else:
            raise e

if __name__ == '__main__':
    main()