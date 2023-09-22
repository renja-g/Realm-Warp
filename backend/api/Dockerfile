# Use the official Python image as a parent image
FROM python:3.11-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY /api .
COPY ./requirements.txt .

# Install any needed packages specified in ../requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV MONGO_URI="mongodb://mongodb:27017/realm_warm"

# Run app.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
