#!/bin/bash
# installing dt_automation_bridge as a service
# create the service definition
sudo cat > /etc/systemd/system/dt_automation_bridge.service << EOF
[Unit]
Description=Dynatrace Automation Bridge

[Service]
User=lizac
WorkingDirectory=/home/lizac/projects/Python/dt_sikulix_bridge/release
ExecStart=/home/lizac/projects/Python/dt_sikulix_bridge/release/run_bridge.sh
StandardOutput=file:/tmp/dt_automation_bridge_output.log
StandardError=file:/tmp/dt_automation_bridge_error.log
Restart=always

[Install]
WantedBy=multi-user.target
EOF
# Reload the service files to include the new service
sudo systemctl daemon-reload
# enable your service on every reboot
sudo systemctl enable dt_automation_bridge.service
# start the service
sudo systemctl start dt_automation_bridge.service
