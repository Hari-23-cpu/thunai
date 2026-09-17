@echo off
start "Thunai Backend" cmd /k "cd /d C:\Users\krish\Downloads\Thunai && uvicorn backend.api:app --reload"
start "Thunai Frontend" cmd /k "cd /d C:\Users\krish\Downloads\Thunai\frontend && npm run dev"