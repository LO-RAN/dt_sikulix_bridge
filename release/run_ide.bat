@echo off
rem cd dist
echo adding the path to the Java runtime included in the Dynatrace ActiveGate distribution
set PATH="c:\Program Files\dynatrace\gateway\jre\bin";%PATH%

rem where to generate timings and screenshots upon script execution
set DT_BRIDGE_OUTPUT=c:\tmp\sikulix

echo launching IDE
call java -jar sikulixide-2.0.5.jar
