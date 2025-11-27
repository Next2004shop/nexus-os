# Stage 1: Build the React App
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve with Nexus Host (Node.js)
FROM node:18-alpine
WORKDIR /app

# Copy package.json for server dependencies
COPY package*.json ./
# Install ONLY production dependencies (express, etc.)
RUN npm install --production

# Copy the built React app from Stage 1
COPY --from=builder /app/dist ./dist
# Copy the Nexus Host server
COPY server.js .

# Expose the port
EXPOSE 3000

# Start the Nexus Host
CMD ["node", "server.js"]
