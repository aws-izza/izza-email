# 1. Use a slim, official Python image
FROM python:3.12-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy and install Python dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the application code
COPY src/ .

# 5. Expose the port the application runs on
EXPOSE 8000

# 6. Define the command to run the application
CMD ["python", "main.py"]
