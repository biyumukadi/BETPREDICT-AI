"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function AdminPage() {
  const [overview, setOverview] = useState<Record<string, unknown> | null>(null);
  const [users, setUsers] = useState<Record<string, unknown>[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const [o, u] = await Promise.all([api.adminOverview(), api.adminUsers()]);
      setOverview(o);
      setUsers(u);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Admin access required");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const sync = async () => {
    try {
      const res = await api.adminSync();
      setMessage(JSON.stringify(res));
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sync failed");
    }
  };

  if (error && !overview) {
    return (
      <div className="panel p-6">
        <h1 className="font-display text-2xl font-semibold">Administration</h1>
        <p className="mt-2 text-sm text-red-600">{error}</p>
        <p className="mt-2 text-sm text-muted">Connexion admin requise (MFA).</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-semibold">Administration</h1>
          <p className="mt-2 text-sm text-muted">Utilisateurs, sources de données, modèles et audit.</p>
        </div>
        <button onClick={sync} className="rounded-xl bg-navy-900 px-4 py-2.5 text-sm font-semibold text-white dark:bg-emerald-500 dark:text-navy-950">
          Synchroniser données / prédictions
        </button>
      </div>
      {message && <pre className="panel overflow-auto p-4 text-xs">{message}</pre>}
      {overview && (
        <section className="grid gap-4 md:grid-cols-5">
          {Object.entries(overview).map(([k, v]) => (
            <div key={k} className="panel p-4">
              <p className="text-[11px] uppercase text-muted">{k}</p>
              <p className="mt-2 font-semibold">{String(v)}</p>
            </div>
          ))}
        </section>
      )}
      <section className="panel overflow-hidden">
        <div className="border-b border-[var(--line)] px-5 py-4">
          <h2 className="font-display text-lg font-semibold">Utilisateurs</h2>
        </div>
        <div className="divide-y divide-[var(--line)]">
          {users.map((u) => (
            <div key={String(u.id)} className="grid grid-cols-2 gap-2 px-5 py-3 text-sm md:grid-cols-4">
              <span>{String(u.email)}</span>
              <span>{String(u.full_name)}</span>
              <span className="uppercase">{String(u.role)}</span>
              <span>{u.mfa_enabled ? "MFA on" : "MFA off"}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
