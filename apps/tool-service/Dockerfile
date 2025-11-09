FROM node:20-alpine

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml ./
COPY apps/tool-service/package.json ./apps/tool-service/
COPY packages/*/package.json ./packages/*/

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build tool service
WORKDIR /app/apps/tool-service
RUN pnpm build

# Expose port
EXPOSE 3001

# Run service
CMD ["pnpm", "start"]

