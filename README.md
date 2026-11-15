# TODOLISTE

Todoliste minimaliste, interactive et **installable sur iPhone** (PWA), avec gestion des rappels et support hors-ligne.

## ✨ Fonctionnalités

### Gestion des tâches
- ✅ Ajout de tâches avec texte libre
- ✅ Catégorisation : **Devoir**, **Mail** ou **Slack**
- ✅ Heure de rappel optionnelle pour chaque tâche
- ✅ Notifications locales (rappel à l'heure de la tâche)
- ✅ **Édition des tâches** (nouveau !)
- ✅ Cocher / décocher pour marquer comme terminé
- ✅ Suppression d'une tâche

### Organisation
- ✅ Filtres : **Tout**, **Devoir**, **Mail**, **Slack**, **À faire**, **Terminé**
- ✅ **Tri des tâches** :
  - Par ordre de création (récents d'abord)
  - Par date de rappel (les plus proches d'abord)
  - Par catégorie
- ✅ Effacer toutes les tâches terminées en un clic
- ✅ Compteur de tâches restantes

### Persistance et notifications
- ✅ Persistance automatique via `localStorage`
- ✅ **Migration des données** entre versions
- ✅ Gestion robuste des notifications
- ✅ Fonctionne hors-ligne (service worker)

## 📱 Installation sur iPhone

1. Ouvre la page dans **Safari**
2. Appuie sur **Partager** (carré avec flèche)
3. Choisis **Sur l'écran d'accueil**
4. L'app s'ouvre en plein écran, avec son icône, comme une vraie app

> ⚠️ **Limitations iOS** : Les notifications ne fonctionnent que si l'app est ouverte (en arrière-plan ou au premier plan). iOS ne permet pas aux PWA de déclencher des notifications sans serveur push. Nécessite iOS 16.4+.

## 💻 Utilisation locale

Ouvre simplement `index.html` dans un navigateur, ou sers le dossier :

```bash
# Python 3
python3 -m http.server 8000

# Node.js (nécessite npm install -g http-server)
http-server

# PHP
php -S localhost:8000
```

Puis ouvre [http://localhost:8000](http://localhost:8000)

## 📁 Fichiers

- `index.html` — l'application complète (HTML + CSS + JavaScript)
- `manifest.webmanifest` — configuration PWA
- `sw.js` — service worker (cache hors-ligne + notifications)
- `icons/` — icônes de l'app (180x180, 192x192, 512x512)

## 🔧 Développement

### Structure du code

L'application est conçu en **architecture monofichier** (single-file app) avec séparation logique :

```
┌─────────────────────────────────────────────────────────────┐
│                        index.html                            │
├─────────────────┬─────────────────┬─────────────────┬───────┤
│      HTML       │      CSS        │   JavaScript    │ Icons │
│   (structure)   │  (style)        │   (logique)      │       │
└─────────────────┴─────────────────┴─────────────────┴───────┘
```

### Modules JavaScript

1. **Utilitaires** - Fonctions helpers
   - `showToast()` - Notifications toast
   - `formatDate()` - Formatage des dates
   - `generateId()` - Génération d'IDs uniques

2. **Gestion des données** - CRUD des tâches
   - `loadTasks()` / `saveTasks()` - Persistance
   - `findTaskById()` / `findTaskIndexById()` - Recherche
   - `addTask()` / `updateTask()` - Modification

3. **Notifications** - Gestion des rappels
   - `notify()` - Affichage des notifications
   - `scheduleReminders()` - Planification
   - `clearTaskTimer()` - Nettoyage
   - `updateNotifUI()` - Mise à jour UI

4. **Tri et filtrage** - Organisation
   - `sortTasks()` - Tri par différents critères
   - `filterTasks()` - Filtrage par catégorie/statut

5. **Rendu** - Affichage
   - `renderTask()` - Création du DOM pour une tâche
   - `render()` - Rafraîchissement complet

6. **Modal d'édition** - Interface de modification
   - `openEditModal()` / `closeEditModal()`
   - `saveEdit()`

### Données

Les tâches sont stockées sous forme d'objets :

```javascript
{
  id: string,           // ID unique (timestamp + random)
  text: string,         // Texte de la tâche
  category: string,     // "devoir" | "mail" | "slack"
  due: number | null,   // Timestamp du rappel (milliseconds)
  done: boolean,        // Statut terminé
  createdAt: number     // Date de création (timestamp)
}
```

### Stockage

- **Clé** : `todoliste.tasks`
- **Version** : `todoliste.tasks.version` (pour les migrations)
- **Format** : JSON

## 🐛 Corrections apportées (v2.0)

### Bugs critiques fixés

| Bug | Description | Solution |
|-----|-------------|----------|
| 🔴 Comparaison par référence | La suppression échouait après reload | Utilisation des IDs pour l'identification |
| 🔴 Gestion des timers | Timers non nettoyés, perdus au reload | Map des timers + nettoyage explicite |
| 🔴 Validation des dates | `NaN` stocké comme date | Vérification avec `isNaN()` |
| 🔴 Problème `append()` | Non standard | Utilisation de `appendChild()` |
| 🔴 Pas de versioning | Migration des données cassée | Ajout de la version du stockage |

### Améliorations majeures

1. **Édition des tâches** - Modal pour modifier texte, catégorie et date
2. **Tri avancé** - Par date de création, date de rappel, catégorie
3. **Affichage des dates** - Format lisible (Aujourd'hui, Demain, date complète)
4. **Gestion robuste des notifications** - Nettoyage, replanification, UI améliorée
5. **Migration des données** - Compatibilité avec l'ancienne version
6. **Gestion des erreurs** - Try/catch, feedback utilisateur
7. **UI/UX améliorée** - Toasts, boutons d'action, design cohérent
8. **Service Worker amélioré** - Cache plus robuste, gestion des erreurs

### Améliorations mineures

- Boutons de suppression et d'édition sur chaque tâche
- Indicateurs visuels de tri
- Messages de confirmation (toasts)
- Validation des formulaires
- Gestion du focus et des clics doubles sur mobile
- Support des permissions de notification (granted/denied/default)

## 🚀 Roadmap

### Futur proche
- [ ] **Recherche** - Filtrer les tâches par texte
- [ ] **Synchronisation** - Sync entre appareils (via Firebase ou autre)
- [ ] **Backup/Restore** - Export/import des données
- [ ] **Dark mode** - Thème sombre
- [ ] **Répétition des tâches** - Rappels récurrents

### Idées
- [ ] **Statistiques** - Temps passé, tâches complétées
- [ ] **Catégories personnalisées** - Ajout de nouvelles catégories
- [ ] **Priorités** - Niveaux de priorité
- [ ] **Sous-tâches** - Tâches imbriquées
- [ ] **Collaboration** - Partage de listes

## 🤝 Contribution

1. Fork le projet
2. Crée une branche (`git checkout -b feature/nouvelle-fonctionnalité`)
3. Commit tes changements (`git commit -m 'Ajout de X'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalité`)
5. Ouvre une Pull Request

## 📜 Licence

MIT License - Libre d'utiliser, modifier et distribuer.

---

**Version 2.0** - Corrigée et améliorée

*Generé avec amour et du café ☕*
