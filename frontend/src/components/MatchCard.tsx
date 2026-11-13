"use client";

import Link from "next/link";
import { Fixture, pct } from "@/lib/api";
import { formatKickoff } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";

export function MatchCard({ fixture }: { fixture: Fixture }) {
  const { locale, t } = useI18n();
  const p = fixture.prediction;
  const score =
    fixture.home_score != null && fixture.away_score != null
      ? `${fixture.home_score} – ${fixture.away_score}`
      : null;

  return (
    <article className="panel group overflow-hidden transition hover:-translate-y-0.5 hover:shadow-soft">
      <div className="flex items-start justify-between gap-3 border-b border-[var(--line)] px-4 py-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted">
            {fixture.competition.country} · {fixture.competition.name}
          </p>
          <p className="mt-1 text-sm text-muted">{formatKickoff(fixture.kickoff_at, locale)}</p>
        </div>
        <div className="flex items-center gap-2">
          {fixture.is_demo && (
            <span className="rounded-md bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-emerald-700 dark:text-emerald-300">
              Demo
            </span>
          )}
          <span className="rounded-md bg-navy-900/5 px-2 py-0.5 text-[10px] font-semibold uppercase text-navy-800 dark:bg-white/10 dark:text-white">
            {fixture.status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 px-4 py-5">
        <div className="text-right">
          <p className="font-display text-base font-semibold leading-tight">{fixture.home_team.name}</p>
          <p className="mt-1 text-xs text-muted">Elo {Math.round(fixture.home_team.elo_rating)}</p>
        </div>
        <div className="min-w-[4.5rem] text-center">
          {score ? (
            <p className="font-display text-2xl font-semibold tabular-nums">{score}</p>
          ) : (
            <p className="font-display text-sm font-medium text-muted">vs</p>
          )}
        </div>
        <div>
          <p className="font-display text-base font-semibold leading-tight">{fixture.away_team.name}</p>
          <p className="mt-1 text-xs text-muted">Elo {Math.round(fixture.away_team.elo_rating)}</p>
        </div>
      </div>

      {p && (
        <div className="space-y-3 border-t border-[var(--line)] px-4 py-4">
          <div className="grid grid-cols-3 gap-2 text-center text-sm">
            <div className="rounded-xl bg-navy-900/5 px-2 py-2 dark:bg-white/5">
              <p className="text-[11px] uppercase text-muted">1</p>
              <p className="font-semibold tabular-nums">{pct(p.home_win_prob)}</p>
            </div>
            <div className="rounded-xl bg-navy-900/5 px-2 py-2 dark:bg-white/5">
              <p className="text-[11px] uppercase text-muted">X</p>
              <p className="font-semibold tabular-nums">{pct(p.draw_prob)}</p>
            </div>
            <div className="rounded-xl bg-navy-900/5 px-2 py-2 dark:bg-white/5">
              <p className="text-[11px] uppercase text-muted">2</p>
              <p className="font-semibold tabular-nums">{pct(p.away_win_prob)}</p>
            </div>
          </div>
          <div className="flex items-center justify-between text-xs text-muted">
            <span>
              {t.confidence}: {pct(p.confidence)}
            </span>
            <span>
              xG {p.expected_home_goals.toFixed(2)}–{p.expected_away_goals.toFixed(2)}
            </span>
          </div>
          <Link
            href={`/matches/${fixture.id}`}
            className="inline-flex w-full items-center justify-center rounded-xl bg-emerald-500 px-3 py-2.5 text-sm font-semibold text-navy-950 transition group-hover:bg-emerald-400"
          >
            {t.viewAnalysis}
          </Link>
        </div>
      )}
    </article>
  );
}
