"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function ProbabilityChart({
  home,
  draw,
  away,
}: {
  home: number;
  draw: number;
  away: number;
}) {
  const data = [
    { name: "1", value: Math.round(home * 100) },
    { name: "X", value: Math.round(draw * 100) },
    { name: "2", value: Math.round(away * 100) },
  ];
  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" />
          <XAxis dataKey="name" stroke="var(--muted)" />
          <YAxis unit="%" stroke="var(--muted)" domain={[0, 100]} />
          <Tooltip
            formatter={(v) => [`${v}%`, "Probabilité"]}
            contentStyle={{
              background: "var(--surface-elevated)",
              border: "1px solid var(--line)",
              borderRadius: 12,
            }}
          />
          <Bar dataKey="value" fill="#10b981" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
