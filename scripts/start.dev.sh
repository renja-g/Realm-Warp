#!/bin/bash

# Start the backend server
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 &
deactivate
cd ..

# Start the frontend server
cd frontend
npm run dev &
cd ..

echo "Development environment is running. Press Ctrl+C to stop."
# Wait for Ctrl+C to stop the environment
trap "exit" INT
wait