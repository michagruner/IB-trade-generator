# Use a Python 3.9 base image
FROM python:latest

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose port 5000 for the Quart application
EXPOSE 5000

# Start the Quart application using Hypercorn
CMD ["hypercorn", "--bind", "0.0.0.0:5000", "app:app"]

