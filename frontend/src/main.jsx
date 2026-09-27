// main.jsx — Le point d'entrée du frontend
// Ce fichier lance l'application React et l'attache à la page HTML (index.html)

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App"; // Notre composant principal

// Crée la racine React et affiche le composant <App /> dans le <div id="root"> de index.html
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
