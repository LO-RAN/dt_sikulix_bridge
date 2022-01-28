import sys
import os
import fnmatch
from flask import Flask, request, abort, send_file, redirect, url_for
import json
import subprocess
from datetime import datetime
from threading import Thread, Lock
from flask import render_template
from flask_basicauth import BasicAuth
from dt_third_party_synthetic import get_client, process_third_party_results, test_api_validity
from werkzeug.utils import secure_filename

from dynatrace_local_override import Dynatrace

# to make it work when packaged as a single executable with pyinstaller
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)

# credentials protecting the scripts upload/delete features
app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = 'dynatrace'

basic_auth = BasicAuth(app)

# used for making sure we chain background threads (and NOT run them in //)
mutex = Lock()

# ---------------- Flask URLs ----------------

# display an HTML page as default URL
@app.route("/")
def index():
    return render_template("index.html", timestamp=datetime.now())


# display an HTML page with API description
@app.route("/testtool_API")
def testtool_API():
    return render_template("API.html", timestamp=datetime.now())


# upload a new compiled jar SikuliX script
@app.route('/testtool_upload_script', methods=['POST'])
@basic_auth.required
def testtool_upload_script():
    # check if the post request has the file part
    if 'file' not in request.files:
        return redirect(url_for('testtool_scripts', error_msg="No file provided"))
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return redirect(url_for('testtool_scripts', error_msg="No file selected"))
    if not allowed_file(file.filename):
        return redirect(url_for('testtool_scripts', error_msg="File type not allowed"))

    filename = secure_filename(file.filename)
    file.save(os.path.join(scripts_path(), filename))
    return redirect(url_for('testtool_scripts', error_msg=" "))


# delete a deployed compiled jar SikuliX script
@app.route('/testtool_delete_script', methods=['GET'])
@basic_auth.required
def testtool_delete_script():
    filename = request.args.get('filename')
    if filename == None:
        return redirect(url_for('testtool_scripts', error_msg="No file provided"))

    if not filename.endswith("_sikuli.jar"):
        return redirect(url_for('testtool_scripts', error_msg="Not a SikuliX .jar file"))

    if not os.path.exists(os.path.join(scripts_path(), filename)):
        return redirect(url_for('testtool_scripts', error_msg="The file does not exist"))    

    os.remove(os.path.join(scripts_path(), filename))
    # remove also results for that script
    if(os.path.exists(output_file(filename, "OUTPUT.log"))):
        os.remove(output_file(filename, "OUTPUT.log"))
    if(os.path.exists(output_file(filename, "timings.txt"))):    
        os.remove(output_file(filename, "timings.txt"))
    # and screenshots
    for file in os.listdir(output_path()):
        if fnmatch.fnmatch(file, script_name(filename)+'_SCREENSHOT_*.png'):
            os.remove(os.path.join(output_path(),file))


    return redirect(url_for('testtool_scripts', error_msg=" "))


# start the execution of a SikuliX script (old gen) 
@app.route('/testtool_launcher', methods=['POST'])
def testtool_launcher():
    global cmd
    
    printlog("testtool_launcher")
    sys.stdout.flush()

    printlog("get parameters")
    script_name = request.json['script_name']
    if script_name == None:
        printlog("script_name == None")
    function_to_execute = request.json['function_to_execute']
    if function_to_execute == None:
        printlog("function_to_execute == None")
    printlog("script_name = "+script_name)
    printlog("function_to_execute = "+function_to_execute)
    cmd_exe=cmd.format(os.path.join(scripts_path(), script_name), function_to_execute)
    printlog("Command = "+cmd_exe)
    return_code, log = run_cmd(cmd_exe)

    # save log on disk
    f = open(script_name+"\OUTPUT.log", "w")
    f.write(log)
    f.close()
    # generate URL to retrieve log
    output=request.url_root+"testtool_log?filename="+script_name+"\OUTPUT.log"

    if (return_code != -1) and (not '[error]' in log) :
        printlog('return 200')
        return output, 200
    else:
        printlog('return 500')


        # generate URL to retreive screenshot and add it to output
        output=output+"\n"+request.url_root+"testtool_error_screenshot?filename="+script_name+"\ERROR.png"

        printlog(output)

        # send back as response
        return output, 500


