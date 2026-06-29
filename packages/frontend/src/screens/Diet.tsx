import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Api } from "../lib/api";
import { mutate } from "../lib/offline";
import { ScreenHeader, Label } from "../components/ui";

const SLOTS = ["morning", "afternoon", "evening", "night"];
const FLAGS = ["high_protein", "late_night_eating", "sugar_craving", "skipped_meal"];

export default function Diet() {
  const today = new Date().toISOString().slice(0, 10);
  const qc = useQueryClient();
  const { data: logs } = useQuery({
    queryKey: ["diet", today],
    queryFn: () => Api.diet(`?start_date=${today}&end_date=${today}`),
  });
  const [draft, setDraft] = useState<Record<string, { text: string; flags: string[] }>>({});

  const logged = new Set((logs ?? []).map((l) => l.meal_slot));

  async function save(slot: string) {
    const d = draft[slot];
    if (!d?.text) return;
    await mutate("/api/v1/diet", "POST", {
      date: today,
      meal_slot: slot,
      description: d.text,
      protein_quality: d.flags.includes("high_protein") ? "high" : null,
      flags: d.flags,
    });
    setDraft((s) => ({ ...s, [slot]: { text: "", flags: [] } }));
    qc.invalidateQueries({ queryKey: ["diet", today] });
  }

  return (
    <div className="px-5 pt-2">
      <ScreenHeader title="Diet journal" subtitle={today} back />
      <div className="mt-3.5 rounded-2xl border border-line bg-greenSoft p-3.5 text-[13px] text-ink2">
        Logged <b className="text-ink">{logged.size} of 4</b> meals today. No calories, no macros —
        just what you ate.
      </div>

      {SLOTS.map((slot) => {
        const existing = (logs ?? []).find((l) => l.meal_slot === slot);
        return (
          <div key={slot} className="mt-3 rounded-2xl border border-line bg-surface p-4">
            <Label>{slot}</Label>
            {existing ? (
              <div className="mt-2 text-sm text-ink">{existing.description}</div>
            ) : (
              <>
                <input
                  value={draft[slot]?.text ?? ""}
                  onChange={(e) =>
                    setDraft((s) => ({
                      ...s,
                      [slot]: { text: e.target.value, flags: s[slot]?.flags ?? [] },
                    }))
                  }
                  onBlur={() => save(slot)}
                  placeholder="What did you eat?"
                  className="mt-2 w-full bg-transparent text-sm text-ink outline-none"
                />
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {FLAGS.map((f) => {
                    const on = draft[slot]?.flags?.includes(f);
                    return (
                      <button
                        key={f}
                        onClick={() =>
                          setDraft((s) => {
                            const cur = s[slot]?.flags ?? [];
                            const flags = on ? cur.filter((x) => x !== f) : [...cur, f];
                            return { ...s, [slot]: { text: s[slot]?.text ?? "", flags } };
                          })
                        }
                        className="rounded-full border border-line px-2.5 py-1 text-[11px]"
                        style={{
                          background: on ? "var(--accentSoft)" : "var(--surface2)",
                          color: on ? "var(--accent)" : "var(--ink2)",
                        }}
                      >
                        {f.replace(/_/g, " ")}
                      </button>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}
