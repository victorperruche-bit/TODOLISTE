# Changelog

## [2.0.0] - 2024-11-15

### ✅ Corrections de bugs

#### 🔴 Bugs critiques

1. **Comparaison par référence dans la suppression**
   - **Problème** : `tasks.filter(x => x !== t)` comparait les références d'objets
   - **Impact** : La suppression échouait après un reload de page
   - **Solution** : Utilisation des IDs uniques pour identifier les tâches
   - **Fichiers** : `index.html` (fonctions de suppression)

2. **Gestion des timers de rappel**
   - **Problème** : Les timers n'étaient pas nettoyés quand les tâches étaient supprimées ou marquées comme terminées
   - **Impact** : Mémoire non libérée, rappels fantômes
   - **Solution** : Utilisation d'une `Map` pour suivre les timers et nettoyage explicite
   - **Fichiers** : `index.html` (gestion des rappels)

3. **Validation des dates de rappel**
   - **Problème** : Pas de vérification que `new Date(value).getTime()` ne retourne pas `NaN`
   - **Impact** : Tâches avec `due: NaN` étaient traitées comme ayant un rappel
   - **Solution** : Validation systématique avec `isNaN()`
   - **Fichiers** : `index.html` (ajout/modification de tâches)

4. **Problème avec `append()`**
   - **Problème** : `li.append(cb, div, tag, del)` n'est pas standard
   - **Impact** : Problèmes de compatibilité avec certains navigateurs
   - **Solution** : Utilisation de `appendChild()` pour chaque élément
   - **Fichiers** : `index.html` (fonction `renderTask`)

5. **Pas de versioning du localStorage**
   - **Problème** : Aucune gestion des migrations entre versions
   - **Impact** : Données corrompues après une mise à jour
   - **Solution** : Ajout d'un système de versioning avec migration automatique
   - **Fichiers** : `index.html` (fonction `loadTasks`)

#### 🟡 Bugs moyens

6. **Tri des tâches absent**
   - **Problème** : Les tâches s'affichaient dans l'ordre d'ajout
   - **Solution** : Ajout de multiples critères de tri (création, rappel, catégorie)

7. **Affichage des dates de rappel**
   - **Problème** : Les dates de rappel n'étaient pas visibles dans l'UI
   - **Solution** : Ajout d'un affichage formaté (Aujourd'hui, Demain, date complète)

8. **Gestion des permissions de notification**
   - **Problème** : L'état "denied" n'était pas géré correctement
   - **Solution** : UI cohérente pour tous les états (default, granted, denied)

9. **Gestion des erreurs**
   - **Problème** : Pas de try/catch autour des opérations localStorage
   - **Solution** : Gestion robuste des erreurs avec feedback utilisateur

### 🚀 Nouvelles fonctionnalités

1. **Édition des tâches**
   - Modal d'édition pour modifier le texte, la catégorie et la date de rappel
   - Boutons d'édition sur chaque tâche
   - Validation des champs

2. **Tri avancé des tâches**
   - Tri par date de création (récents d'abord)
   - Tri par date de rappel (les plus proches d'abord)
   - Tri par catégorie
   - Indicateurs visuels de l'ordre de tri

3. **Affichage amélioré**
   - Dates de rappel formatées de manière lisible
   - Toasts notifications pour les actions (ajout, modification, suppression)
   - Compteur de tâches restantes amélioré

4. **Gestion robuste des notifications**
   - Nettoyage automatique des timers
   - Replanification après modification
   - Support amélioré du Service Worker

5. **Migration des données**
   - Compatibilité avec l'ancienne version (v1.0)
   - Migration automatique des données
   - Versioning du stockage

### 📊 Améliorations techniques

1. **Architecture du code**
   - Meilleure séparation des responsabilités
   - Fonctions utilitaires dédiées
   - Documentation inline améliorée

2. **Service Worker**
   - Cache plus robuste (v2)
   - Gestion des erreurs améliorée
   - Fallback intelligent pour les requêtes

3. **Manifest PWA**
   - Configuration améliorée
   - Support iOS optimisé
   - Icônes pour toutes les plateformes

4. **UI/UX**
   - Design cohérent et moderne
   - Feedback visuel pour les actions
   - Gestion du focus et des clics doubles sur mobile

### 📁 Fichiers modifiés

- `index.html` : Réécriture complète avec corrections et nouvelles fonctionnalités
- `sw.js` : Service Worker amélioré
- `manifest.webmanifest` : Configuration PWA mise à jour
- `README.md` : Documentation complète

### 🔧 Tests

- ✅ Ajout de tâche
- ✅ Suppression de tâche
- ✅ Marquer comme terminé
- ✅ Filtrage par catégorie
- ✅ Tri par différents critères
- ✅ Édition de tâche
- ✅ Notifications (quand autorisées)
- ✅ Persistance des données
- ✅ Migration depuis v1.0
- ✅ Support hors-ligne
- ✅ Installation PWA

## [1.0.0] - 2024-11-14

Version initiale avec fonctionnalités de base :
- Ajout de tâches avec catégories
- Rappels avec notifications
- Filtres de base
- Persistance via localStorage
- PWA installable
- Service Worker pour le cache offline
