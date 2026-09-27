// vite.config.js — Configuration de Vite (le bundler/serveur de dev du frontend)

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()], // Active le support React (JSX, hot reload, etc.)
  server: {
    port: 3000, // Le frontend de dev tourne sur http://localhost:3000
    proxy: {
      // En dev, les requêtes /api sont redirigées vers le backend (port 8000)
      // Exemple : fetch("/api/tasks") → http://localhost:8000/api/tasks
      // En production, c'est nginx qui fait ce proxy (voir nginx.conf)
      "/api": "http://localhost:8000",
    },
  },
});
