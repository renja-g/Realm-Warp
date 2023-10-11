#!/bin/bash

# Start MongoDB Docker container
docker-compose up -d mongodb

# Install frontend dependencies
cd frontend || exit
npm install
cd ..

# Install backend API dependencies
cd backend/api || exit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..

# Install backend Tracker service dependencies
cd backend/services/tracker || exit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../../..