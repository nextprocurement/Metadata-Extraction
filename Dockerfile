# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY app/requirements.txt /app/requirements.txt

# Copy the rest of the application code
COPY app/ /app/

# Copy the environment file (optional, if you use it inside the container)
COPY .env .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for Flask (customizable)
EXPOSE 5000

# Command to run the application
CMD ["python", "main.py"]
