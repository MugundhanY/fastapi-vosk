# Use a Docker image with FFmpeg pre-installed
FROM jrottenberg/ffmpeg:4.4-ubuntu

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt /app/

# Install the Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of your application code to the container
COPY . /app/

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Command to run the FastAPI app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
