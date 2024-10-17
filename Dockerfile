# Use a base image that includes Python and FFmpeg
FROM ubuntu:20.04

# Set the timezone environment variable to prevent tzdata prompt
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory
WORKDIR /app

# Install dependencies (Python, pip, and FFmpeg)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    tzdata

# Copy the requirements.txt file to the container
COPY requirements.txt /app/

# Install the Python dependencies
RUN pip3 install -r requirements.txt

# Copy the rest of your application code to the container
COPY . /app/

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Command to run the FastAPI app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
