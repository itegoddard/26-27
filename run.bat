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
REM      run.bat setup              install dependencies
REM
REM  Optional second argument overrides the config module:
REM      run.bat sim goddard.config.goddard_v2
REM ===========================================================================

REM Work from the script's own folder so the space in the path never matters.
cd /d "%~dp0"

set "CONFIG=goddard.config.demo_placeholder"
set "OUT=out"
set "PAUSE_AT_END="

REM ---------------------------------------------------------------- python
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: python was not found on your PATH.
    echo   Install Python 3.10 or newer and tick "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

REM ---------------------------------------------------------------- dispatch
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
echo     1.  Check      - what still needs filling in
echo     2.  Simulate   - one flight, writes Excel + plots
echo     3.  Band       - 27-corner calibration sweep
echo     4.  Show       - open the last results
echo     5.  Test       - run the test suite
echo     6.  Setup      - install dependencies
echo     7.  Exit
echo.
set "ACTION="
set /p "PICK=  Choose 1-7: "
if "%PICK%"=="1" set "ACTION=check"
if "%PICK%"=="2" set "ACTION=sim"
if "%PICK%"=="3" set "ACTION=band"
if "%PICK%"=="4" set "ACTION=show"
if "%PICK%"=="5" set "ACTION=test"
if "%PICK%"=="6" set "ACTION=setup"
if "%PICK%"=="7" exit /b 0
if "!ACTION!"=="" (
    echo   Not a valid choice.
    goto :menu
)


:dispatch
echo.
if /i "%ACTION%"=="check" goto :do_check
if /i "%ACTION%"=="sim"   goto :do_sim
if /i "%ACTION%"=="run"   goto :do_sim
if /i "%ACTION%"=="band"  goto :do_band
if /i "%ACTION%"=="show"  goto :do_show
if /i "%ACTION%"=="open"  goto :do_show
if /i "%ACTION%"=="test"  goto :do_test
if /i "%ACTION%"=="setup" goto :do_setup

echo   Unknown command: %ACTION%
echo   Try: check ^| sim ^| band ^| show ^| test ^| setup
goto :end


:do_check
echo   Listing register parameters that are still OPEN...
echo.
python -m goddard.cli check
goto :end


:do_sim
call :warn_if_demo
echo   Running a single flight with config: %CONFIG%
echo.
python -m goddard.cli run --config %CONFIG% --out "%OUT%"
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
python -m goddard.cli band --config %CONFIG% --out "%OUT%"
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
python -m pytest -q
goto :end


:do_setup
echo   Installing dependencies...
echo.
python -m pip install -e ".[dev,report]"
if errorlevel 1 goto :failed
echo.
echo   Done. Try option 1 next.
goto :end


:warn_if_demo
if /i not "%CONFIG%"=="goddard.config.demo_placeholder" exit /b 0
echo   ------------------------------------------------------------
echo    WARNING: using the DEMO config. Every number in it is made
echo    up. The results show that the model runs - they are NOT a
echo    prediction and must not be quoted.
echo.
echo    Real values are the OPEN entries in
echo    docs\assumptions_register.md  (see option 1).
echo   ------------------------------------------------------------
echo.
exit /b 0


:failed
echo.
echo   Command failed. Scroll up for the error.
echo   If a module is missing, try option 6 (Setup).


:end
echo.
if defined PAUSE_AT_END pause
endlocal
exit /b 0
