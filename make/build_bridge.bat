cd ..\src
pyinstaller -F --add-data "templates;templates" --add-data "static;static"  --distpath ..\release\ dt_automation_bridge.py
rem copy python utilities (timing decorator and vnc connection helpers)
rem Note: see src/README_dtbridge_sikulix.txt for how this jar file was creaed
copy dtbridge_sikuli.jar ..\release\
rem copy SikuliX jar from official web site (as it is too big to be commited to GIT)
powershell (new-object System.Net.WebClient).DownloadFile('https://launchpad.net/sikuli/sikulix/2.0.5/+download/sikulixide-2.0.5.jar','..\release\sikulixide-2.0.5.jar')
cd ..\make
