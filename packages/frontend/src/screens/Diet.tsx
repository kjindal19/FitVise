import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Api, type DietLog } from "../lib/api";
import { mutate } from "../lib/offline";
import { ScreenHeader, Label } from "../components/ui";
import { CloseIcon } from "../components/Icon";

const FLAGS = ["high_protein", "late_night_eating", "sugar_craving", "skipped_meal"];

/** Slot derived from the time of day the meal was logged. */
function slotForHour(hour: number): string {
  if (hour < 11) return "morning";
  if (hour < 16) return "afternoon";
  if (hour < 21) return "evening";
  return "night";
}

function nowHHMM(): string {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function timeLabel(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

export default function Diet() {
  const today = new Date().toISOString().slice(0, 10);
  const qc = useQueryClient();
  const { data: logs } = useQuery({
    queryKey: ["diet", today],
    queryFn: () => Api.diet(`?start_date=${today}&end_date=${today}`),
  });

  const [text, setText] = useState("");
  const [time, setTime] = useState(nowHHMM());
  const [flags, setFlags] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const entries = (logs ?? [])
    .slice()
    .sort((a, b) => a.logged_at.localeCompare(b.logged_at));

  function toggleFlag(f: string) {
    setFlags((cur) => (cur.includes(f) ? cur.filter((x) => x !== f) : [...cur, f]));
  }

  async function save() {
    if (!text.trim() || saving) return;
    setSaving(true);
    const [hh, mm] = time.split(":").map((n) => parseInt(n, 10));
    const at = new Date();
    at.setHours(hh || 0, mm || 0, 0, 0);
    await mutate("/api/v1/diet", "POST", {
      date: today,
      logged_at: at.toISOString(),
      meal_slot: slotForHour(hh || 0),
      description: text.trim(),
      protein_quality: flags.includes("high_protein") ? "high" : null,
      flags,
    });
    setText("");
    setFlags([]);
    setTime(nowHHMM());
    setSaving(false);
    qc.invalidateQueries({ queryKey: ["diet", today] });
  }

  async function remove(id: string) {
    await Api.deleteDiet(id);
    qc.invalidateQueries({ queryKey: ["diet", today] });
  }

  return (
    <div className="px-5 pb-10 pt-2">
      <ScreenHeader title="Diet journal" subtitle={today} back />
      <div className="mt-3.5 rounded-2xl border border-line bg-greenSoft p-3.5 text-[13px] text-ink2">
        Logged <b className="text-ink">{entries.length}</b>{" "}
        {entries.length === 1 ? "meal" : "meals"} today. No calories, no macros — log whatever you
        ate, whenever you ate it.
      </div>

      {/* Logged entries */}
      {entries.map((e) => (
        <Entry key={e.id} log={e} onRemove={() => remove(e.id)} />
      ))}

      {/* Add a new entry */}
      <div className="mt-3 rounded-2xl border border-dashed border-line bg-surface p-4">
        <div className="flex items-center justify-between">
          <Label>Add a meal</Label>
          <input
            type="time"
            value={time}
            onChange={(ev) => setTime(ev.target.value)}
            className="rounded-lg border border-line bg-surface2 px-2 py-1 font-mono text-xs text-ink"
          />
        </div>
        <textarea
          value={text}
          onChange={(ev) => setText(ev.target.value)}
          placeholder="What did you eat?"
          rows={2}
          className="mt-2 w-full resize-none bg-transparent text-sm text-ink outline-none"
        />
        <div className="mt-2 flex flex-wrap gap-1.5">
          {FLAGS.map((f) => {
            const on = flags.includes(f);
            return (
              <button
                key={f}
                onClick={() => toggleFlag(f)}
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
        <button
          onClick={save}
          disabled={!text.trim() || saving}
          className="mt-3.5 h-11 w-full rounded-xl bg-accent font-semibold text-white disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save meal"}
        </button>
      </div>
    </div>
  );
}

function Entry({ log, onRemove }: { log: DietLog; onRemove: () => void }) {
  return (
    <div className="mt-3 rounded-2xl border border-line bg-surface p-4">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-[0.1em] text-ink3">
          {timeLabel(log.logged_at)} · {log.meal_slot}
        </span>
        <button
          onClick={onRemove}
          aria-label="Remove meal"
          className="flex h-7 w-7 items-center justify-center rounded-full border border-line bg-surface2"
        >
          <CloseIcon size={14} stroke="var(--ink3)" />
        </button>
      </div>
      <div className="mt-2 text-sm text-ink">{log.description}</div>
      {log.flags && log.flags.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {log.flags.map((f) => (
            <span
              key={f}
              className="rounded-full bg-surface2 px-2.5 py-1 text-[11px] text-ink2"
            >
              {f.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
