#!/bin/sh
# Railway startup script that properly handles PORT variable
exec uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
