# import the Dynatrace Bridge features
load("dtbridge_sikuli.jar")
from dtbridge import *

#-----------------------------------------------------------------------------------------
@dt_get_timings
def open_session():
    if(exists("PressCtrlAlt.png")):
        dt_vnc_send_ctrl_alt_del()
    
        wait(2)            
    if(exists("password_field.png")):     
        type("<REPLACE WITH YOUR ACTUAL WINDOWS SESSION PASSWORD>")
        type(Key.ENTER)
        wait(2)      

#-----------------------------------------------------------------------------------------
@dt_get_timings
def close_session():
    # lock the session when finished
    dt_vnc_send_ctrl_alt_del()
    click(wait("Signout-1.png",5))

#-----------------------------------------------------------------------------------------
@dt_get_timings
def open_calc():
    # minimize all open windows  
    type("M", Key.WIN)
    wait(5)    
    # start calculator App
    click("windows_logo.png")
    wait(5)
    type("calc")
    wait(2)
    type(Key.ENTER)
    # wait for the app to start
    wait("flCalcul.png",5)

#-----------------------------------------------------------------------------------------
@dt_get_timings
def calc1():
    # interact with the mouse
    click("eight_digit.png")
    click("multiply.png")
    click("seven_digit.png")
    click("equal_sign.png")
    wait(1)
    # check result
    wait("expected_56.png",1)
    
#-----------------------------------------------------------------------------------------
@dt_get_timings
def calc2(entry):
    # interact with key strokes
    type(entry+Key.ENTER)
    # check result
    wait("expected_1dot2.png",1)

#-----------------------------------------------------------------------------------------
@dt_get_timings
def close_calc():
    # close the app
#    type(Key.F4, Key.ALT);
    click("window_close.png")

#-----------------------------------------------------------------------------------------
if __name__ == '__main__':
   # build a list of passed parameters 
   args=dt_get_args(sys.argv)
   vs=dt_vnc_connect("<REPLACE WITH YOUR ACTUAL VNC SERVER>", <PORT>, "<PASSWORD>")  
   # make it the default screen for the following commands
   use(vs)                  
   try:         
       open_session()
       open_calc()
       calc1()   
       if 'param1' in args:
           calc2(args['param1'])
       else:
           calc2("6/5")
       close_calc()
       close_session()
   finally:    
       dt_vnc_disconnect()
       # revert to default local screen
       use()