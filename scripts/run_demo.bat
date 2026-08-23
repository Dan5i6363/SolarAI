@echo off
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (echo Virtual environment missing.& exit /b 1)
if not exist "models\pv_condition_classifier.pt" .venv\Scripts\python.exe -m ai.train --epochs 180 --seed 42
tasklist /FI "IMAGENAME eq streamlit.exe" 2>NUL | find /I "streamlit.exe" >NUL && (echo Streamlit is already running.& exit /b 0)
.venv\Scripts\streamlit.exe run dashboard\app.py
