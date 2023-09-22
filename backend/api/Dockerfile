# Stage 1: Build image
FROM python:3.11-alpine

WORKDIR /app
COPY /api .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
ENV MONGO_URI="mongodb://mongodb:27017/realm_warm"

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
