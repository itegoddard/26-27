@echo off
setlocal EnableDelayedExpansion

REM ===========================================================================
REM  Goddard 26-27 flight model launcher
REM
REM  Double-click for a menu, or run from cmd with an argument:
REM
REM      run.bat check              list unfilled register parameters
REM      run.bat sim                single flight, writes Excel + plots
REM      run.bat band               27-corner calibration sweep
REM      run.bat test               run the test suite
REM      run.bat show               open the last results
REM      run.bat setup              create .venv and install dependencies
REM      run.bat doctor             diagnose the environment
REM
REM  Runs the REAL vehicle (goddard_v1) by default. Override it with a
REM  second argument:
REM      run.bat sim goddard.config.demo_placeholder
REM
REM  Portability notes:
REM    - Works from any directory; cd's to its own folder first.
REM    - Tolerates spaces in the path.
REM    - Finds Python via the py launcher, python, or python3.
REM    - Installs into a project-local .venv, so it works on locked-down
REM      machines where global site-packages is read-only.
REM ===========================================================================

cd /d "%~dp0"
set "ROOT=%CD%"

set "CONFIG=goddard.config.goddard_v1"
set "OUT=out"
set "PAUSE_AT_END="
set "DEADREADS=0"
set "VENV=%ROOT%\.venv"
set "VENV_PY=%VENV%\Scripts\python.exe"

REM ------------------------------------------------- is this the project root
if not exist "%ROOT%\pyproject.toml" goto :not_project
if not exist "%ROOT%\goddard\cli.py" goto :not_project

REM ------------------------------------------------------------------ dispatch
if "%~1"=="" (
    set "PAUSE_AT_END=1"
    goto :menu
)
set "ACTION=%~1"
if not "%~2"=="" set "CONFIG=%~2"
goto :dispatch


:menu
echo.
echo   ========================================================
echo     Goddard 26-27 Flight Model
echo   ========================================================
echo.
if not exist "%VENV_PY%" (
    echo     [ First run? Choose 6 to set up. ]
    echo.
)
echo     1.  Check      - what still needs filling in
echo     2.  Simulate   - one flight, writes Excel + plots
echo     3.  Band       - 27-corner calibration sweep
echo     4.  Show       - open the last results
echo     5.  Test       - run the test suite
echo     6.  Setup      - create .venv and install dependencies
echo     7.  Doctor     - diagnose the environment
echo     8.  Equations  - validate every equation, open the PDF
echo     9.  Exit
echo.
set "ACTION="
set "PICK="
set /p "PICK=  Choose 1-9: "

REM Guard against a closed or redirected stdin: set /p leaves PICK untouched at
REM EOF, which would spin this menu forever. Bail out after a few dead reads.
if "!PICK!"=="" (
    set /a DEADREADS+=1
    if !DEADREADS! GEQ 5 goto :quit
    goto :menu
)
set "DEADREADS=0"

if "!PICK!"=="1" set "ACTION=check"
if "!PICK!"=="2" set "ACTION=sim"
if "!PICK!"=="3" set "ACTION=band"
if "!PICK!"=="4" set "ACTION=show"
if "!PICK!"=="5" set "ACTION=test"
if "!PICK!"=="6" set "ACTION=setup"
if "!PICK!"=="7" set "ACTION=doctor"
if "!PICK!"=="8" set "ACTION=equations"
if "!PICK!"=="9" goto :quit
if "!ACTION!"=="" (
    echo   Not a valid choice.
    goto :menu
)


:dispatch
echo.
if /i "%ACTION%"=="setup"  goto :do_setup
if /i "%ACTION%"=="doctor" goto :do_doctor

REM Everything else needs a working interpreter.
call :resolve_python
if not defined PY goto :no_python

if /i "%ACTION%"=="check" goto :do_check
if /i "%ACTION%"=="sim"   goto :do_sim
if /i "%ACTION%"=="run"   goto :do_sim
if /i "%ACTION%"=="band"  goto :do_band
if /i "%ACTION%"=="show"  goto :do_show
if /i "%ACTION%"=="open"  goto :do_show
if /i "%ACTION%"=="test"  goto :do_test
if /i "%ACTION%"=="equations" goto :do_equations

echo   Unknown command: %ACTION%
echo   Try: check ^| sim ^| band ^| show ^| test ^| setup ^| doctor ^| equations
goto :end


