FROM python:3.9-slim

WORKDIR /app

# Copy and install requirements from the src directory
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source from the src directory
COPY src/ .

EXPOSE 8000

# The command remains the same as main.py will be in the root of the WORKDIR
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
