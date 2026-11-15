// Service Worker pour Todoliste - Version 2.0
// Gestion du cache offline et des notifications

const CACHE_NAME = "todoliste-v2";
const ASSETS_TO_CACHE = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon-180.png",
  "./icons/icon-192.png",
  "./icons/icon-512.png"
];

// Installation : mise en cache des assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        // Ajouter tous les assets au cache
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => {
        // Passer directement à l'activation
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error("Erreur lors de l'installation du cache:", error);
      })
  );
});

// Activation : nettoyage des anciens caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      // Supprimer tous les caches qui ne sont pas le cache actuel
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log("Suppression de l'ancien cache:", cacheName);
            return caches.delete(cacheName);
          }
          return Promise.resolve();
        })
      );
    })
    .then(() => {
      // Prendre le contrôle des clients immédiatement
      return self.clients.claim();
    })
    .catch((error) => {
      console.error("Erreur lors de l'activation:", error);
    })
  );
});

// Interception des requêtes : stratégie cache-first avec fallback
self.addEventListener("fetch", (event) => {
  // Ne pas intercepter les requêtes POST ou autres méthodes non-GET
  if (event.request.method !== "GET") {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        // Retourner la réponse en cache si disponible
        if (cachedResponse) {
          return cachedResponse;
        }

        // Sinon, faire la requête réseau
        return fetch(event.request).then((response) => {
          // Cloner la réponse pour la mettre en cache
          const responseClone = response.clone();
          
          // Mettre à jour le cache
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
          
          return response;
        });
      })
      .catch((error) => {
        console.error("Erreur lors de la récupération:", error);
        
        // Fallback : retourner index.html pour les requêtes de navigation
        if (event.request.mode === "navigate" || 
            (event.request.method === "GET" && 
             event.request.headers.get("accept").includes("text/html"))) {
          return caches.match("./index.html");
        }
        
        // Retourner une réponse d'erreur
        return new Response(null, { status: 500 });
      })
  );
});

// Gestion des clics sur les notifications
self.addEventListener("notificationclick", (event) => {
  // Fermer la notification
  event.notification.close();
  
  // Trouver le client (fenêtre) ouvert
  event.waitUntil(
    self.clients.matchAll({ type: "window" }).then((clients) => {
      // Focus sur un client existant
      for (const client of clients) {
        if (client.focus) {
          return client.focus();
        }
      }
      
      // Sinon, ouvrir une nouvelle fenêtre
      return self.clients.openWindow("./index.html");
    })
  );
});

// Gestion de la fermeture des notifications
self.addEventListener("notificationclose", (event) => {
  // Peut être utilisé pour nettoyer ou logger
  console.log("Notification fermée:", event.notification.tag);
});

// Gestion des messages depuis le client
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

// Écouter les erreurs
self.addEventListener("error", (error) => {
  console.error("Erreur dans le service worker:", error);
});
