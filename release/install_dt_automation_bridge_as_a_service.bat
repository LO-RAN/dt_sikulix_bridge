rem installing dt_automation_bridge as a service with NSSM ( https://nssm.cc/ )
%~dp0nssm install dt_bridge %~dp0run_bridge.bat
%~dp0nssm set dt_bridge AppDirectory %~dp0
%~dp0nssm set dt_bridge DisplayName "Dynatrace automation bridge"
%~dp0nssm set dt_bridge Start SERVICE_AUTO_START 
%~dp0nssm set dt_bridge ObjectName LocalSystem 
%~dp0nssm reset dt_bridge ObjectName
%~dp0nssm set dt_bridge Type SERVICE_INTERACTIVE_PROCESS
%~dp0nssm set dt_bridge AppPriority NORMAL_PRIORITY_CLASS
%~dp0nssm set dt_bridge AppNoConsole 0
%~dp0nssm set dt_bridge AppAffinity All 
%~dp0nssm set dt_bridge AppRotateFiles 1
%~dp0nssm set dt_bridge AppRotateOnline 0
%~dp0nssm set dt_bridge AppRotateSeconds 86400
%~dp0nssm set dt_bridge AppRotateBytes 1048576
rem specify where to generate execution logs
%~dp0nssm set dt_bridge AppStdout c:\tmp\dt_bridge_out.log
%~dp0nssm set dt_bridge AppStderr c:\tmp\dt_bridge_err.log

rem start the service
%~dp0nssm start dt_bridge