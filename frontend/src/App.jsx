// App.jsx — Le composant principal du frontend
// C'est la page que l'utilisateur voit dans son navigateur.
// Elle affiche la liste des tâches et permet d'en ajouter, toggler et supprimer.

import { useState, useEffect } from "react";

function App() {
  // useState = stocker des données qui peuvent changer (React les réaffiche automatiquement)
  const [tasks, setTasks] = useState([]); // Liste des tâches (vide au départ)
  const [newTask, setNewTask] = useState(""); // Le texte tapé dans le champ input

  // useEffect = exécuter du code au chargement de la page
  // Ici : appeler GET /api/tasks pour récupérer les tâches depuis le backend
  useEffect(() => {
    fetch("/api/tasks") // Appel HTTP vers le backend
      .then((res) => res.json()) // Convertir la réponse en JSON
      .then(setTasks) // Stocker les tâches dans le state
      .catch(console.error); // Afficher l'erreur dans la console si ça échoue
  }, []); // [] = exécuter une seule fois, au chargement

  // Fonction appelée quand l'utilisateur soumet le formulaire (bouton "Ajouter")
  const addTask = async (e) => {
    e.preventDefault(); // Empêcher le rechargement de la page (comportement par défaut d'un formulaire)
    if (!newTask.trim()) return; // Ne rien faire si le champ est vide

    // Appel HTTP POST vers le backend pour créer la tâche
    const res = await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" }, // On envoie du JSON
      body: JSON.stringify({ title: newTask }), // Le corps de la requête : {"title": "..."}
    });
    const task = await res.json(); // Le backend retourne la tâche créée (avec son id)
    setTasks([...tasks, task]); // Ajouter la nouvelle tâche à la liste affichée
    setNewTask(""); // Vider le champ input
  };

  // Fonction appelée quand on clique sur une tâche pour la toggler (done / not done)
  const toggleTask = async (id) => {
    // Appel HTTP PATCH vers le backend — inverse le statut "done"
    const res = await fetch(`/api/tasks/${id}`, { method: "PATCH" });
    const updated = await res.json(); // Le backend retourne la tâche mise à jour
    // Remplacer la tâche dans la liste par sa version mise à jour
    setTasks(tasks.map((t) => (t.id === id ? updated : t)));
  };

  // Fonction appelée quand on clique sur le bouton "✕" pour supprimer une tâche
  const deleteTask = async (id) => {
    // Appel HTTP DELETE vers le backend
    await fetch(`/api/tasks/${id}`, { method: "DELETE" });
    // Retirer la tâche de la liste affichée (sans recharger la page)
    setTasks(tasks.filter((t) => t.id !== id));
  };

  // Le JSX ci-dessous décrit ce qui est affiché dans le navigateur
  // C'est du HTML mélangé avec du JavaScript (syntaxe React)
  return (
    <div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>DevOps Task List</h1>

      {/* Formulaire pour ajouter une tâche */}
      <form onSubmit={addTask} style={{ display: "flex", gap: 8 }}>
        <input
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)} // Met à jour le state à chaque frappe
          placeholder="Nouvelle tâche..."
          style={{ padding: 8, flex: 1 }}
        />
        <button type="submit" style={{ padding: "8px 16px" }}>
          Ajouter
        </button>
      </form>

      {/* Liste des tâches — .map() parcourt le tableau et crée un élément par tâche */}
      <ul style={{ listStyle: "none", padding: 0, marginTop: 20 }}>
        {tasks.map((t) => (
          <li
            key={t.id} // key = identifiant unique pour React (obligatoire dans une liste)
            style={{
              display: "flex",
              alignItems: "center",
              padding: "8px 0",
              borderBottom: "1px solid #eee",
            }}
          >
            {/* Cliquer sur le titre toggle le statut done/not done */}
            <span
              onClick={() => toggleTask(t.id)}
              style={{
                flex: 1,
                cursor: "pointer",
                textDecoration: t.done ? "line-through" : "none", // Barré si done
                color: t.done ? "#999" : "#000", // Grisé si done
              }}
            >
              {t.title}
            </span>

            {/* Bouton pour supprimer la tâche */}
            <button
              onClick={() => deleteTask(t.id)}
              style={{
                background: "none",
                border: "none",
                color: "#c00",
                cursor: "pointer",
                fontSize: 18,
                padding: "0 8px",
              }}
            >
              ✕
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
