param([int]$Port = 8000)

$ErrorActionPreference = 'Stop'
python -m uvicorn backend.app:app --host 127.0.0.1 --port $Port
