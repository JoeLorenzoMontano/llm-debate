#!/bin/bash
# Start the LLM Debate Web UI

echo "Starting LLM Debate Web UI..."
echo "Access the UI at: http://localhost:8000"
echo ""

# Check if web requirements are installed
python3 -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing web dependencies..."
    pip3 install -r web/requirements.txt
fi

# Start the server
cd "$(dirname "$0")"
python3 -m uvicorn web.backend.main:app --host 0.0.0.0 --port 8000 --reload
