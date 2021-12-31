# dt_sikulix_bridge
a bridge between Dynatrace Synthetic and SikuliX GUI tests

## Build the dependencies
```
cd src
python -m venv env
.\env\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
cd ..
```
## Build the bridge executable 
```
cd make
.\build_bridge.bat
cd ..
```
## Deploy

1. copy the contents of "release\" folder to target host.
2. edit and review "run_bridge.bat" (adjust paths and port as required).
3. edit and review "install_dt_automation_bridge_as_a_service.bat" (adjust paths as required).
4. run "install_dt_automation_bridge_as_a_service.bat" to install the bridge as a service.

