# Stage 1: Build image
FROM python:3.11-alpine as builder

WORKDIR /app
COPY /worker .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM python:3.11-alpine

WORKDIR /app
COPY --from=builder /app /app
EXPOSE 8000
ENV MONGO_URI="mongodb://mongodb:27017/realm_warm"

CMD ["python", "tracker.py"]
