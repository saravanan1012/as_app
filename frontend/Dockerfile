FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG NUXT_API_PROXY=http://api:8000
ENV NUXT_API_PROXY=$NUXT_API_PROXY
ENV NUXT_PUBLIC_API_BASE=/api
ENV NUXT_PUBLIC_VENDOR_SLUG=as-demo
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000
ENV NUXT_API_PROXY=http://api:8000
ENV NUXT_PUBLIC_API_BASE=/api
ENV NUXT_PUBLIC_VENDOR_SLUG=as-demo
COPY --from=build /app/.output ./.output
EXPOSE 3000
USER node
CMD ["node", ".output/server/index.mjs"]
