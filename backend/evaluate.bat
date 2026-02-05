@echo off
echo Question Intelligence System - CLI Evaluation
echo ============================================

if "%1"=="" (
    echo Usage: evaluate.bat "COURSE_NAME" [options]
    echo.
    echo Options:
    echo   -d, --details    Show detailed test results
    echo   -a, --all        Show all test results including passed
    echo.
    echo Example: evaluate.bat "INTRODUCTION TO OPERATING SYSTEM" -d
    pause
    exit /b 1
)

echo Running evaluation for course: %1
echo.

cd /d "%~dp0"
python evaluate_simple.py %*

echo.
echo Evaluation completed. Press any key to exit.
pause > nul