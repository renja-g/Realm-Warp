# Use the official Python image as a parent image
FROM python:3.11

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV MONGO_URI="mongodb://mongodb:27017/realm_warm"

# Run app.py when the container launches
CMD ["python", "app.py"]