:do_equations
echo   Validating every equation in docs\equations.tex against an
echo   independent derivation...
echo.
%PY% tools\validate_equations.py
if errorlevel 1 (
    echo.
    echo   One or more equations did not validate. Scroll up.
    goto :end
)
echo.
if exist "docs\equations.pdf" (
    echo   Opening docs\equations.pdf ...
    start "" "docs\equations.pdf"
) else (
    echo   docs\equations.pdf not found. Rebuild it with:
    echo       pdflatex -output-directory=docs docs\equations.tex
)
goto :end


REM =========================================================== python plumbing

REM Prefer the project venv. Otherwise find any usable system Python.
REM PY is stored WITH quotes when it is a path, so it expands safely unquoted.
:resolve_python
set "PY="
if exist "%VENV_PY%" (
    set PY="%VENV_PY%"
    exit /b 0
)
call :find_system_python
if defined BOOTPY set "PY=%BOOTPY%"
exit /b 0

:find_system_python
set "BOOTPY="
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "BOOTPY=py -3"
    exit /b 0
)
python -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "BOOTPY=python"
    exit /b 0
)
python3 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "BOOTPY=python3"
    exit /b 0
)
exit /b 1


REM ================================================================== commands

:do_setup
echo   Setting up the Goddard model environment.
echo.
call :find_system_python
if not defined BOOTPY goto :no_python

echo   Using system Python: %BOOTPY%
%BOOTPY% -c "import sys; print('   version', sys.version.split()[0])"
echo.

if exist "%VENV_PY%" (
    echo   Virtual environment already exists at .venv
) else (
    echo   Creating virtual environment in .venv  ^(one time, ~15 s^)...
    %BOOTPY% -m venv "%VENV%"
    if errorlevel 1 (
        echo.
        echo   Could not create the virtual environment.
        echo   On some systems you may need:  %BOOTPY% -m pip install virtualenv
        goto :failed
    )
)

if not exist "%VENV_PY%" (
    echo   Virtual environment looks incomplete. Delete the .venv folder and retry.
    goto :failed
)

echo.
echo   Installing dependencies into .venv ...
echo.
"%VENV_PY%" -m pip install --quiet --upgrade pip setuptools wheel
"%VENV_PY%" -m pip install -e ".[dev,report]"
if errorlevel 1 goto :failed

echo.
echo   Verifying...
"%VENV_PY%" -c "import goddard, openpyxl, matplotlib; print('   goddard', goddard.__version__, '- openpyxl and matplotlib OK')"
if errorlevel 1 goto :failed

echo.
echo   Setup complete. Choose option 2 to run a flight.
goto :end


:do_doctor
echo   Environment diagnosis
echo   ---------------------
echo   Project root : %ROOT%
if exist "%ROOT%\pyproject.toml" (echo   pyproject    : found) else (echo   pyproject    : MISSING)
if exist "%ROOT%\goddard\cli.py" (echo   goddard pkg  : found) else (echo   goddard pkg  : MISSING)
if exist "%VENV_PY%" (echo   .venv        : found) else (echo   .venv        : not created - run option 6)
echo.
call :find_system_python
if defined BOOTPY (
    echo   System Python: %BOOTPY%
    %BOOTPY% -c "import sys; print('   version      :', sys.version.split()[0]); print('   executable   :', sys.executable)"
) else (
    echo   System Python: NOT FOUND on PATH
)
echo.
if exist "%VENV_PY%" (
    echo   Packages in .venv:
    "%VENV_PY%" -c "import importlib;[print('    ',n,'OK' if importlib.util.find_spec(n) else 'MISSING') for n in ('goddard','openpyxl','matplotlib','pytest')]"
)
goto :end


:do_check
echo   Listing register parameters that are still OPEN...
echo.
%PY% -m goddard.cli check
goto :end


:do_sim
call :warn_if_demo
echo   Running a single flight with config: %CONFIG%
echo.
%PY% -m goddard.cli run --config %CONFIG% --out "%OUT%"
if errorlevel 1 goto :failed
echo.
echo   Opening results...
if exist "%OUT%\goddard_results.xlsx" start "" "%OUT%\goddard_results.xlsx"
if exist "%OUT%\plots" start "" "%OUT%\plots"
goto :end


