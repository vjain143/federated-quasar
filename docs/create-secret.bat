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

@echo off
setlocal EnableDelayedExpansion

echo Select an environment:
echo 1. Development
echo 2. Testing
echo 3. Production
set /p ENV_CHOICE=Enter your choice (1-3): 

if "%ENV_CHOICE%"=="1" (
    set "ENVIRONMENT=Development"
) else if "%ENV_CHOICE%"=="2" (
    set "ENVIRONMENT=Testing"
) else if "%ENV_CHOICE%"=="3" (
    set "ENVIRONMENT=Production"
) else (
    echo Invalid choice. Exiting.
    exit /b 1
)

echo Setting environment to: %ENVIRONMENT%
set "ENV_VAR_NAME=MY_ENVIRONMENT"
setx %ENV_VAR_NAME% "%ENVIRONMENT%" /M

echo Environment variable %ENV_VAR_NAME% set to %ENVIRONMENT%.

endlocal


kubectl create secret generic %SECRET_NAME% --from-literal=%SECRET_KEY%=%SECRET_VALUE%
