# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
# This leverages Docker's layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY ./line_server ./line_server

# Expose the port the app runs on
EXPOSE 8000

# The command to run the application
# It expects the file path to be passed via the FILE_TO_SERVE environment variable
CMD ["uvicorn", "line_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
