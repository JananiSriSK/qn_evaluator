@echo off
echo Starting Question Intelligence System Backend...
cd /d "c:\Users\Jananisri\Desktop\study\mcanotes\SEM_4_Project\qn_evaluator\backend"

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing/updating dependencies...
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo Starting server...
python main.py

pause