# start the execution of a SikuliX script (new gen)
@app.route('/testtool_launcher2', methods=['POST'])
def testtool_launcher2():
    global cmd

    
    printlog("testtool_launcher2")
    sys.stdout.flush()

    params=request.form.copy() 

    if 'script' not in params or 'api_url' not in params or 'api_token' not in params:
        return "'script', 'api_url' and 'api_token' fields required", 400

    # digest these 3 mandatory parameters
    script = params['script']
    params.pop('script')

    api_url = params['api_url']
    params.pop('api_url')

    api_token = params['api_token']
    params.pop('api_token')

    # check whatever possible upfront to minimize the causes of failure
    # i.e. : does the script actually exists ?
    #        does the API URL reachable and the Token valid for Synthetic ingestion ?
    #        ...

    is_ok=True
    # is the script name provided corresponding to source code format ?
    if script.endswith(".sikuli"):
        # it should be found as a folder
        if not os.path.isdir(os.path.join(scripts_path(), script)):
            is_ok=False
    # is the script name provided correponding to a compiled jar file
    elif script.endswith("_sikuli.jar"):
        # it should be found as a regular file
        if not os.path.isfile(os.path.join(scripts_path(), script)):
            is_ok=False
    # in all other cases, that is a wrong format
    else:
        is_ok=False

    if not is_ok:
        return script+" not found. Make sure it exists at configured scripts'location as either a <script>.sikuli folder or a <script>_sikuli.jar file.", 400

    script_args=""
    
    # process remaining parameters to provide them to the executed script 
    for p in params:
        script_args+=p+'='+params[p]+" "        

    cmd_exe=cmd.format(os.path.join(scripts_path(), script), script_args)

    dt_client=get_client( api_url, api_token)
    try:
        r=test_api_validity(dt_client)
        if r.status_code >= 400:
            return r.reason, r.status_code
    except Exception as e:
        return str(e), 500


    #printlog("Running command : "+cmd_exe)

    # execute script in a separate thread to be able to respond quickly with an aknowledgment
    Thread(target = run_cmd2, args=(cmd_exe, dt_client, script, request.url_root)).start()

    return "request processed", 200


# get a json properties file (old gen)
@app.route('/testtool_properties', methods=['GET'])
def testtool_properties():
    printlog("testtool_properties")
    sys.stdout.flush()
    filename = request.args.get('filename')
    if filename == None:
        abort(400)
    with open(filename) as f:
        payload = json.load(f)
        return payload, 200

# display an HTML page with a script's execution results (screenshots, response times, errors, detailed log)
@app.route('/testtool_execution_results', methods=['GET'])
def testtool_execution_results():
    printlog("testtool_execution_results")
    sys.stdout.flush()
    filename = request.args.get('filename')
    if filename == None:
        abort(400)

    details=[]
    if not (os.path.isfile(output_file(filename,"timings.txt"))):
        return "No execution results yet for this script"

    f = open(output_file(filename,"timings.txt"), "r")
    for line in f:
        detail=json.loads(line)
        if detail['startTimestamp']:
            detail['startTimestamp']=datetime.fromtimestamp(detail['startTimestamp']/1000.0)
        details.append(detail)
    f.close()

    return render_template("results.html", script=script_name(filename),details=details)

# display an HTML page with the list of currently deployed scripts with ability to add, remove, view last results
@app.route('/testtool_scripts', methods=['GET'])
def testtool_scripts():
    printlog("testtool_scripts")
    sys.stdout.flush()
    error_msg = request.args.get('error_msg')
    if error_msg is None:
        error_msg=" "
    details=[]

    for filename in os.listdir(scripts_path()):
        detail={}
        detail["name"]=filename
        detail["mdate"]=datetime.fromtimestamp(os.path.getmtime(os.path.join(scripts_path(), filename))).strftime("%m/%d/%Y, %H:%M:%S")
        details.append(detail)
        

    return render_template("scripts.html", error_msg=error_msg, details=details, timestamp=datetime.now())
    

# get the last execution log for a script 
@app.route('/testtool_log', methods=['GET'])
def testtool_log():
    printlog("testtool_log")
    sys.stdout.flush()
    filename = request.args.get('filename')
    if filename == None:
        abort(400)
    payload = send_file(os.path.join(output_path(),filename), mimetype='text/plain')
    return payload, 200

