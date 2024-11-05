# Use an official Python 3.10 image as a base
FROM python:3.10-slim

# Install dependencies for CEF (required for display and basic GUI support)
RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libnss3 \
    libxss1 \
    libasound2 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install Python dependencies (cefpython3 and any other required packages)
RUN pip install --no-cache-dir cefpython3

# Command to run your Python application (replace 'your_application.py' with the actual script name)
CMD ["python", "your_application.py"]

