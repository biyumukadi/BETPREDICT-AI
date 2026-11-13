"use client";

import { useEffect, useState } from "react";
import { DemoBanner } from "@/components/DemoBanner";
import { api, pct } from "@/lib/api";

export default function HistoryPage() {
  const [perf, setPerf] = useState<Record<string, unknown> | null>(null);
  const [history, setHistory] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.performance(), api.history()])
      .then(([p, h]) => {
        setPerf(p);
        setHistory(h);
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-6">
      <DemoBanner show />
      <div>
        <h1 className="font-display text-3xl font-semibold">Historique & performance IA</h1>
        <p className="mt-2 text-sm text-muted">
          Les statistiques publiques incluent toutes les prédictions, correctes et incorrectes. Suppression
          sélective interdite.
        </p>
      </div>

      {error && <div className="panel px-4 py-3 text-red-600">{error}</div>}

      {perf && (
        <section className="grid gap-4 md:grid-cols-4">
          {[
            ["Échantillon", String(perf.sample_size ?? 0)],
            ["Hit-rate 1X2", perf.hit_rate_1x2 != null ? pct(Number(perf.hit_rate_1x2)) : "—"],
            ["Brier moyen", perf.avg_brier != null ? Number(perf.avg_brier).toFixed(4) : "—"],
            ["Log loss", perf.avg_log_loss != null ? Number(perf.avg_log_loss).toFixed(4) : "—"],
          ].map(([label, value]) => (
            <div key={label} className="panel p-5">
              <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
              <p className="mt-2 font-display text-2xl font-semibold tabular-nums">{value}</p>
            </div>
          ))}
        </section>
      )}

      <section className="panel overflow-hidden">
        <div className="border-b border-[var(--line)] px-5 py-4">
          <h2 className="font-display text-lg font-semibold">Pronostics publiés</h2>
        </div>
        <div className="divide-y divide-[var(--line)]">
          {history.map((row, i) => {
            const fixture = row.fixture as Record<string, unknown>;
            const prediction = row.prediction as Record<string, unknown>;
            const evaluation = row.evaluation as Record<string, unknown> | null;
            return (
              <div key={i} className="grid gap-2 px-5 py-4 md:grid-cols-[1.4fr_1fr_auto]">
                <div>
                  <p className="font-medium">
                    {String(fixture.home)} vs {String(fixture.away)}
                  </p>
                  <p className="text-xs text-muted">
                    {String(fixture.competition)} · {String(fixture.kickoff_at)}
                    {fixture.is_demo ? " · DEMO" : ""}
                  </p>
                </div>
                <div className="text-sm text-muted">
                  1 {pct(Number(prediction.home_win_prob))} · X {pct(Number(prediction.draw_prob))} · 2{" "}
                  {pct(Number(prediction.away_win_prob))}
                  {fixture.score ? ` · Score ${String(fixture.score)}` : ""}
                </div>
                <div className="text-sm font-semibold">
                  {evaluation
                    ? evaluation.result_1x2_correct
                      ? "Correct"
                      : "Incorrect"
                    : "En attente"}
                </div>
              </div>
            );
          })}
          {!history.length && <p className="px-5 py-8 text-sm text-muted">Aucun historique disponible.</p>}
        </div>
      </section>
    </div>
  );
}
