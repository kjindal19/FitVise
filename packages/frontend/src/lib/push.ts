// Web Push subscription helper. Fetches the VAPID public key from the backend,
// asks for notification permission, subscribes via the service worker, and
// registers the subscription with FitVise.

import { Api } from "./api";

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
}

export async function isPushSupported(): Promise<boolean> {
  return "serviceWorker" in navigator && "PushManager" in window;
}

export async function enablePush(): Promise<{ ok: boolean; reason?: string }> {
  if (!(await isPushSupported())) return { ok: false, reason: "unsupported" };

  const { public_key, enabled } = await Api.vapidKey();
  if (!enabled || !public_key)
    return { ok: false, reason: "Web Push not configured on the server (no VAPID keys)." };

  const permission = await Notification.requestPermission();
  if (permission !== "granted") return { ok: false, reason: "permission-denied" };

  const reg = await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(public_key) as BufferSource,
  });

  const json = sub.toJSON();
  await Api.subscribePush({
    endpoint: sub.endpoint,
    keys: { p256dh: json.keys?.p256dh, auth: json.keys?.auth },
    user_agent: navigator.userAgent,
  });
  return { ok: true };
}
