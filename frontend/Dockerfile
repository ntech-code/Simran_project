# Frontend Dockerfile for Tax Analysis System
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files first (for Docker layer caching)
COPY package.json ./

# Install dependencies
RUN npm install

# Copy the rest of the app
COPY . .

# Set the backend API URL for the build
# In Docker, the frontend talks to the backend via the browser,
# so it needs to use localhost:8000 (the exposed port)
ENV VITE_API_URL=http://localhost:8000

# Build the production bundle
RUN npm run build

# Production stage — serve with nginx
FROM nginx:alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
