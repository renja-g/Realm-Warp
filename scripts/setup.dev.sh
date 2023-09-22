#!/bin/bash

# Start MongoDB Docker container
docker-compose up -d mongodb

# Install frontend dependencies
cd frontend
npm install
cd ..

# Install backend Python dependencies in a virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..