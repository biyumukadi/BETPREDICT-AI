"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu, Moon, Sun, X } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", key: "dashboard" as const },
  { href: "/history", key: "history" as const },
  { href: "/budget", key: "budget" as const },
  { href: "/billing", key: "billing" as const },
  { href: "/admin", key: "admin" as const },
];

export function Nav() {
  const { t, locale, setLocale } = useI18n();
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [dark, setDark] = useState(false);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(!!localStorage.getItem("bp_access_token"));
    const isDark = localStorage.getItem("bp_theme") === "dark";
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    localStorage.setItem("bp_theme", next ? "dark" : "light");
    document.documentElement.classList.toggle("dark", next);
  };

  const logout = () => {
    localStorage.removeItem("bp_access_token");
    localStorage.removeItem("bp_refresh_token");
    setAuthed(false);
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--line)] bg-[color-mix(in_srgb,var(--surface)_82%,transparent)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="brand text-lg font-semibold tracking-tight text-navy-900 dark:text-white">
          <span className="text-emerald-500">BET</span>PREDICT <span className="text-emerald-500">AI</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={cn(
                "rounded-lg px-3 py-2 text-sm transition",
                pathname === l.href
                  ? "bg-navy-900 text-white dark:bg-emerald-500 dark:text-navy-950"
                  : "text-muted hover:bg-navy-900/5 dark:hover:bg-white/5"
              )}
            >
              {t[l.key]}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setLocale(locale === "fr" ? "en" : "fr")}
            className="rounded-lg border border-[var(--line)] px-2.5 py-1.5 text-xs font-semibold uppercase"
          >
            {locale}
          </button>
          <button onClick={toggleTheme} className="rounded-lg border border-[var(--line)] p-2" aria-label="theme">
            {dark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          {authed ? (
            <button onClick={logout} className="hidden rounded-lg bg-navy-900 px-3 py-2 text-sm text-white md:inline-flex dark:bg-emerald-500 dark:text-navy-950">
              {t.logout}
            </button>
          ) : (
            <Link href="/login" className="hidden rounded-lg bg-emerald-500 px-3 py-2 text-sm font-medium text-navy-950 md:inline-flex">
              {t.login}
            </Link>
          )}
          <button className="rounded-lg border border-[var(--line)] p-2 md:hidden" onClick={() => setOpen(!open)}>
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>
      {open && (
        <div className="border-t border-[var(--line)] px-4 py-3 md:hidden">
          <div className="flex flex-col gap-1">
            {links.map((l) => (
              <Link key={l.href} href={l.href} onClick={() => setOpen(false)} className="rounded-lg px-3 py-2 text-sm">
                {t[l.key]}
              </Link>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
