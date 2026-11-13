"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function NotificationsPage() {
  const [prefs, setPrefs] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api
      .notificationPrefs()
      .then(setPrefs)
      .catch((e) => setError(e.message));
  }, []);

  const toggle = async (key: string) => {
    if (!prefs) return;
    const next = { ...prefs, [key]: !prefs[key] };
    if (key === "telegram_enabled" && next.telegram_enabled) next.consent_telegram = true;
    if (key === "whatsapp_enabled" && next.whatsapp_enabled) next.consent_whatsapp = true;
    setPrefs(next);
    try {
      await api.updateNotificationPrefs(next);
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    }
  };

  if (error && !prefs) {
    return <div className="panel p-6 text-sm text-red-600">{error}</div>;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Notifications</h1>
        <p className="mt-2 text-sm text-muted">
          Push, email, et (avec consentement) Telegram / WhatsApp Business.
        </p>
      </div>
      <div className="panel divide-y divide-[var(--line)]">
        {prefs &&
          [
            "push_enabled",
            "email_enabled",
            "new_analysis",
            "lineup_changes",
            "injuries",
            "probability_shifts",
            "match_results",
            "telegram_enabled",
            "whatsapp_enabled",
          ].map((key) => (
            <label key={key} className="flex items-center justify-between px-5 py-4 text-sm">
              <span>{key}</span>
              <input type="checkbox" checked={!!prefs[key]} onChange={() => toggle(key)} />
            </label>
          ))}
      </div>
      {saved && <p className="text-sm text-emerald-600">Préférences enregistrées.</p>}
    </div>
  );
}
