@echo off

set /p SECRET_NAME_INPUT=Enter the secret name: 
set /p SECRET_KEY=Enter the secret key: 
set /p SECRET_VALUE=Enter the secret value: 

REM Get the current date and time in the format YYYYMMDD-HHMMSS
for /f "tokens=1-6 delims=/:. " %%A in ("%DATE% %TIME%") do (
    set TIMESTAMP=%%D%%C%%B-%%E%%F%%G
)

REM Set the secret name with the current date and time appended
set SECRET_NAME=%SECRET_NAME_INPUT%_%TIMESTAMP%



kubectl create secret generic %SECRET_NAME% --from-literal=%SECRET_KEY%=%SECRET_VALUE%
