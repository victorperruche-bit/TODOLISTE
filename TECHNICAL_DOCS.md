# Documentation Technique - TODOLISTE v2.0

## 📋 Table des matières

1. [Architecture Générale](#-architecture-générale)
2. [Analyse du Code Original](#-analyse-du-code-original)
3. [Bugs Identifiés et Corrections](#-bugs-identifiés-et-corrections)
4. [Nouvelle Architecture](#-nouvelle-architecture)
5. [Flux de Données](#-flux-de-données)
6. [APIs Utilisées](#-apis-utilisées)
7. [Bonnes Pratiques Implémentées](#-bonnes-pratiques-implémentées)

---

## 🏗️ Architecture Générale

### Structure des Fichiers

```
TODOLISTE/
├── index.html          # Application principale (HTML + CSS + JS)
├── manifest.webmanifest # Configuration PWA
├── sw.js               # Service Worker
├── icons/              # Icônes de l'application
│   ├── icon-180.png    # iOS
│   ├── icon-192.png    # Android/Chrome
│   └── icon-512.png    # Android/Chrome (haute résolution)
├── README.md           # Documentation utilisateur
└── CHANGELOG.md        # Historique des changements
```

### Pattern d'Architecture

L'application suit une **architecture monofichier** (Single-File Application) avec une séparation logique en modules fonctionnels :

```
┌─────────────────────────────────────────────────────────────┐
│                    index.html                               │
├─────────────────┬─────────────────┬─────────────────┬───────┤
│   MODULE 1      │   MODULE 2      │   MODULE 3      │  ...  │
│  Utilitaires    │  Gestion Données│  Notifications   │       │
├─────────────────┼─────────────────┼─────────────────┼───────┤
│ - showToast()   │ - loadTasks()   │ - notify()      │       │
│ - formatDate()  │ - saveTasks()   │ - scheduleR...  │       │
│ - generateId()  │ - findTask...   │ - clearTask...  │       │
└─────────────────┴─────────────────┴─────────────────┴───────┘
```

---

## 🔍 Analyse du Code Original

### Fonctionnalités Originales

| Fonctionnalité | État | Implémentation |
|---------------|------|----------------|
| Ajout de tâches | ✅ | Formulaire + localStorage |
| Catégories | ✅ | Select (Devoir, Mail, Slack) |
| Rappels | ⚠️ | datetime-local + Notification API |
| Notifications | ⚠️ | Service Worker + Notification API |
| Filtres | ✅ | Boutons de filtre |
| Persistance | ✅ | localStorage |
| PWA | ✅ | manifest + service worker |
| Cache offline | ✅ | Service Worker |

### Problèmes Majeurs

#### 1. Gestion des Identifiants
```javascript
// Code original (BUGGY)
tasks.push({ 
  id: Date.now(),  // ❌ Même ID si 2 tâches à la même ms
  text, 
  category: $("category").value, 
  due: $("due").value ? new Date($("due").value).getTime() : null, 
  done: false 
});

tasks = tasks.filter(x => x !== t);  // ❌ Comparaison par référence
```

**Problèmes :**
- `Date.now()` peut produire des IDs dupliqués
- Comparaison par référence (`x !== t`) échoue après reload
- Pas de champ `createdAt` pour le tri

#### 2. Gestion des Timers
```javascript
// Code original (BUGGY)
const timers = [];

function scheduleReminders() {
  timers.forEach(clearTimeout);  // ❌ clearTimeout attend un ID, pas un timer
  timers.length = 0;  // ❌ Ne nettoie pas proprement
  // ...
  timers.push(setTimeout(() => { ... }));
}
```

**Problèmes :**
- `timers.forEach(clearTimeout)` est incorrect (clearTimeout prend un ID, pas un callback)
- Pas de nettoyage quand les tâches sont supprimées
- Timers perdus au reload
- Pas de vérification que la tâche existe encore

#### 3. Validation des Dates
```javascript
// Code original (BUGGY)
due: $("due").value ? new Date($("due").value).getTime() : null
```

**Problèmes :**
- Si `new Date(value)` retourne `Invalid Date`, `getTime()` retourne `NaN`
- `NaN` est stocké et traité comme une date valide
- Pas de vérification avec `isNaN()`

#### 4. Manipulation du DOM
```javascript
// Code original (BUGGY)
li.append(cb, div, tag, del);  // ❌ Non standard
```

**Problèmes :**
- `append()` avec plusieurs arguments n'est pas standard
- Peut causer des problèmes de compatibilité

---

## 🐛 Bugs Identifiés et Corrections

### Liste Complète des Bugs

| ID | Séverité | Description | Impact | Correction |
|----|----------|-------------|--------|------------|
| BUG-001 | 🔴 Critique | Comparaison par référence | Suppression échoue après reload | Utiliser les IDs |
| BUG-002 | 🔴 Critique | Gestion des timers | Mémoire non libérée | Map + nettoyage |
| BUG-003 | 🔴 Critique | Validation des dates | NaN stocké comme date | Vérification isNaN |
| BUG-004 | 🟡 Moyen | append() non standard | Compatibilité | appendChild() |
| BUG-005 | 🟡 Moyen | Pas de versioning | Migration cassée | Versioning |
| BUG-006 | 🟡 Moyen | Pas de tri | Expérience utilisateur | Tri avancé |
| BUG-007 | 🟡 Moyen | Pas d'affichage date | Manque d'info | Formatage |
| BUG-008 | 🟢 Mineur | Gestion des erreurs | Crash possible | Try/catch |
| BUG-009 | 🟢 Mineur | Permission denied | UI incohérente | Gestion complète |
| BUG-010 | 🟢 Mineur | Pas d'édition | Fonctionnalité manquante | Modal |

### Détail des Corrections

#### Correction BUG-001 : Identification par ID

```javascript
// AVANT (buggy)
tasks = tasks.filter(x => x !== t);

// APRÈS (corrigé)
function findTaskIndexById(id) {
  return tasks.findIndex(t => t.id === id);
}

// Utilisation
const taskIndex = findTaskIndexById(taskId);
if (taskIndex !== -1) {
  tasks.splice(taskIndex, 1);
}
```

**Avantages :**
- Identification fiable même après reload
- Pas de problèmes de référence
- Code plus maintenable

#### Correction BUG-002 : Gestion des Timers

```javascript
// AVANT (buggy)
const timers = [];
timers.forEach(clearTimeout);
timers.push(setTimeout(...));

// APRÈS (corrigé)
const timers = new Map(); // Map<taskId, timerId>

function clearTaskTimer(taskId) {
  if (timers.has(taskId)) {
    clearTimeout(timers.get(taskId));
    timers.delete(taskId);
  }
}

function scheduleReminders() {
  timers.forEach((timerId) => clearTimeout(timerId));
  timers.clear();
  // ...
  timers.set(task.id, timerId);
}
```

**Avantages :**
- Nettoyage explicite par tâche
- Pas de fuite mémoire
- Gestion propre au reload

#### Correction BUG-003 : Validation des Dates

```javascript
// AVANT (buggy)
due: $("due").value ? new Date($("due").value).getTime() : null

// APRÈS (corrigé)
const dueValue = dueEl.value;
const dueDate = dueValue ? new Date(dueValue) : null;
const due = dueDate && !isNaN(dueDate.getTime()) ? dueDate.getTime() : null;
```

**Avantages :**
- Pas de NaN stocké
- Validation robuste
- Code plus lisible

---

## 🆕 Nouvelle Architecture

### Modules Fonctionnels

#### 1. Module Utilitaires

**Responsabilités :**
- Fonctions helpers réutilisables
- Formatage de données
- Génération d'IDs

**Fonctions :**
```javascript
// Affichage de notifications toast
function showToast(message, duration = 3000)

// Formatage de dates
function formatDate(timestamp)

// Génération d'IDs uniques
function generateId()
```

#### 2. Module Gestion des Données

**Responsabilités :**
- CRUD des tâches
- Persistance localStorage
- Migration des données

**Fonctions :**
```javascript
// Chargement des tâches avec migration
function loadTasks()

// Sauvegarde des tâches
function saveTasks()

// Recherche par ID
function findTaskById(id)
function findTaskIndexById(id)

// Modification des tâches
function addTask(text, category, due)
function updateTask(taskId, updates)
function clearDoneTasks()
```

**Structure des données :**
```javascript
{
  id: string,           // ID unique (ex: "1700000000000-abc123")
  text: string,         // Texte de la tâche
  category: string,     // "devoir" | "mail" | "slack"
  due: number | null,   // Timestamp du rappel
  done: boolean,        // Statut terminé
  createdAt: number     // Date de création (timestamp)
}
```

#### 3. Module Notifications

**Responsabilités :**
- Gestion des permissions
- Planification des rappels
- Affichage des notifications

**Fonctions :**
```javascript
// Affichage d'une notification
function notify(title, body)

// Planification de tous les rappels
function scheduleReminders()

// Nettoyage d'un timer spécifique
function clearTaskTimer(taskId)

// Mise à jour de l'UI
function updateNotifUI()
```

**Gestion des timers :**
- Utilisation d'une `Map<taskId, timerId>` pour suivre les timers
- Nettoyage automatique quand une tâche est supprimée ou marquée comme terminée
- Replanification après modification

#### 4. Module Tri et Filtrage

**Responsabilités :**
- Tri des tâches selon différents critères
- Filtrage par catégorie/statut

**Fonctions :**
```javascript
// Tri des tâches
function sortTasks()

// Filtrage des tâches
function filterTasks()
```

**Critères de tri :**
- `created-desc` : Par date de création (récents d'abord)
- `due-asc` : Par date de rappel (les plus proches d'abord)
- `category` : Par catégorie (Devoir → Mail → Slack)

#### 5. Module Rendu

**Responsabilités :**
- Création du DOM pour les tâches
- Rafraîchissement de l'interface

**Fonctions :**
```javascript
// Création du DOM pour une tâche
function renderTask(t)

// Rafraîchissement complet
function render()
```

**Structure DOM d'une tâche :**
```html
<li>
  <input type="checkbox" />
  <div class="task">
    <span class="label">Texte de la tâche</span>
    <span class="due">Aujourd'hui à 14:30</span>
  </div>
  <span class="tag devoir">devoir</span>
  <div class="actions">
    <button class="edit">✏️</button>
    <button class="delete">✕</button>
  </div>
</li>
```

#### 6. Module Modal d'Édition

**Responsabilités :**
- Interface de modification des tâches
- Gestion de l'état du modal

**Fonctions :**
```javascript
// Ouverture du modal
function openEditModal(taskId)

// Fermeture du modal
function closeEditModal()

// Sauvegarde des modifications
function saveEdit()
```

### Initialisation

```javascript
function init() {
  // 1. Charger les tâches
  loadTasks();
  
  // 2. Rendu initial
  render();
  
  // 3. Mise à jour de l'UI des notifications
  updateNotifUI();
  
  // 4. Planifier les rappels
  if ("Notification" in window) {
    scheduleReminders();
  }
  
  // 5. Enregistrer le service worker
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js");
  }
  
  // 6. Gestion du double-clic mobile
  setupDoubleClickPrevention();
}
```

---

## 📊 Flux de Données

### Flux Principal

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   UI        │────▶│   Actions    │────▶│   State     │
│  (Form)     │     │  (Ajout)     │     │  (tasks)    │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   State     │────▶│  localStorage│◀────│   State     │
│  (tasks)    │     │              │     │  (Chargement)│
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       ▼                                       ▼
┌─────────────┐                         ┌─────────────┐
│   Render    │◀────────────────────────│   Filtres   │
│  (Affichage)│                         │   / Tri      │
└─────────────┘                         └─────────────┘
```

### Flux des Notifications

```
┌─────────────┐
│   Tâche     │────▶┐
│  avec due   │    │
└─────────────┘    │
                   ▼
┌─────────────────────────┐
│  scheduleReminders()    │────▶┐
│  - Calcul des delays    │    │
│  - Création des timers  │    │
└─────────────────────────┘    │
                           ▼
              ┌─────────────────────────┐
              │      Timer              │
              │  (setTimeout)           │────▶┐
              └─────────────────────────┘    │
                                          ▼
┌─────────────────────────┐     ┌─────────────┐
│       notify()           │────▶│ Notification │
│  - Vérifie permissions   │     │   API        │
│  - Affiche la notification│     └─────────────┘
└─────────────────────────┘
```

### Flux de Migration

```
┌─────────────────────────┐
│  Chargement depuis       │
│  localStorage            │
└─────────────┬───────────┘
              │
              ▼
┌─────────────────────────┐
│  Vérification de la      │
│  version stockée          │
└─────────────┬───────────┘
              │
     ┌────────▴────────┐
     ▼                 ▼
┌───────────┐   ┌─────────────────┐
│  Même      │   │  Version        │
│  version   │   │  différente     │
└───────────┘   │  → Migration     │
                 └─────────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │  Données migrées         │
                 │  et sauvegardées         │
                 └─────────────────────────┘
```

---

## 🌐 APIs Utilisées

### 1. Web Storage API (`localStorage`)

**Utilisation :**
- Persistance des tâches
- Stockage de la version

**Méthodes :**
```javascript
localStorage.setItem(key, value);
localStorage.getItem(key);
localStorage.removeItem(key);
```

**Limites :**
- ~5MB de stockage
- Synchronique (bloque le thread principal)
- Uniquement des strings

### 2. Notification API

**Utilisation :**
- Affichage des notifications système
- Demande de permission

**Méthodes :**
```javascript
Notification.requestPermission();
new Notification(title, options);
```

**Permissions :**
- `default` : Non demandé
- `granted` : Autorisé
- `denied` : Refusé

**Limitations iOS :**
- Pas de notifications sans serveur push
- Nécessite iOS 16.4+
- L'app doit être ouverte

### 3. Service Worker API

**Utilisation :**
- Cache offline
- Gestion des notifications en arrière-plan
- Interception des requêtes

**Événements :**
```javascript
self.addEventListener("install", ...);
self.addEventListener("activate", ...);
self.addEventListener("fetch", ...);
self.addEventListener("notificationclick", ...);
```

**Cycle de vie :**
```
Enregistrement → Installation → Attente → Activation → Contrôle
```

### 4. Cache API

**Utilisation :**
- Mise en cache des assets
- Fallback offline

**Méthodes :**
```javascript
caches.open(cacheName);
cache.addAll(urls);
cache.match(request);
cache.put(request, response);
```

### 5. DOM API

**Utilisation :**
- Manipulation du DOM
- Gestion des événements

**Méthodes :**
```javascript
document.createElement(tag);
element.appendChild(node);
element.addEventListener(event, handler);
```

---

## ✅ Bonnes Pratiques Implémentées

### 1. Gestion des Identifiants

✅ **Utilisation d'IDs uniques et persistants**
```javascript
function generateId() {
  return Date.now() + "-" + Math.random().toString(36).substr(2, 9);
}
```

**Avantages :**
- Pas de collisions
- Persistant après reload
- Facile à manipuler

### 2. Gestion des Erreurs

✅ **Try/catch systématique**
```javascript
try {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    tasks = JSON.parse(stored);
  }
} catch (e) {
  console.error("Erreur:", e);
  tasks = [];
  showToast("Erreur de chargement");
}
```

**Avantages :**
- Application ne crash pas
- Feedback utilisateur
- Debug facilité

### 3. Validation des Données

✅ **Validation systématique**
```javascript
// Validation des dates
if (due && isNaN(due)) {
  due = null;
}

// Validation des catégories
if (!CATS.includes(category)) {
  category = "devoir";
}
```

**Avantages :**
- Pas de données invalides
- Expérience utilisateur cohérente

### 4. Nettoyage des Ressources

✅ **Nettoyage des timers**
```javascript
// Au reload
window.addEventListener("beforeunload", () => {
  timers.forEach((timerId) => clearTimeout(timerId));
  timers.clear();
});

// À la suppression
function clearTaskTimer(taskId) {
  if (timers.has(taskId)) {
    clearTimeout(timers.get(taskId));
    timers.delete(taskId);
  }
}
```

**Avantages :**
- Pas de fuite mémoire
- Ressources libérées proprement

### 5. Migration des Données

✅ **Versioning du stockage**
```javascript
const STORAGE_VERSION = "2.0";

function loadTasks() {
  const storedVersion = localStorage.getItem(STORAGE_KEY + ".version");
  if (storedVersion !== STORAGE_VERSION) {
    // Migration des données
    tasks = migrateData(JSON.parse(stored));
    saveTasks();
    localStorage.setItem(STORAGE_KEY + ".version", STORAGE_VERSION);
  }
}
```

**Avantages :**
- Compatibilité entre versions
- Migration automatique
- Pas de perte de données

### 6. Feedback Utilisateur

✅ **Notifications toast**
```javascript
function showToast(message, duration = 3000) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), duration);
}
```

**Avantages :**
- Utilisateur informé des actions
- Feedback visuel
- Non intrusif

### 7. Code Modulaire

✅ **Séparation des responsabilités**
```javascript
// Chaque module a ses propres fonctions
// Module Utilitaires
function showToast() { ... }
function formatDate() { ... }

// Module Données
function loadTasks() { ... }
function saveTasks() { ... }

// Module Notifications
function notify() { ... }
function scheduleReminders() { ... }
```

**Avantages :**
- Code maintenable
- Facile à tester
- Réutilisable

### 8. Documentation

✅ **Commentaires clairs**
```javascript
/**
 * Formate une date en string lisible
 * @param {number} timestamp - Timestamp en milliseconds
 * @returns {string} Date formatée
 */
function formatDate(timestamp) {
  // ...
}
```

**Avantages :**
- Code compréhensible
- Facile à maintenir
- Meilleure collaboration

---

## 📚 Ressources

- [MDN Web Docs - localStorage](https://developer.mozilla.org/fr/docs/Web/API/Window/localStorage)
- [MDN Web Docs - Notification API](https://developer.mozilla.org/fr/docs/Web/API/Notification)
- [MDN Web Docs - Service Workers](https://developer.mozilla.org/fr/docs/Web/API/Service_Worker_API)
- [PWA Checklist](https://web.dev/pwa-checklist/)
- [iOS PWA Limitations](https://medium.com/@firt/progressive-web-apps-on-ios-are-here-d00959168ff5)

---

## 🎯 Conclusion

La version 2.0 de TODOLISTE représente une **réingénierie complète** de l'application avec :

1. **Correction de tous les bugs critiques** identifiés dans la version 1.0
2. **Amélioration de l'architecture** avec une meilleure séparation des responsabilités
3. **Ajout de nouvelles fonctionnalités** (édition, tri, affichage des dates)
4. **Implémentation des bonnes pratiques** (validation, gestion des erreurs, migration)
5. **Documentation complète** pour faciliter la maintenance

L'application est maintenant **plus robuste, plus maintenable et plus riche en fonctionnalités**, tout en conservant sa simplicité et son approche minimaliste.
