#!/bin/bash
echo ""
echo "=========================================="
echo "  ElectroSolar Manager - Starting..."
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Install from https://python.org"
    exit 1
fi

echo "Installing/checking dependencies..."
pip3 install -r requirements.txt -q

echo ""
echo "Starting server..."
echo "Open your browser at: http://localhost:5000"
echo "Login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop."
echo ""
python3 app.py
