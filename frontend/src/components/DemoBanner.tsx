"use client";

import { useI18n } from "@/lib/i18n";

export function DemoBanner({ show, text }: { show: boolean; text?: string }) {
  const { t } = useI18n();
  if (!show) return null;
  return (
    <div className="w-full border-b border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-center text-sm font-medium text-emerald-700 dark:text-emerald-300">
      {text || t.demo}
    </div>
  );
}
