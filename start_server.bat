@echo off
REM Start Company Validation API Server

echo ==================================
echo Company Validation API Server
echo ==================================
echo.

REM Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found
    echo    Create .env file with required API keys
    echo.
)

REM Check if dependencies are installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Start server
echo Starting server on http://localhost:8003
echo API Docs: http://localhost:8003/docs
echo Health Check: http://localhost:8003/health
echo.
echo Press Ctrl+C to stop
echo.

python api_server.py
