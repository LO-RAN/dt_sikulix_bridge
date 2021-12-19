import os
import sys
import shutil
import time
from datetime import datetime
import json
from sikuli import *
# ---- trick using TigerVNC java code
import com.tigervnc.rfb.CMsgWriterV3
import com.tigervnc.rfb.Keysyms as Keysyms
import org.sikuli.vnc.VNCScreen as VNCScreen
import com.tigervnc.vncviewer.UserPreferences as Pref
vs=None
step_id=0

# decorator to retrieve function execution timings and error context (log & screenshot)
# this script is intended to be used from a SikuliX python script
# by importing the "get_timings" decorator function like so :
#    from dtbridge import get_timings
# and decorating the functions to monitor like so :
#    @get_timings
#    def my_fonction(param1, ..., param n):
def dt_get_timings(func):
    def wrapper(*args, **kwargs):
        global step_id
        Settings.UserLogPrefix = "dtbridge"
        Settings.UserLogTime = True        

        the_path=os.getenv('DT_BRIDGE_OUTPUT')
        
        Debug.user(func.__name__)
        
        try:
            error = False
            errmsg = ""
            # start timer
            ts = time.time()
            # call function
            result = func(*args, **kwargs)

            return result
        except (FindFailed, Exception), e:
            error = True
            errmsg = str(e)          
            print("[error] "+errmsg)
        finally:
            # stop timer
            te = time.time()

            # take screenshot after step completion
            if vs is not None:    
                image = vs.capture(SCREEN).save()
            else:
                image = capture(SCREEN)

            screenshot="SCREENSHOT_"+func.__name__+".png"
            
            imagepath=output_path(screenshot)
            resultpath=output_path("timings.txt")
            
            # save screenshot on disk    
            shutil.move(image, imagepath)
            
            # build results
            data = {'id': step_id, 'title': func.__name__, 'startTimestamp': int(round(ts*1000)), 'responseTimeMillis': int(round((te - ts)*1000)), 'screenshot': screenshot}
            if error:
                data['error'] = {
                    "code": 1,
                    "message": errmsg
                }

            step_id +=1
            
            # save results to file

            timerfile = open(resultpath, 'a')
            json.dump(data, timerfile)
            timerfile.write("\n")
            timerfile.close()

            if error:
                raise
            
    return wrapper


# convert command line arguments to a dict with key-value pairs
def dt_get_args(arguments):
    args= {}
    for arg in arguments:
        if "=" in arg:
            key, val = arg.split('=')
        else:
            key = arg
            val = arg
        args[key] = val

        print(str(args))
    return args


def output_path(file):
    script=os.path.realpath(sys.argv[0])
    the_path=os.getenv('DT_BRIDGE_OUTPUT')
    
    if the_path is None:
        # set it to current directory
        the_path=os.path.abspath(os.getcwd())

    # are we dealing with the compiled jar file ? 
    if script.endswith("$py.class"):
        script_name=os.path.basename(script).replace("$py.class","")
    else:
        script_name=os.path.basename(script).replace(".py","")

    return os.path.join(the_path,script_name+"_"+file)


# open VNC connection
def dt_vnc_connect(host, port=5900, pwd='dynatrace'):
    global vs
    vs = VNCScreen.start(host, port, pwd, 10, 1000)
    
    if not vs:    
       print("Error connecting to VNC")
       exit(-1)


    Pref.set("global", "AcceptClipboard", True)
    Pref.set("global", "SendClipboard", True)
    
    return vs

# send CTRL+ALT+DEL over the VNC connection
def dt_vnc_send_ctrl_alt_del(vs):
    if vs:    
        cc = vs.getClient().writer()
        cc.writeKeyEvent(Keysyms.Control_L, True)
        cc.writeKeyEvent(Keysyms.Alt_L, True)
        cc.writeKeyEvent(Keysyms.Delete, True)
        cc.writeKeyEvent(Keysyms.Delete, False)
        cc.writeKeyEvent(Keysyms.Alt_L, False)
        cc.writeKeyEvent(Keysyms.Control_L, False)
    else:
        print("No VNC Screen to interact with")

 