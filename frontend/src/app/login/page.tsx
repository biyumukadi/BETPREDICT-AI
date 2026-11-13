"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function LoginPage() {
  const { t } = useI18n();
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("user@betpredict.ai");
  const [password, setPassword] = useState("User123!");
  const [fullName, setFullName] = useState("");
  const [dob, setDob] = useState("1995-01-01");
  const [mfa, setMfa] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const tokens =
        mode === "login"
          ? await api.login(email, password, mfa || undefined)
          : await api.register({
              email,
              password,
              full_name: fullName || "Utilisateur",
              date_of_birth: dob,
              locale: "fr",
            });
      localStorage.setItem("bp_access_token", tokens.access_token);
      localStorage.setItem("bp_refresh_token", tokens.refresh_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auth failed");
    }
  };

  return (
    <div className="mx-auto max-w-md space-y-6">
      <div className="text-center">
        <p className="brand text-sm font-semibold uppercase tracking-[0.2em] text-emerald-600">BETPREDICT AI</p>
        <h1 className="mt-2 font-display text-3xl font-semibold">{mode === "login" ? t.login : "Créer un compte"}</h1>
        <p className="mt-2 text-sm text-muted">Vérification d&apos;âge légal obligatoire (+18).</p>
      </div>
      <form onSubmit={submit} className="panel space-y-4 p-6">
        {mode === "register" && (
          <>
            <input
              className="w-full rounded-xl border border-[var(--line)] bg-transparent px-3 py-3 text-sm"
              placeholder="Nom complet"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
            <input
              type="date"
              className="w-full rounded-xl border border-[var(--line)] bg-transparent px-3 py-3 text-sm"
              value={dob}
              onChange={(e) => setDob(e.target.value)}
              required
            />
          </>
        )}
        <input
          type="email"
          className="w-full rounded-xl border border-[var(--line)] bg-transparent px-3 py-3 text-sm"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          className="w-full rounded-xl border border-[var(--line)] bg-transparent px-3 py-3 text-sm"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {mode === "login" && (
          <input
            className="w-full rounded-xl border border-[var(--line)] bg-transparent px-3 py-3 text-sm"
            placeholder="Code MFA admin (si activé)"
            value={mfa}
            onChange={(e) => setMfa(e.target.value)}
          />
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" className="w-full rounded-xl bg-emerald-500 py-3 text-sm font-semibold text-navy-950">
          {mode === "login" ? t.login : "S'inscrire"}
        </button>
        <button
          type="button"
          className="w-full text-sm text-emerald-600"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login" ? "Créer un compte" : "Déjà inscrit ? Connexion"}
        </button>
        <p className="text-xs text-muted">
          Comptes démo : user@betpredict.ai / User123! · premium@betpredict.ai / Premium123! ·
          admin@betpredict.ai / Admin123! (MFA 000000)
        </p>
      </form>
    </div>
  );
}
