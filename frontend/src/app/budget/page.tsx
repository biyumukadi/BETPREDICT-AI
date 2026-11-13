"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function BudgetPage() {
  const { locale, t } = useI18n();
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stake, setStake] = useState({ market: "1x2", selection: "1", stake_amount: 5, odds_decimal: 2.0 });

  const load = () =>
    api
      .budget()
      .then(setData)
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  const onStake = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api.addStake(stake);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  };

  if (error && !data) {
    return (
      <div className="panel p-6">
        <p className="text-sm text-red-600">{error}</p>
        <p className="mt-2 text-sm text-muted">Connectez-vous pour gérer votre budget responsable.</p>
      </div>
    );
  }

  const profile = (data?.profile || {}) as Record<string, unknown>;
  const decisions = (data?.decisions || []) as Record<string, unknown>[];
  const alerts = (data?.alerts || []) as string[];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">{t.budget}</h1>
        <p className="mt-2 max-w-3xl text-sm text-muted">
          {locale === "fr"
            ? String(data?.responsible_gaming_notice_fr || "")
            : String(data?.responsible_gaming_notice_en || "")}
        </p>
      </div>

      {alerts.length > 0 && (
        <div className="rounded-2xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-800 dark:text-amber-200">
          {alerts.join(" · ")}
        </div>
      )}

      <section className="grid gap-4 md:grid-cols-4">
        {[
          ["Budget max", `${profile.max_budget ?? "—"} ${profile.currency ?? ""}`],
          ["Misés", `${profile.total_staked ?? 0}`],
          ["Retours", `${profile.total_returned ?? 0}`],
          ["ROI", profile.roi != null ? `${(Number(profile.roi) * 100).toFixed(1)}%` : "—"],
        ].map(([k, v]) => (
          <div key={k} className="panel p-5">
            <p className="text-xs uppercase text-muted">{k}</p>
            <p className="mt-2 font-display text-2xl font-semibold tabular-nums">{v}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={onStake} className="panel space-y-3 p-6">
          <h2 className="font-display text-lg font-semibold">Enregistrer une décision</h2>
          <p className="text-xs text-muted">
            Suivi personnel uniquement. Aucune stratégie de récupération automatique des pertes.
          </p>
          <input
            className="w-full rounded-xl border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
            value={stake.market}
            onChange={(e) => setStake({ ...stake, market: e.target.value })}
            placeholder="Marché"
          />
          <input
            className="w-full rounded-xl border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
            value={stake.selection}
            onChange={(e) => setStake({ ...stake, selection: e.target.value })}
            placeholder="Sélection"
          />
          <input
            type="number"
            step="0.01"
            className="w-full rounded-xl border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
            value={stake.stake_amount}
            onChange={(e) => setStake({ ...stake, stake_amount: Number(e.target.value) })}
          />
          <input
            type="number"
            step="0.01"
            className="w-full rounded-xl border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
            value={stake.odds_decimal}
            onChange={(e) => setStake({ ...stake, odds_decimal: Number(e.target.value) })}
          />
          <button className="rounded-xl bg-navy-900 px-4 py-2.5 text-sm font-semibold text-white dark:bg-emerald-500 dark:text-navy-950">
            Enregistrer
          </button>
        </form>

        <div className="panel p-6">
          <h2 className="font-display text-lg font-semibold">Historique des décisions</h2>
          <div className="mt-4 space-y-2">
            {decisions.map((d) => (
              <div key={String(d.id)} className="rounded-xl border border-[var(--line)] px-3 py-2 text-sm">
                {String(d.decision_date)} · {String(d.market)}/{String(d.selection)} · {String(d.stake_amount)} ·{" "}
                {String(d.result)}
              </div>
            ))}
            {!decisions.length && <p className="text-sm text-muted">Aucune décision enregistrée.</p>}
          </div>
        </div>
      </section>
    </div>
  );
}
