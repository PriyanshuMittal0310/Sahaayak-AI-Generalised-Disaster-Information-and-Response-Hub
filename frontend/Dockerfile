# Development stage
FROM node:18 AS development

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including devDependencies)
RUN npm install

# Copy source code
COPY . .

# Expose port for development server
EXPOSE 3000

# Start development server
CMD ["npm", "start"]

# Production stage (optional, uncomment if needed)
# FROM nginx:alpine
# COPY --from=development /app/build /usr/share/nginx/html
# EXPOSE 80
# CMD ["nginx", "-g", "daemon off;"]
