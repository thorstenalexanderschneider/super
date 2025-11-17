# Stage 1: static build (optional, for frameworks)
FROM nginx:alpine AS runtime

# Remove default nginx html
RUN rm -rf /usr/share/nginx/html/*

# Copy your site
COPY . /usr/share/nginx/html/

# Expose HTTP
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
