# ---------- STAGE 1: build ----------
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# ---------- STAGE 2: nginx ----------
FROM nginx:alpine

# Удаляем дефолтный конфиг nginx
RUN rm /etc/nginx/conf.d/default.conf

# Копируем свой конфиг
COPY nginx.conf /etc/nginx/conf.d

# Копируем собранный фронт в папку nginx
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

EXPOSE  80
CMD ["nginx", "-g", "daemon off;"]
