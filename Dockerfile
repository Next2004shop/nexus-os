# Build Stage for Frontend
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production Stage (Python Backend)
FROM python:3.9-slim
WORKDIR /app

# Install system dependencies for MetaTrader5 (Wine/Xvfb would be needed for real MT5 on Linux, 
# but for Cloud Run we assume "Headless/Mock" or Windows Container. 
# Since MT5 is Windows-only, this Dockerfile is for the "Brain" and Web Interface.
# The actual Trading Terminal must run on a Windows VPS or local machine.)
RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY nexus_bridge.py .
COPY nexus_brain.py .
COPY nexus_security.py .
COPY nexus_memory.json .

# Copy Built Frontend Assets
COPY --from=build /app/dist ./static

# Expose Port
EXPOSE 5000

# Run Application
CMD ["python", "nexus_bridge.py"]
