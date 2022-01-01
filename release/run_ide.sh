#!/bin/bash

echo adding the path to the Java runtime included in the Dynatrace ActiveGate distribution
export PATH="/opt/dynatrace/gateway/jre/bin":$PATH

# where to generate timings and screenshots upon script execution
export DT_BRIDGE_OUTPUT=/tmp

echo launching IDE
java -jar $PWD/sikulixide-2.0.5.jar
