@echo off
echo Starting IEEE 738 Dynamic Line Rating API Server...
echo.
echo Server will be available at:
echo   - http://localhost:8000
echo   - Swagger Docs: http://localhost:8000/docs
echo.
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
