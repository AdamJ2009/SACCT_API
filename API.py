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
    result = re.sub(r"\s+still logged in\s*$",f" - {now}",str(result))
    result = str(result).split() 
    print(result)
    if len(result) < 14:
        return "not a user"
    result = str(result[13] + "-" +  result[10] + "-" +result[11])
    return result

def not_a_user_json():
    data = {"Error":"Not Found","Reason":"Not a user"}
    response = jsonify(data)
    response.status_code = 404
    return response

def no_data_json(name,access_str):
    data = { "user":name,
                "last":{
                    "access":access_str,
                    "submit":"Not within 90 days"
                }
    }
    response = jsonify(data)
    response.status_code = 404
    return response


def get_time_submit(base_command):
    try:
        command = base_command + " -o Submit | tail -n 1"
        test = subprocess.run(command, capture_output=True ,shell = True).stdout
        test = clean_bytes(test)
        test = datetime.datetime.strptime(test, '%Y-%m-%dT%H:%M:%S')
        return str(test.strftime('%Y-%m-%d'))
    except:
        return "Nothing in last 90 days"

def get_count_jobs(base_command):
    command = base_command + "| wc -l"
    test = subprocess.run(command, capture_output=True ,shell = True).stdout
    return clean_bytes(test)

def get_job_times(base_command,count: int):
    command = base_command + " -P -o Start,End,Planned"
    result = subprocess.run(command, capture_output=True ,shell = True).stdout
    result = clean_bytes(result)
    #Turn into array
    result = result.replace("\n","|")
    result = result.split("|")
    #Parse array
    diff = datetime.timedelta(seconds=0)
    queue = datetime.timedelta(hours=0,minutes=0,seconds=0)
    for i in range(3,len(result),3):
        start = datetime.datetime.strptime(result[i], '%Y-%m-%dT%H:%M:%S')
        end = datetime.datetime.strptime(result[i+1], '%Y-%m-%dT%H:%M:%S')
        diff += (end-start)
        local_queue = result[i+2]
        (h, m, s) = local_queue.split(':')
        d = datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
        queue += d
    return diff/count,queue/count

