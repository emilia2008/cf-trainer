# ---- Build the static site ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Empty: the browser calls /api on the same origin and nginx forwards it to the backend.
# Set it at build time only when the API lives on another domain.
ARG VITE_API_BASE=""
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

# ---- Serve it with nginx ----
FROM nginx:1.27-alpine
# Where nginx forwards /api requests. The nginx image fills ${BACKEND_URL} into the
# template at start-up (envsubst), so the same image works outside docker compose too.
ENV BACKEND_URL=http://backend:8000
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
