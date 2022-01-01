#!/bin/bash

echo adding the path to the Java runtime included in the Dynatrace ActiveGate distribution
export PATH="/opt/dynatrace/gateway/jre/bin":$PATH
export JAVA_HOME=/opt/dynatrace/gateway/jre

# default is to use SikuliX if no parameter is provided on the command line
# note: first placeholder is the script name
#       second placeholder is the function to execute

export CMD="\"$JAVA_HOME/bin/java\" -jar \"$PWD/sikulixide-2.0.5.jar\" -r {} --args \"{}\""

# where to generate timings and screenshots upon script execution
export DT_BRIDGE_OUTPUT=/tmp

# where to look for scripts to execute
export DT_BRIDGE_SCRIPTS=$PWD/scripts

echo launching bridge
# first parameter is the command to execute (defaults to SikuliX...)
# second prameter is the listening port (defaults to 5000)
$PWD/dt_automation_bridge "$CMD" 5000
