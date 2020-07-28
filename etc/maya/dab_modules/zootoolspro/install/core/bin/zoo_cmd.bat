
@echo off
set ZOO_CORE_TEMP=%~dp0..\
if "%ZOOTOOLS_ROOT%" == "" (

    set ZOOTOOLS_ROOT=%~dp0..\
) else (
    echo Custom Zootools root specified %ZOOTOOLS_ROOT%
)
if "%ZOO_PYTHON_INTERPRETER%" == "" (
    set ZOO_PYTHON_INTERPRETER="python"
) else (
    echo Custom python interpreter specified %ZOO_PYTHON_INTERPRETER%
)

if EXIST "%ZOO_CORE_TEMP%\scripts\zoo_cmd.py" (
    REM echo "calling %ZOO_CORE_TEMP%\scripts\zoo_cmd.py"
    %ZOO_PYTHON_INTERPRETER% "%ZOO_CORE_TEMP%\scripts\zoo_cmd.py" %*
) else (
    REM echo "calling %ZOO_CORE_TEMP%\scripts\zoo_cmd.pyc"
    %ZOO_PYTHON_INTERPRETER% "%ZOO_CORE_TEMP%\scripts\zoo_cmd.pyc" %*
)

exit /b 1