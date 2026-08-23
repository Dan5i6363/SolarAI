$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (!(Test-Path '.venv\Scripts\python.exe')) { throw 'Virtual environment missing.' }
if (!(Test-Path 'models\pv_condition_classifier.pt')) { & .\.venv\Scripts\python.exe -m ai.train --epochs 180 --seed 42 }
if (Get-Process streamlit -ErrorAction SilentlyContinue) { Write-Host 'A Streamlit process is already running.'; exit 0 }
& .\.venv\Scripts\streamlit.exe run dashboard\app.py
