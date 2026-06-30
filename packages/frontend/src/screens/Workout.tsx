import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Api, type AccessoryItem } from "../lib/api";
import { mutate } from "../lib/offline";
import { ScreenHeader } from "../components/ui";
import { CheckIcon } from "../components/Icon";

interface SetRow {
  weight: number;
  reps: number;
  done: boolean;
}
interface ExRow {
  name: string;
  target: string;
  sets: SetRow[];
}

export default function Workout() {
  const nav = useNavigate();
  const { data: programme } = useQuery({
    queryKey: ["programme"],
    queryFn: Api.currentProgramme,
    retry: false,
  });

  const session = programme?.sessions?.[0];

  const initial = useMemo<ExRow[]>(() => {
    if (!session) return [];
    return session.exercises.map((e) => {
      const reps = e.reps_raw ?? (e.reps_min ? `${e.reps_min}-${e.reps_max ?? e.reps_min}` : "8-12");
      return {
        name: e.name,
        target: `${e.sets ?? 3} × ${reps}`,
        sets: Array.from({ length: e.sets ?? 3 }, () => ({
          weight: 0,
          reps: e.reps_min ?? 10,
          done: false,
        })),
      };
    });
  }, [session]);

  const [rows, setRows] = useState<ExRow[]>([]);
  const [open, setOpen] = useState(0);
  const ex = rows.length ? rows : initial;

  const update = (ei: number, si: number, patch: Partial<SetRow>) =>
    setRows(() =>
      (rows.length ? rows : initial).map((r, i) =>
        i !== ei ? r : { ...r, sets: r.sets.map((s, j) => (j !== si ? s : { ...s, ...patch })) }
      )
    );

  async function finish() {
    const today = new Date().toISOString().slice(0, 10);
    const sets = ex.flatMap((e, _ei) =>
      e.sets
        .filter((s) => s.done)
        .map((s, idx) => ({
          exercise_name: e.name,
          set_number: idx + 1,
          weight: s.weight,
          reps: s.reps,
        }))
    );
    const synced = await mutate("/api/v1/workouts", "POST", {
      session_id: programme?.sessions?.[0]?.id ?? null,
      date: today,
      completed_at: new Date().toISOString(),
      sets,
    });
    alert(synced ? "Workout saved ✓" : "Saved offline — will sync when online");
    nav("/");
  }

  return (
    <div className="pb-28 pt-2">
      <div className="px-5">
        <ScreenHeader
          title={session?.label ?? session?.session_type ?? "Workout"}
          subtitle="Active session · tap to log"
          back
          bell={false}
        />
      </div>

      {ex.length === 0 && (
        <div className="mt-10 px-5 text-center text-sm text-ink2">
          No active programme yet. Ask your AI coach to create one, then start a workout.
        </div>
      )}

      {session?.warmup && session.warmup.length > 0 && (
        <AccessoryBlock title="Warm-up" items={session.warmup} accent="var(--amber, #f59e0b)" />
      )}

      <div className="mt-4 flex flex-col gap-2.5 px-5">
        {ex.map((row, ei) => (
          <div key={ei} className="overflow-hidden rounded-2xl border border-line bg-surface">
            <button
              onClick={() => setOpen(ei)}
              className="flex w-full items-center gap-3 p-4 text-left"
            >
              <div className="flex-1">
                <div className="text-base font-semibold text-ink">{row.name}</div>
                <div className="mt-0.5 font-mono text-xs text-ink3">{row.target}</div>
              </div>
              <span className="font-mono text-xs text-ink2">
                {row.sets.filter((s) => s.done).length}/{row.sets.length}
              </span>
            </button>
            {open === ei && (
              <div className="border-t border-line px-4 pb-4">
                {row.sets.map((s, si) => (
                  <div key={si} className="flex items-center gap-1.5 border-b border-line py-2.5">
                    <span className="w-3 font-mono text-[11px] text-ink3">{si + 1}</span>
                    <Stepper value={s.weight} unit="kg" onChange={(v) => update(ei, si, { weight: v })} step={2.5} />
                    <span className="text-xs text-ink3">×</span>
                    <Stepper value={s.reps} onChange={(v) => update(ei, si, { reps: v })} step={1} />
                    <button
                      onClick={() => update(ei, si, { done: !s.done })}
                      className="ml-auto flex h-9 w-9 items-center justify-center rounded-xl border-2"
                      style={{
                        borderColor: s.done ? "var(--green)" : "var(--line)",
                        background: s.done ? "var(--green)" : "transparent",
                      }}
                    >
                      <CheckIcon size={17} stroke={s.done ? "#fff" : "var(--ink3)"} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {session?.cooldown && session.cooldown.length > 0 && (
        <AccessoryBlock title="Cool-down" items={session.cooldown} accent="var(--blue, #3b82f6)" />
      )}

      {ex.length > 0 && (
        <div
          className="absolute inset-x-0 bottom-0 px-5 py-3.5"
          style={{ background: "linear-gradient(to top,var(--bg) 70%,transparent)" }}
        >
          <button
            onClick={finish}
            className="h-13 w-full rounded-2xl bg-accent py-3.5 text-base font-semibold text-white"
          >
            Finish workout
          </button>
        </div>
      )}
    </div>
  );
}

function AccessoryBlock({
  title,
  items,
  accent,
}: {
  title: string;
  items: AccessoryItem[];
  accent: string;
}) {
  const [done, setDone] = useState<boolean[]>(() => items.map(() => false));
  return (
    <div className="mt-4 px-5">
      <div className="flex items-center gap-2">
        <span className="h-2.5 w-2.5 rounded-full" style={{ background: accent }} />
        <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-ink3">
          {title}
        </span>
      </div>
      <div className="mt-2 overflow-hidden rounded-2xl border border-line bg-surface">
        {items.map((it, i) => (
          <button
            key={i}
            onClick={() => setDone((d) => d.map((v, j) => (j === i ? !v : v)))}
            className="flex w-full items-center gap-3 border-b border-line p-3.5 text-left last:border-b-0"
          >
            <span
              className="flex h-7 w-7 items-center justify-center rounded-lg border-2"
              style={{
                borderColor: done[i] ? accent : "var(--line)",
                background: done[i] ? accent : "transparent",
              }}
            >
              <CheckIcon size={15} stroke={done[i] ? "#fff" : "var(--ink3)"} />
            </span>
            <div className="flex-1">
              <div
                className="text-[14px] font-medium text-ink"
                style={{ textDecoration: done[i] ? "line-through" : "none", opacity: done[i] ? 0.6 : 1 }}
              >
                {it.name}
              </div>
              {(it.reps || it.notes) && (
                <div className="mt-0.5 text-xs text-ink3">
                  {[it.reps, it.notes].filter(Boolean).join(" · ")}
                </div>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function Stepper({
  value,
  onChange,
  step,
  unit,
}: {
  value: number;
  onChange: (v: number) => void;
  step: number;
  unit?: string;
}) {
  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => onChange(Math.max(0, Math.round((value - step) * 100) / 100))}
        className="h-9 w-8 rounded-lg border border-line bg-surface2 text-lg text-ink"
      >
        −
      </button>
      <span className="w-8 text-center font-mono text-[15px] font-semibold text-ink">{value}</span>
      <button
        onClick={() => onChange(Math.round((value + step) * 100) / 100)}
        className="h-9 w-8 rounded-lg border border-line bg-surface2 text-lg text-ink"
      >
        +
      </button>
      {unit && <span className="text-[11px] text-ink3">{unit}</span>}
    </div>
  );
}
