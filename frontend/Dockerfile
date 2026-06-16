FROM node:20-alpine AS builder
WORKDIR /app

# install deps
COPY package*.json ./
RUN npm ci --production=false

# copy source and build
COPY . .
RUN npm run build

FROM node:20-alpine
COPY --from=builder /app .
EXPOSE 3000
CMD ["npm","run","start"]
