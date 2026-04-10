FROM node:22-slim

WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json /app/
COPY apps/web/package.json /app/apps/web/
COPY packages/sdk/package.json /app/packages/sdk/

# Install dependencies
RUN npm install

# Copy source
COPY . /app

EXPOSE 5173

# Vite hot reload requires host 0.0.0.0 for Docker
CMD ["npm", "--workspace", "@acp/web", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
