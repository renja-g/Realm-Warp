# Use an official Python image as the base image
FROM python:3.11-alpine as base

# Set the working directory within the container
WORKDIR /app

# Copy only the requirements file to leverage Docker cache
COPY ./services/tracker/requirements.txt /app/tracker/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/tracker/requirements.txt

# Copy the application code and environment file
COPY ./services/tracker /app/tracker
COPY ./utils /app/utils
COPY ./.env /app/

# Define the default command to run the application
CMD ["python", "-m", "tracker.tracker"]
