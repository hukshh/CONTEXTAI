FROM node:18-alpine AS builder
WORKDIR /app

# Copy package lock and install dependencies
COPY package*.json ./
RUN npm ci

# Copy frontend source code
COPY . .

# Set env variables needed during build
ENV NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Build optimized pages
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["npm", "run", "start"]
