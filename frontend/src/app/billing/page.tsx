"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function BillingPage() {
  const [plans, setPlans] = useState<{ plan: string; price_eur_monthly: number; features: string[] }[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.plans().then(setPlans).catch((e) => setError(e.message));
  }, []);

  const checkout = async (plan: string) => {
    setMessage(null);
    setError(null);
    try {
      const res = await api.checkout(plan, "stripe");
      if (res.checkout_url) {
        window.location.href = String(res.checkout_url);
        return;
      }
      setMessage(String(res.message || "Abonnement mis à jour"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Checkout failed");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Abonnements</h1>
        <p className="mt-2 text-sm text-muted">
          Gratuit, Premium et Pro. Paiements via Stripe ; Mobile Money disponible lorsque les credentials régionaux
          sont configurés.
        </p>
      </div>
      {message && <div className="panel border-emerald-400/40 px-4 py-3 text-sm text-emerald-700">{message}</div>}
      {error && <div className="panel px-4 py-3 text-sm text-red-600">{error}</div>}
      <div className="grid gap-4 md:grid-cols-3">
        {plans.map((plan) => (
          <article key={plan.plan} className="panel flex flex-col p-6">
            <p className="text-xs uppercase tracking-wide text-emerald-600">{plan.plan}</p>
            <h2 className="mt-2 font-display text-3xl font-semibold">
              {plan.price_eur_monthly === 0 ? "0 €" : `${plan.price_eur_monthly} €`}
              <span className="text-sm font-normal text-muted"> / mois</span>
            </h2>
            <ul className="mt-4 flex-1 space-y-2 text-sm text-muted">
              {plan.features.map((f) => (
                <li key={f}>• {f}</li>
              ))}
            </ul>
            {plan.plan !== "free" ? (
              <button
                onClick={() => checkout(plan.plan)}
                className="mt-6 rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-navy-950"
              >
                Choisir {plan.plan}
              </button>
            ) : (
              <div className="mt-6 rounded-xl border border-[var(--line)] px-4 py-2.5 text-center text-sm text-muted">
                Inclus
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