:do_band
call :warn_if_demo
echo   Sweeping the three unmeasured constants over 27 corners.
echo   This takes about a minute.
echo.
%PY% -m goddard.cli band --config %CONFIG% --out "%OUT%"
if errorlevel 1 goto :failed
echo.
if exist "%OUT%" start "" "%OUT%"
goto :end


:do_show
if not exist "%OUT%\goddard_results.xlsx" (
    echo   No results yet. Run option 2 first.
    goto :end
)
start "" "%OUT%\goddard_results.xlsx"
if exist "%OUT%\plots" start "" "%OUT%\plots"
echo   Opened %OUT%.
goto :end


:do_test
echo   Running the test suite...
echo.
%PY% -m pytest -q
goto :end


REM =================================================================== notices

:warn_if_demo
if /i "%CONFIG%"=="goddard.config.demo_placeholder" goto :warn_demo
if /i "%CONFIG%"=="goddard.config.goddard_v1" goto :warn_v1
exit /b 0

:warn_demo
echo   ------------------------------------------------------------
echo    WARNING: using the DEMO config. Every number in it is made
echo    up. The results show that the model runs - they are NOT a
echo    prediction and must not be quoted.
echo.
echo    The real vehicle is goddard.config.goddard_v1, which is now
echo    the default. You have gone out of your way to get here.
echo   ------------------------------------------------------------
echo.
exit /b 0

:warn_v1
echo   ------------------------------------------------------------
echo    Running the REAL vehicle: goddard_v1
echo.
echo    Airframe, motor and trajectory run on confirmed numbers.
echo    Five values are still provisional and do affect the result:
echo.
echo       nose tip mass           injector plate thickness
echo       launch rail length      mean wind speed
echo       surface roughness
echo.
echo    Recovery is solved from a 3.5 kN opening-load limit, which is
echo    itself pending a pull test on the real bulkhead assembly.
echo.
echo    Apogee is reported with the vapour tail TRUNCATED at liquid
echo    depletion - the conservative choice, matching the working
echo    model. Retaining the tail would read higher, but its c* is
echo    not valid once no fuel is burning.
echo.
echo    ONE PLACEHOLDER remains: the N2O latent heat is an unverified
echo    stand-in ^(register D12^). It sets tank chilling, hence thrust
echo    taper and burn time, so it touches everything downstream.
echo.
echo    Supersonic wave drag is UNVALIDATED and runs high through the
echo    transonic. It is the largest known model error.
echo.
echo    Constraints are printed after every run and written to the
echo    Constraints sheet. Full picture: docs\STATUS.md
echo   ------------------------------------------------------------
echo.
exit /b 0


:not_project
echo.
echo   ============================================================
echo    run.bat is not inside the project folder.
echo   ============================================================
echo.
echo    It is currently in:
echo      %ROOT%
echo.
echo    but there is no pyproject.toml or goddard\ package here.
echo.
echo    This usually means only run.bat was downloaded, instead of
echo    the whole repository. Get the full project:
echo.
echo      git clone https://github.com/itegoddard/26-27.git
echo      cd 26-27
echo      run.bat
echo.
echo    Or on GitHub use  Code -^> Download ZIP,  extract it, and
echo    run run.bat from inside the extracted folder.
echo.
goto :hard_end


:no_python
echo.
echo   ============================================================
echo    Python was not found.
echo   ============================================================
echo.
echo    Tried: py -3, python, python3 - none responded.
echo.
echo    Install Python 3.10 or newer from https://python.org/downloads
echo    and tick "Add python.exe to PATH" during installation.
echo.
echo    Then reopen this window and choose option 6 ^(Setup^).
echo.
goto :end


:failed
echo.
echo   Command failed. Scroll up for the error.
echo   Option 7 ^(Doctor^) will diagnose the environment.


REM ------------------------------------------------------------------ endings
REM In menu mode return to the menu so several actions can be run in one
REM session -- Setup then Simulate is the common pair, and closing the window
REM in between would mean relaunching. Only option 8 exits.
REM With a command-line argument, run once and exit so scripting still works.

:end
echo.
if not defined PAUSE_AT_END goto :quit
echo   ------------------------------------------------------------
pause
goto :menu

:hard_end
echo.
pause
goto :quit

:quit
endlocal
exit /b 0
