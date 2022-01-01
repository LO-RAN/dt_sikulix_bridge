#!/bin/bash

cd ../src
pyinstaller -F --add-data "templates:templates" --add-data "static:static"  --distpath ../release/ dt_automation_bridge.py
# copy python utilities (timing decorator and vnc connection helpers)
# Note: see src/README_dtbridge_sikulix.txt for how this jar file was creaed
copy $PWD/dtbridge_sikuli.jar ../release/
# copy SikuliX jar from official web site (as it is too big to be commited to GIT)
cp $PWD/dtbridge_sikuli.jar ../release/
wget -O ../release/sikulixide-2.0.5.jar https://launchpad.net/sikuli/sikulix/2.0.5/+download/sikulixide-2.0.5.jar
cd ../make