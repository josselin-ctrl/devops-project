# Dockerfile du frontend — Multi-stage build (Bun → nginx)
# Étape 1 : Bun compile le code React en fichiers statiques (HTML/JS/CSS)
# Étape 2 : nginx sert ces fichiers statiques en production
# Résultat : l'image finale ne contient que nginx + les fichiers, pas Bun ni node_modules

# --- Étape 1 : Build ---
FROM oven/bun:latest AS build
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile        # Installer les dépendances (versions exactes du lockfile)
COPY . .
RUN bun run build                        # Compiler React → fichiers statiques dans dist/

# --- Étape 2 : Production ---
# nginx:alpine = serveur web ultra-léger (~5 Mo)
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html    # Copier les fichiers buildés
COPY nginx.conf /etc/nginx/conf.d/default.conf       # Config nginx (reverse proxy vers backend)
EXPOSE 80                                            # Le frontend est servi sur le port 80
