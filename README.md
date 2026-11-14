# TODOLISTE

Todoliste minimaliste, interactive et **installable sur iPhone** (PWA), sans aucune dépendance.

## Fonctionnalités

- Ajout de tâches avec catégorie : **Devoir**, **Mail** ou **Slack**
- Heure de rappel optionnelle pour chaque tâche
- Notifications locales (rappel à l'heure de la tâche, app ouverte)
- Cocher / décocher pour marquer comme terminé
- Suppression d'une tâche
- Filtres : Tout, Devoir, Mail, Slack, À faire, Terminé
- Effacer toutes les tâches terminées en un clic
- Compteur de tâches restantes
- Persistance automatique via `localStorage`
- Fonctionne hors-ligne (service worker)

## Installation sur iPhone

1. Ouvre la page dans **Safari**
2. Appuie sur **Partager** (carré avec flèche)
3. Choisis **Sur l'écran d'accueil**
4. L'app s'ouvre en plein écran, avec son icône, comme une vraie app

> ⚠️ Nécessite iOS 16.4+ pour les notifications. Le rappel se déclenche à l'heure choisie tant que l'app est ouverte (en arrière-plan ou fermée, iOS ne permet pas aux PWA de déclencher des notifications sans serveur push).

## Utilisation locale

Ouvre simplement `index.html` dans un navigateur, ou sers le dossier :

```bash
python3 -m http.server 8000
```

puis ouvre http://localhost:8000

## Fichiers

- `index.html` — l'application complète
- `manifest.webmanifest` — configuration PWA
- `sw.js` — service worker (cache hors-ligne + notifications)
- `icons/` — icônes de l'app
