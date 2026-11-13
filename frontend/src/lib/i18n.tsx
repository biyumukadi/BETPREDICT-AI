"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

type Locale = "fr" | "en";

const dict = {
  fr: {
    brand: "BETPREDICT AI",
    tagline: "Pronostics sportifs basés sur des probabilités mesurables",
    dashboard: "Tableau de bord",
    history: "Historique IA",
    budget: "Budget",
    billing: "Abonnements",
    admin: "Admin",
    login: "Connexion",
    logout: "Déconnexion",
    search: "Rechercher équipe, championnat, pays…",
    today: "Aujourd'hui",
    tomorrow: "Demain",
    week: "7 prochains jours",
    finished: "Terminés",
    confidence: "Confiance",
    markets: "Marchés",
    disclaimer:
      "Estimations statistiques uniquement. Aucun résultat n'est garanti. Service d'analyse — aucune mise n'est acceptée.",
    demo: "MODE DÉMONSTRATION — données synthétiques clairement identifiées",
    viewAnalysis: "Voir l'analyse",
    valueBets: "Value bets théoriques",
    responsible: "Jeu responsable",
  },
  en: {
    brand: "BETPREDICT AI",
    tagline: "Sports forecasts grounded in measurable probabilities",
    dashboard: "Dashboard",
    history: "AI History",
    budget: "Budget",
    billing: "Plans",
    admin: "Admin",
    login: "Sign in",
    logout: "Sign out",
    search: "Search team, league, country…",
    today: "Today",
    tomorrow: "Tomorrow",
    week: "Next 7 days",
    finished: "Finished",
    confidence: "Confidence",
    markets: "Markets",
    disclaimer:
      "Statistical estimates only. No outcome is guaranteed. Analysis service — no stakes accepted.",
    demo: "DEMO MODE — synthetic data clearly labeled",
    viewAnalysis: "View analysis",
    valueBets: "Theoretical value bets",
    responsible: "Responsible play",
  },
} as const;

type Dict = (typeof dict)[Locale];

const I18nContext = createContext<{
  locale: Locale;
  t: Dict;
  setLocale: (l: Locale) => void;
}>({ locale: "fr", t: dict.fr, setLocale: () => undefined });

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocale] = useState<Locale>("fr");
  useEffect(() => {
    const saved = localStorage.getItem("bp_locale") as Locale | null;
    if (saved === "fr" || saved === "en") setLocale(saved);
  }, []);
  const value = useMemo(
    () => ({
      locale,
      t: dict[locale],
      setLocale: (l: Locale) => {
        localStorage.setItem("bp_locale", l);
        setLocale(l);
      },
    }),
    [locale]
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}
