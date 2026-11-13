"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { DemoBanner } from "@/components/DemoBanner";
import { ProbabilityChart } from "@/components/ProbabilityChart";
import { api, Fixture, pct, Prediction } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { formatKickoff } from "@/lib/utils";

type Detail = Fixture & {
  odds?: Record<string, unknown>[];
  value_bets?: Record<string, unknown>[];
  injuries?: { home: Record<string, unknown>[]; away: Record<string, unknown>[] };
  team_comparison?: Record<string, unknown>;
  prediction?: Prediction | null;
};

export default function MatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { locale, t } = useI18n();
  const [data, setData] = useState<Detail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .fixture(id)
      .then((d) => setData(d as Detail))
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) return <div className="panel px-4 py-6 text-red-600">{error}</div>;
  if (!data) return <div className="panel px-4 py-6 text-muted">Chargement…</div>;

  const p = data.prediction;
  const markets = p?.markets || [];

  return (
    <div className="space-y-6">
      <DemoBanner show={data.is_demo} />
      <section className="panel overflow-hidden">
        <div className="border-b border-[var(--line)] bg-navy-900 px-6 py-8 text-white">
          <p className="text-xs uppercase tracking-[0.18em] text-emerald-400">
            {data.competition.country} · {data.competition.name}
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold md:text-4xl">
            {data.home_team.name} <span className="text-emerald-400">vs</span> {data.away_team.name}
          </h1>
          <p className="mt-2 text-sm text-white/70">{formatKickoff(data.kickoff_at, locale)} · {data.venue || "—"}</p>
        </div>

        {p && (
          <div className="grid gap-6 p-6 lg:grid-cols-2">
            <div>
              <h2 className="font-display text-lg font-semibold">Probabilités 1X2</h2>
              <ProbabilityChart home={p.home_win_prob} draw={p.draw_prob} away={p.away_win_prob} />
              <p className="mt-2 text-sm text-muted">
                {t.confidence}: {pct(p.confidence)} · Score le plus probable: {p.most_likely_score} (
                {pct(p.most_likely_score_prob)})
              </p>
            </div>
            <div className="space-y-4">
              <h2 className="font-display text-lg font-semibold">Explication IA</h2>
              <p className="text-sm leading-relaxed text-muted">
                {locale === "fr" ? p.explanation_fr : p.explanation_en}
              </p>
              <div className="rounded-xl bg-amber-500/10 px-4 py-3 text-sm text-amber-800 dark:text-amber-200">
                {(p.uncertainties as { message_fr?: string; message_en?: string }).message_fr &&
                  (locale === "fr"
                    ? (p.uncertainties as { message_fr: string }).message_fr
                    : (p.uncertainties as { message_en: string }).message_en)}
              </div>
              <p className="text-xs text-muted">
                Modèle {p.model_version} · Mis à jour {new Date(p.published_at).toLocaleString(locale)}
              </p>
            </div>
          </div>
        )}
      </section>

      <section className="panel p-6">
        <h2 className="font-display text-lg font-semibold">{t.markets}</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs uppercase text-muted">
              <tr>
                <th className="py-2 pr-4">Marché</th>
                <th className="py-2 pr-4">Prédiction</th>
                <th className="py-2 pr-4">Probabilité</th>
                <th className="py-2 pr-4">Confiance</th>
              </tr>
            </thead>
            <tbody>
              {markets.map((m, i) => (
                <tr key={`${m.market}-${m.selection}-${i}`} className="border-t border-[var(--line)]">
                  <td className="py-3 pr-4">{m.market}</td>
                  <td className="py-3 pr-4 font-medium">
                    {m.selection}
                    {m.recommended ? <span className="ml-2 text-xs text-emerald-600">★</span> : null}
                  </td>
                  <td className="py-3 pr-4 tabular-nums">{pct(m.probability)}</td>
                  <td className="py-3 pr-4 tabular-nums">{pct(m.confidence)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="panel p-6">
          <h2 className="font-display text-lg font-semibold">Comparaison</h2>
          <pre className="mt-3 overflow-auto rounded-xl bg-navy-900/5 p-4 text-xs dark:bg-white/5">
            {JSON.stringify(data.team_comparison, null, 2)}
          </pre>
        </div>
        <div className="panel p-6">
          <h2 className="font-display text-lg font-semibold">{t.valueBets}</h2>
          <p className="mt-2 text-xs text-muted">
            EV = (probabilité estimée × cote) − 1. Une EV positive estimée ne garantit aucun gain réel.
          </p>
          <div className="mt-4 space-y-3">
            {(data.value_bets || []).length === 0 && (
              <p className="text-sm text-muted">Aucun value bet théorique détecté pour ce match.</p>
            )}
            {(data.value_bets || []).map((vb, i) => (
              <div key={i} className="rounded-xl border border-[var(--line)] px-4 py-3 text-sm">
                <p className="font-medium">
                  {String(vb.bookmaker)} · {String(vb.market)} · {String(vb.selection)}
                </p>
                <p className="mt-1 text-muted">
                  p={pct(Number(vb.model_probability))} · cote={String(vb.odds_decimal)} · EV=
                  {Number(vb.expected_value).toFixed(3)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="panel p-6">
        <h2 className="font-display text-lg font-semibold">Blessures / suspensions</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {(["home", "away"] as const).map((side) => (
            <div key={side}>
              <h3 className="text-sm font-semibold uppercase text-muted">{side}</h3>
              <ul className="mt-2 space-y-2 text-sm">
                {(data.injuries?.[side] || []).map((inj, i) => (
                  <li key={i} className="rounded-lg bg-navy-900/5 px-3 py-2 dark:bg-white/5">
                    {String(inj.player)} — {String(inj.status)} ({String(inj.reason)})
                    {inj.is_demo ? " · DEMO" : ""}
                  </li>
                ))}
                {(data.injuries?.[side] || []).length === 0 && (
                  <li className="text-muted">Aucune donnée confirmée</li>
                )}
              </ul>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
