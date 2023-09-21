# Use a Node.js LTS image as a parent image
FROM node:lts

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install Node.js dependencies
RUN npm install

# Build the Svelte application
RUN npm run build

# Expose port 5000 to the world outside this container
EXPOSE 5000

# Start the Svelte application
CMD ["npm", "start"]
