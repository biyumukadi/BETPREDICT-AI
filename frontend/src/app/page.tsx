"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { DemoBanner } from "@/components/DemoBanner";
import { MatchCard } from "@/components/MatchCard";
import { api, Dashboard, Fixture } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function DashboardPage() {
  const { t, locale } = useI18n();
  const [data, setData] = useState<Dashboard | null>(null);
  const [competitionId, setCompetitionId] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Fixture[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .dashboard(competitionId || undefined)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [competitionId]);

  const onSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      setResults(null);
      return;
    }
    try {
      setResults(await api.search(query.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    }
  };

  const sections = useMemo(() => {
    if (!data) return [];
    return [
      { title: t.today, items: data.today },
      { title: t.tomorrow, items: data.tomorrow },
      { title: t.week, items: data.next_7_days },
      { title: t.finished, items: data.finished },
    ];
  }, [data, t]);

  return (
    <div className="space-y-8">
      <DemoBanner show={!!data?.demo_mode || process.env.NEXT_PUBLIC_DEMO_MODE === "true"} />

      <section className="relative overflow-hidden rounded-3xl border border-[var(--line)] bg-navy-900 text-white shadow-soft">
        <div
          className="absolute inset-0 opacity-40"
          style={{
            background:
              "radial-gradient(circle at 20% 20%, rgba(16,185,129,.35), transparent 40%), radial-gradient(circle at 80% 0%, rgba(52,211,153,.2), transparent 35%)",
          }}
        />
        <div className="relative grid gap-6 px-6 py-10 md:grid-cols-[1.2fr_0.8fr] md:px-10">
          <div>
            <p className="brand text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400">
              BETPREDICT AI
            </p>
            <h1 className="mt-3 max-w-xl font-display text-3xl font-semibold leading-tight md:text-5xl">
              {t.tagline}
            </h1>
            <p className="mt-4 max-w-xl text-sm text-white/75 md:text-base">
              {locale === "fr" ? data?.disclaimer_fr || t.disclaimer : data?.disclaimer_en || t.disclaimer}
            </p>
          </div>
          <form onSubmit={onSearch} className="flex flex-col justify-end gap-3">
            <label className="text-xs uppercase tracking-wide text-white/60">{t.search}</label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-navy-700/50" size={16} />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t.search}
                  className="w-full rounded-xl border-0 bg-white py-3 pl-10 pr-3 text-sm text-navy-900 outline-none"
                />
              </div>
              <button type="submit" className="rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-navy-950">
                OK
              </button>
            </div>
            <select
              value={competitionId}
              onChange={(e) => setCompetitionId(e.target.value)}
              className="rounded-xl border-0 bg-white/10 px-3 py-3 text-sm text-white outline-none"
            >
              <option value="">Tous les championnats</option>
              {data?.competitions.map((c) => (
                <option key={c.id} value={c.id} className="text-navy-900">
                  {c.country} — {c.name}
                </option>
              ))}
            </select>
          </form>
        </div>
      </section>

      {error && <div className="panel border-red-300 px-4 py-3 text-sm text-red-700">{error}</div>}
      {loading && <div className="panel px-4 py-8 text-center text-muted">Chargement des rencontres…</div>}

      {results && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl font-semibold">Résultats</h2>
            <button className="text-sm text-emerald-600" onClick={() => setResults(null)}>
              Effacer
            </button>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {results.map((f) => (
              <MatchCard key={f.id} fixture={f} />
            ))}
          </div>
        </section>
      )}

      {!results &&
        sections.map((section) =>
          section.items.length ? (
            <section key={section.title} className="space-y-4">
              <h2 className="font-display text-xl font-semibold">{section.title}</h2>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {section.items.map((f) => (
                  <MatchCard key={f.id} fixture={f} />
                ))}
              </div>
            </section>
          ) : null
        )}
    </div>
  );
}
