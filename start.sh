#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Flask application...${NC}"

# Start the Flask app in the background
python3 app.py &

# Store the process ID
FLASK_PID=$!

# Wait a bit for Flask to start up
sleep 2

# Check if the server is running
if curl -s http://localhost:5000 > /dev/null; then
    echo -e "${GREEN}Flask server is running!${NC}"
    
    # Open in default browser based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open http://localhost:5000
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open http://localhost:5000
    else
        # Windows
        start http://localhost:5000
    fi
else
    echo -e "${RED}Failed to start Flask server${NC}"
    kill $FLASK_PID
    exit 1
fi

# Keep script running and handle cleanup on Ctrl+C
trap "echo -e '\n${RED}Shutting down Flask server...${NC}'; kill $FLASK_PID; exit" INT
wait $FLASK_PID 
