#!/bin/bash

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker before running this script."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose is not installed. Please install docker-compose before running this script."
    exit 1
fi

# Navigate to the directory containing your docker-compose.yml file
cd /path/to/your/docker-compose-directory

# Start the containers using docker-compose
docker-compose up -d

# Optionally, you can add more commands or instructions here
# For example, you might want to display a message after starting the containers
echo "Docker containers started successfully!"
