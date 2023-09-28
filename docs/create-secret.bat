@echo off
set /p SECRET_NAME=Enter the secret name: 
set /p SECRET_KEY=Enter the secret key: 
set /p SECRET_VALUE=Enter the secret value: 

kubectl create secret generic %SECRET_NAME% --from-literal=%SECRET_KEY%=%SECRET_VALUE%