# get the last screenshot for a step in a script
@app.route('/testtool_screenshot', methods=['GET'])
def testtool_screenshot():
    printlog("testtool_screenshot")
    sys.stdout.flush()
    script = request.args.get('script')
    if script == None:
        abort(400)
    image = request.args.get('image')
    if image == None:
        abort(400)

    payload = send_file(output_file(script,image), mimetype='image/png')
    return payload, 200


# ---------------- Helper functions ----------------

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'jar'}


def format_log(input):
    output="https://"
    return output

def printlog(content):
    print(datetime.now(),":",content)

def run_cmd(cmd, shell=""):
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            shell=False, stderr=subprocess.PIPE)
    if result.stderr:
        printlog('stderr:'+result.stderr.decode('utf-8'))
        return -1, result.stderr.decode('utf-8')
    if result.stdout:
        printlog("Command Result: {}".format(result.stdout.decode('utf-8')))
        return 0, result.stdout.decode('utf-8')
    else:
        return 0,"OK"

def run_cmd2(cmd, dt_client: Dynatrace, script, url):
    global mutex
    # make sure no other thread is running, otherwise wait
    # get exclusive token
    mutex.acquire()    
    
    try:
        result_file=output_file(script, "timings.txt")
        # try to figure out the frequency of execution
        # did we had previous results
        if not os.path.isfile(result_file):
            # no clue, let's guess it's 15 mn
            frequency=900
        else:
            last_time=os.path.getmtime(result_file)
            frequency=int(datetime.timestamp(datetime.now()) - last_time)
        # in case the test execution did not trigger for a long time (maybe because of a maintenance window), 
        # we may end up with a very big interval.
        # We must make sure the value does not exceed the max accepted by Dynatrace API
        frequency=min(frequency, 86400)

        # (re)create file to store timings
        f = open(result_file, "w")
        f.write("")
        f.close()
        
        
        log="OK"

        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE,
            shell=True, 
            stderr=subprocess.PIPE,
            env=os.environ
            )

        is_error=False
        if result.stderr:
            log=result.stderr.decode('utf-8')
            is_error=True
        if result.stdout:
            log=result.stdout.decode('utf-8')

            # remove specific errors we want to ignore :
            # this one because we start the bridge as a service and it has no access to local mouse, keyboard and screen.
            # But we don't mind because it will only interact with remote desktop through VNC connection.
            log_pattern="[error] Mouse: not useable (blocked)"
            if log_pattern in log:
                log=log.replace(log_pattern,"")
            # remaining error ?

            if '[error]' in log:
                is_error=True


        # save log on file
        log_file=output_file(script, "OUTPUT.log")
        f = open(log_file, "w")
        f.write(log)
        f.close()

        results_url=url+"testtool_execution_results?filename="+script

        # send results to Dynatrace with Synthetic third party API 
        process_third_party_results(script, result_file, log, results_url, dt_client, is_error, frequency)
    finally:
        # release token when processing done
        mutex.release()

def output_path():
    the_path=os.getenv('DT_BRIDGE_OUTPUT')
    if the_path is None:
        # set it to current directory
        the_path=os.path.abspath(os.getcwd())
    return the_path

def script_name(script):
    if script.endswith("_sikuli.jar"):
        script_name=os.path.basename(script).replace("_sikuli.jar","")
    else:
        script_name=os.path.basename(script).replace(".sikuli","")
    return script_name

def output_file(script, file):
    if not file:
        return os.path.join(output_path(),script_name(script))
    else:    
        return os.path.join(output_path(),script_name(script)+"_"+file)


def scripts_path():
    the_path=os.getenv('DT_BRIDGE_SCRIPTS')
    if the_path is None:
        # set it to current directory
        the_path=os.path.abspath(os.getcwd())
    return the_path


# ---------------- Main entry point ----------------

if __name__ == '__main__':
    # default port
    thePort = 5000

    if(len(sys.argv)>1):
        cmd=sys.argv[1]
    else:
        # default is to use Sikulix
        # note: first placeholder is the script name
        #       second placeholder is the function to execute
        cmd="java -jar sikulixide-2.0.5.jar -r {} --args \"{}\""
        # can be used also with other tools, like AutoIt : 
        # cmd="AutoIt3.exe {} {}"


    if(len(sys.argv)>2):
        try:
            thePort=int(sys.argv[2])
        except:
            thePort=5000
            
    printlog("using command line : "+cmd)
    #app.run(host='0.0.0.0', port=5000)
    app.run(host='0.0.0.0', port=thePort,ssl_context='adhoc')
