FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build widgets
RUN npm run build

# Expose port
EXPOSE 3002

# Start server
CMD ["npm", "run", "serve"]
