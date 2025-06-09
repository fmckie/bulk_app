FROM nginx:alpine

# Copy the app files to nginx html directory
COPY app/ /usr/share/nginx/html/

# Expose port 80
EXPOSE 80

# Nginx will start automatically with the base image