def get_shape(base_command,count):
    command = base_command + " -P -o NNodes,NCPUS,Ntasks,Nodelist"
    print(command)
    result = subprocess.run(command, capture_output=True ,shell = True).stdout
    result = clean_bytes(result)
    result = result.replace("\n","|")
    result = result.split("|")
    print(result)
    node = 0
    cpu = 0
    for i in range(4,len(result),4):
        print(i//4)
        node += int(result[i])
        cpu += int(result[i+1])
    return node/count,cpu/count,0,0

    
@app.route('/user/<string:name>',methods=['GET'])
def get_user_metrics(name: str):
    if request.method == 'GET':
        last_access = get_last_user_access_time(name) #Check if the user has ever accessed this cluster
        if last_access == "not a user": 
            return not_a_user_json()
        else:
            last_access = datetime.datetime.strptime(last_access, '%Y-%b-%d')
            access_str = str(last_access.strftime('%Y-%m-%d'))
            print(last_access)
        user = "-u " + name + " "
        end =  "-E " + access_str 
        start  = "-S " + str((last_access - datetime.timedelta(days = 90)).strftime('%Y-%m-%d')) + " " #90 days forced limit
        base_command = "sacct -X " + user + start + end
        submit_time = get_time_submit(base_command)
        if submit_time == "Nothing in last 90 days":
            return no_data_json(name,access_str)
        count = get_count_jobs(base_command)
        count = int(count) - 2 #Table header needs to go as well
        average_time,average_queue = get_job_times(base_command,count)
        node,cpu,tasks,nodelist = get_shape(base_command,count)
        data = { "user":name,
                "last":{
                    "access":access_str,
                    "submit":submit_time
                },
                "jobs":{
                    "average_time":str(average_time),
                    "average_queue":str(average_queue),
                    "count":count
                },
                "shape":
                {
                    "avg_nodes":node,
                    "avg_cpu":cpu,
                    "avg_tasks":tasks,
                    "nodelist":nodelist
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
    # Source - https://stackoverflow.com/a/46134448
    # Posted by Jonathan
    # Retrieved 2026-08-20, License - CC BY-SA 3.0
    browser_useragents = ["ABrowse", "Acoo Browser", "America Online Browser", "AmigaVoyager", "AOL", "Arora", "Avant Browser", "Beonex", "BonEcho", "Browzar", "Camino", "Charon", "Cheshire", "Chimera", "Chrome", "ChromePlus", "Classilla", "CometBird", "Comodo_Dragon", "Conkeror", "Crazy Browser", "Cyberdog", "Deepnet Explorer", "DeskBrowse", "Dillo", "Dooble", "Edge", "Element Browser", "Elinks", "Enigma Browser", "EnigmaFox", "Epiphany", "Escape", "Firebird", "Firefox", "Fireweb Navigator", "Flock", "Fluid", "Galaxy", "Galeon", "GranParadiso", "GreenBrowser", "Hana", "HotJava", "IBM WebExplorer", "IBrowse", "iCab", "Iceape", "IceCat", "Iceweasel", "iNet Browser", "Internet Explorer", "iRider", "Iron", "K-Meleon", "K-Ninja", "Kapiko", "Kazehakase", "Kindle Browser", "KKman", "KMLite", "Konqueror", "LeechCraft", "Links", "Lobo", "lolifox", "Lorentz", "Lunascape", "Lynx", "Madfox", "Maxthon", "Midori", "Minefield", "Mozilla", "myibrow", "MyIE2", "Namoroka", "Navscape", "NCSA_Mosaic", "NetNewsWire", "NetPositive", "Netscape", "NetSurf", "OmniWeb", "Opera", "Orca", "Oregano", "osb-browser", "Palemoon", "Phoenix", "Pogo", "Prism", "QtWeb Internet Browser", "Rekonq", "retawq", "RockMelt", "Safari", "SeaMonkey", "Shiira", "Shiretoko", "Sleipnir", "SlimBrowser", "Stainless", "Sundance", "Sunrise", "surf", "Sylera", "Tencent Traveler", "TenFourFox", "theWorld Browser", "uzbl", "Vimprobable", "Vonkeror", "w3m", "WeltweitimnetzBrowser", "WorldWideWeb", "Wyzo", "Android Webkit Browser", "BlackBerry", "Blazer", "Bolt", "Browser for S60", "Doris", "Dorothy", "Fennec", "Go Browser", "IE Mobile", "Iris", "Maemo Browser", "MIB", "Minimo", "NetFront", "Opera Mini", "Opera Mobile", "SEMC-Browser", "Skyfire", "TeaShark", "Teleca-Obigo", "uZard Web", "Thunderbird", "AbiLogicBot", "Link Valet", "Link Validity Check", "LinkExaminer", "LinksManager.com_bot", "Mojoo Robot", "Notifixious", "online link validator", "Ploetz + Zeller", "Reciprocal Link System PRO", "REL Link Checker Lite", "SiteBar", "Vivante Link Checker", "W3C-checklink", "Xenu Link Sleuth", "EmailSiphon", "CSE HTML Validator", "CSSCheck", "Cynthia", "HTMLParser", "P3P Validator", "W3C_CSS_Validator_JFouffa", "W3C_Validator", "WDG_Validator", "Awasu", "Bloglines", "everyfeed-spider", "FeedFetcher-Google", "GreatNews", "Gregarius", "MagpieRSS", "NFReader", "UniversalFeedParser", "!Susie", "Amaya", "Cocoal.icio.us", "DomainsDB.net MetaCrawler", "gPodder", "GSiteCrawler", "iTunes", "lftp", "MetaURI", "MT-NewsWatcher", "Nitro PDF", "Snoopy", "URD-MAGPIE", "WebCapture", "Windows-Media-Player"]
    user_agent = request.headers.get('User-Agent', '')

    if any(browser in user_agent for browser in browser_useragents):
        response = "<h1>403 forbidden</h1><p>This is not a website, this is an api, you must use curl</p>"
        return response,403

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