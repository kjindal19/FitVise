/// <reference lib="webworker" />
// FitVise service worker (injectManifest). Provides offline precaching plus
// Web Push handling (display + click-through navigation).

import { precacheAndRoute } from "workbox-precaching";

declare let self: ServiceWorkerGlobalScope & {
  __WB_MANIFEST: Array<{ url: string; revision: string | null }>;
};

// Injected by vite-plugin-pwa at build time.
precacheAndRoute(self.__WB_MANIFEST);

self.addEventListener("install", () => {
  self.skipWaiting();
});
self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

interface PushPayload {
  title?: string;
  body?: string;
  type?: string;
  data?: { screen?: string; tab?: string; [k: string]: unknown };
  id?: string | null;
}

self.addEventListener("push", (event: PushEvent) => {
  let payload: PushPayload = {};
  try {
    payload = event.data?.json() ?? {};
  } catch {
    payload = { title: "FitVise", body: event.data?.text() };
  }
  const title = payload.title || "FitVise";
  event.waitUntil(
    self.registration.showNotification(title, {
      body: payload.body || "",
      icon: "/icons/icon.svg",
      badge: "/icons/icon.svg",
      tag: payload.type || "fitvise",
      data: payload.data || {},
    })
  );
});

self.addEventListener("notificationclick", (event: NotificationEvent) => {
  event.notification.close();
  const screen = (event.notification.data as PushPayload["data"])?.screen || "home";
  const url = `/${screen === "home" ? "" : screen}`;
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ("focus" in client) {
          client.navigate?.(url);
          return client.focus();
        }
      }
      return self.clients.openWindow(url);
    })
  );
});
