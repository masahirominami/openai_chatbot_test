# Use an official Python runtime as the base image
FROM python:3.9-slim-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y wget gnupg curl

# Install MongoDB
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-4.4.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-4.4.gpg
RUN echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-4.4.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-4.4.list
# RUN echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-4.4.gpg] http://repo.mongodb.org/apt/debian bullseye/mongodb-org/4.4 main" | tee /etc/apt/sources.list.d/mongodb-org-4.4.list
RUN apt-get update && apt-get install -y mongodb-org

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Copy .env file
COPY .env /app/.env

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available for the FastAPI app
EXPOSE 8000

# Make port 27017 available for MongoDB
EXPOSE 27017

# Define environment variable for OpenAI API key
ENV OPENAI_API_KEY=your_openai_api_key_here

# Create a directory for MongoDB data
RUN mkdir -p /data/db

# Create a start script
RUN echo "#!/bin/bash\nmongod --fork --logpath /var/log/mongod.log --bind_ip_all\nuvicorn app.main:app --host 0.0.0.0 --port 8000" > /app/start.sh
RUN chmod +x /app/start.sh

# Run the start script
CMD ["/app/start.sh"]
