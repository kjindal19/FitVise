import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Api } from "../lib/api";
import { ScreenHeader } from "../components/ui";

type Tab = "weight" | "waist";

export default function Progress() {
  const [tab, setTab] = useState<Tab>("weight");
  const { data: metrics } = useQuery({ queryKey: ["metrics"], queryFn: () => Api.metrics() });

  const series = (metrics ?? [])
    .slice()
    .reverse()
    .map((m) => (tab === "weight" ? m.weight : m.waist_cm))
    .filter((v): v is number => v != null);

  const min = Math.min(...series, 0);
  const max = Math.max(...series, 1);
  const pts = series
    .map((v, i) => {
      const x = series.length > 1 ? (i / (series.length - 1)) * 300 + 10 : 160;
      const y = 140 - ((v - min) / (max - min || 1)) * 120;
      return `${x.toFixed(0)},${y.toFixed(0)}`;
    })
    .join(" ");

  return (
    <div className="px-5 pt-2">
      <ScreenHeader title="Progress" />
      <div className="mt-3 flex gap-1.5">
        {(["weight", "waist"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="rounded-full border px-3.5 py-2 text-[13px] font-semibold capitalize"
            style={{
              borderColor: tab === t ? "var(--accent)" : "var(--line)",
              background: tab === t ? "var(--accent)" : "var(--surface)",
              color: tab === t ? "#fff" : "var(--ink2)",
            }}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="mt-3.5 rounded-2xl border border-line bg-surface p-4">
        <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-ink3">
          {tab} · {series.length} readings
        </div>
        {series.length === 0 ? (
          <div className="py-10 text-center text-sm text-ink2">
            No data yet. Log a body-metrics snapshot to see your trend.
          </div>
        ) : (
          <svg className="mt-3.5 block w-full" height={160} viewBox="0 0 320 160" preserveAspectRatio="none">
            {[40, 80, 120].map((y) => (
              <line key={y} x1={0} y1={y} x2={320} y2={y} stroke="var(--line)" strokeWidth={1} />
            ))}
            <polyline points={pts} fill="none" stroke="var(--green)" strokeWidth={2.5} strokeLinecap="round" />
          </svg>
        )}
      </div>
    </div>
  );
}
