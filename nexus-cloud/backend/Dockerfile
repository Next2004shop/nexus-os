
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install specific production dependencies if missing
RUN pip install --no-cache-dir gunicorn

# Make port 5002 available to the world outside this container
EXPOSE 5002

# Define environment variable
ENV PORT=5002
ENV HOST=0.0.0.0

# Run uvicorn when the container launches
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5002"]
