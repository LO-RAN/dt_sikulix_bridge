@echo off
echo adding the path to the Java runtime included in the Dynatrace ActiveGate distribution
set PATH="c:\Program Files\dynatrace\gateway\jre\bin";%PATH%


rem default is to use SikuliX if no parameter is provided on the command line
rem note: first placeholder is the script name
rem       second placeholder is the function to execute
set CMD="java -jar sikulixide-2.0.5.jar -r {} --args \"{}\""
rem  but can be used also with other tools, like AutoIt : 
rem  set CMD="AutoIt3.exe {} {}"

rem where to generate timings and screenshots upon script execution
set DT_BRIDGE_OUTPUT=c:\tmp

echo launching bridge 
rem first parameter is the command to execute (defaults to SikuliX...)
rem second prameter is the listening port (defaults to 5000)
call dt_automation_bridge.exe %CMD% 5000
