# Using official python runtime base image
FROM python:3.13

# Define build arguments for database configuration
ARG DB_TYPE="mysql"
ARG DB_HOST="localhost"
ARG DB_PORT="3306"
ARG DB_NAME="votedb"
ARG DB_USER="user"
ARG DB_PASS="password"

# Set environment variables from build arguments
ENV DB_TYPE=${DB_TYPE}
ENV DB_HOST=${DB_HOST}
ENV DB_PORT=${DB_PORT}
ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASS=${DB_PASS}

# Set the application directory
WORKDIR /app

# Install requirements.txt
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy code and necessary directories to the /app inside the container
COPY . /app
COPY data /app/data
COPY seeds /app/seeds
COPY logs /app/logs

# Expose the port server listens to
EXPOSE 8000

# Define command to be run when launching the container
CMD ["python", "app.py"]