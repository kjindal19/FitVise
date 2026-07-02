import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Api, type AccessoryItem, type WorkoutLog } from "../lib/api";
import { mutate } from "../lib/offline";
import { useAuth } from "../lib/auth";
import { ScreenHeader } from "../components/ui";
import { MinusIcon } from "../components/Icon";
import { toISODate, todaySession } from "../lib/programme";

interface SetRow {
  // null weight = bodyweight / no added load.
  weight: number | null;
  reps: number;
}
interface ExRow {
  name: string;
  target: string;
  sets: SetRow[];
}

/** Most recent logged { weight, reps } per exercise, for sensible defaults. */
type LastMap = Record<string, { weight: number | null; reps: number }>;

/** Rebuild editable rows from a saved log, grouping its sets by exercise. */
function rowsFromLog(log: WorkoutLog): ExRow[] {
  const order: string[] = [];
  const byName = new Map<string, SetRow[]>();
  const sorted = [...log.sets].sort((a, b) => (a.set_number ?? 0) - (b.set_number ?? 0));
  for (const s of sorted) {
    if (!byName.has(s.exercise_name)) {
      byName.set(s.exercise_name, []);
      order.push(s.exercise_name);
    }
    byName.get(s.exercise_name)!.push({ weight: s.weight ?? null, reps: s.reps ?? 0 });
  }
  return order.map((name) => {
    const sets = byName.get(name)!;
    return { name, target: `${sets.length} ${sets.length === 1 ? "set" : "sets"}`, sets };
  });
}

export default function Workout() {
  const nav = useNavigate();
  const [params] = useSearchParams();
  const { user } = useAuth();
  const weightUnit = user?.weight_unit ?? "kg";

  // The day being logged. Defaults to today; a ?date=YYYY-MM-DD opens a past
  // session (from the history screen) for viewing/editing.
  const dateISO = params.get("date") ?? toISODate();
  const isToday = dateISO === toISODate();
  // Parse with an explicit time so it's the local day, not UTC midnight.
  const dateObj = useMemo(() => new Date(`${dateISO}T00:00:00`), [dateISO]);

  const { data: programme } = useQuery({
    queryKey: ["programme"],
    queryFn: Api.currentProgramme,
    retry: false,
  });

  // Last ~8 weeks of logs so we can pre-fill each exercise with last time's load.
  // Extend the window back to the selected date so an older log still loads to edit;
  // prefill still picks the most-recent set since the list is ordered date-desc.
  const eightWeeksAgo = toISODate(new Date(Date.now() - 56 * 86400_000));
  const since = dateISO < eightWeeksAgo ? dateISO : eightWeeksAgo;
  const { data: history } = useQuery({
    queryKey: ["workouts", "history", since],
    queryFn: () => Api.workouts(`?start_date=${since}`),
  });

  const existing = (history ?? []).find((w) => w.date === dateISO);
  const session = todaySession(programme, dateObj);

  const lastByExercise = useMemo<LastMap>(() => {
    const map: LastMap = {};
    // history is ordered date desc, so the first time we see an exercise is the
    // most recent session it appeared in.
    for (const log of history ?? []) {
      for (const s of log.sets) {
        const key = s.exercise_name.toLowerCase();
        if (!(key in map)) map[key] = { weight: s.weight ?? null, reps: s.reps ?? 10 };
      }
    }
    return map;
  }, [history]);

  const initial = useMemo<ExRow[]>(() => {
    // An existing log for this date wins — we're editing what was saved.
    if (existing && existing.sets.length) return rowsFromLog(existing);
    if (!session) return [];
    return session.exercises.map((e) => {
      const reps = e.reps_raw ?? (e.reps_min ? `${e.reps_min}-${e.reps_max ?? e.reps_min}` : "8-12");
      const last = lastByExercise[e.name.toLowerCase()];
      const defaultReps = last?.reps ?? e.reps_min ?? 10;
      const defaultWeight = last ? last.weight : 0;
      return {
        name: e.name,
        target: `${e.sets ?? 3} × ${reps}`,
        sets: Array.from({ length: e.sets ?? 3 }, () => ({
          weight: defaultWeight,
          reps: defaultReps,
        })),
      };
    });
  }, [existing, session, lastByExercise]);

  const [rows, setRows] = useState<ExRow[] | null>(null);
  const [open, setOpen] = useState(0);

  // Seed editable state once the programme + history have resolved.
  useEffect(() => {
    if (initial.length) setRows(initial);
  }, [initial]);

  const ex = rows ?? initial;

  const setExercise = (ei: number, fn: (r: ExRow) => ExRow) =>
    setRows((prev) => (prev ?? initial).map((r, i) => (i === ei ? fn(r) : r)));

  const updateSet = (ei: number, si: number, patch: Partial<SetRow>) =>
    setExercise(ei, (r) => ({
      ...r,
      sets: r.sets.map((s, j) => (j === si ? { ...s, ...patch } : s)),
    }));

  const addSet = (ei: number) =>
    setExercise(ei, (r) => {
      // New set inherits the previous set's load (or a sensible default).
      const prev = r.sets[r.sets.length - 1] ?? { weight: 0, reps: 10 };
      return { ...r, sets: [...r.sets, { ...prev }] };
    });

  const removeSet = (ei: number, si: number) =>
    setExercise(ei, (r) => ({ ...r, sets: r.sets.filter((_, j) => j !== si) }));

  async function finish() {
    const sets = ex.flatMap((e) =>
      e.sets.map((s, idx) => ({
        exercise_name: e.name,
        set_number: idx + 1,
        weight: s.weight, // null = bodyweight
        reps: s.reps,
      }))
    );
    if (sets.length === 0) {
      alert("Add at least one set before finishing.");
      return;
    }
    const synced = await mutate("/api/v1/workouts", "POST", {
      session_id: session?.id ?? null,
      date: dateISO,
      completed_at: new Date().toISOString(),
      sets,
    });
    const verb = existing ? "updated" : "saved";
    alert(synced ? `Workout ${verb} ✓` : "Saved offline — will sync when online");
    nav("/");
  }

  return (
    <div className="pb-28 pt-2">
      <div className="px-5">
        <ScreenHeader
          title={session?.label ?? session?.session_type ?? "Workout"}
          subtitle={
            isToday
              ? "Active session · tap to log"
              : dateObj.toLocaleDateString(undefined, {
                  weekday: "long",
                  month: "short",
                  day: "numeric",
                })
          }
          back
          bell={false}
        />
        <button
          onClick={() => nav("/workout/history")}
          className="mt-2 text-xs font-medium text-accent"
        >
          Past workouts ›
        </button>
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
              onClick={() => setOpen(open === ei ? -1 : ei)}
              className="flex w-full items-center gap-3 p-4 text-left"
            >
              <div className="flex-1">
                <div className="text-base font-semibold text-ink">{row.name}</div>
                <div className="mt-0.5 font-mono text-xs text-ink3">{row.target}</div>
              </div>
              <span className="font-mono text-xs text-ink2">
                {row.sets.length} {row.sets.length === 1 ? "set" : "sets"}
              </span>
            </button>
            {open === ei && (
              <div className="border-t border-line px-4 pb-3 pt-1">
                <div className="flex items-center gap-2 px-1 pb-1 font-mono text-[10px] uppercase tracking-wide text-ink3">
                  <span className="w-4">#</span>
                  <span className="flex-1">Weight</span>
                  <span className="w-16 text-center">Reps</span>
                  <span className="w-8" />
                </div>
                {row.sets.map((s, si) => (
                  <div key={si} className="flex items-center gap-2 border-b border-line py-2.5 last:border-b-0">
                    <span className="w-4 font-mono text-[11px] text-ink3">{si + 1}</span>
                    <WeightInput
                      value={s.weight}
                      unit={weightUnit}
                      onChange={(v) => updateSet(ei, si, { weight: v })}
                    />
                    <NumberInput
                      value={s.reps}
                      onChange={(v) => updateSet(ei, si, { reps: v })}
                      className="w-16"
                    />
                    <button
                      onClick={() => removeSet(ei, si)}
                      aria-label="Remove set"
                      className="flex h-9 w-8 items-center justify-center rounded-lg border border-line bg-surface2"
                    >
                      <MinusIcon size={16} stroke="var(--ink3)" />
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => addSet(ei)}
                  className="mt-3 h-10 w-full rounded-xl border border-dashed border-line text-[13px] font-medium text-ink2"
                >
                  + Add set
                </button>
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
            {existing ? "Update workout" : "Finish workout"}
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
              {done[i] && (
                <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={3}>
                  <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
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

/**
 * Weight entry: free decimal input (e.g. 4, 6, 7.5) with −/+ nudge buttons.
 * An empty value means bodyweight (logged as null) and shows a "BW" hint.
 */
function WeightInput({
  value,
  unit,
  onChange,
}: {
  value: number | null;
  unit: string;
  onChange: (v: number | null) => void;
}) {
  const round = (n: number) => Math.round(n * 100) / 100;
  const nudge = (delta: number) => onChange(round(Math.max(0, (value ?? 0) + delta)));
  return (
    <div className="flex flex-1 items-center gap-1">
      <button
        onClick={() => nudge(-2.5)}
        className="h-9 w-8 shrink-0 rounded-lg border border-line bg-surface2 text-lg text-ink"
      >
        −
      </button>
      <input
        inputMode="decimal"
        value={value ?? ""}
        placeholder="BW"
        onChange={(e) => {
          const raw = e.target.value.trim();
          if (raw === "") return onChange(null);
          const n = Number(raw);
          if (!Number.isNaN(n)) onChange(n);
        }}
        className="w-full min-w-0 rounded-lg border border-line bg-surface2 py-1.5 text-center font-mono text-[15px] font-semibold text-ink outline-none"
      />
      <button
        onClick={() => nudge(2.5)}
        className="h-9 w-8 shrink-0 rounded-lg border border-line bg-surface2 text-lg text-ink"
      >
        +
      </button>
      <span className="shrink-0 text-[11px] text-ink3">{unit}</span>
    </div>
  );
}

function NumberInput({
  value,
  onChange,
  className = "",
}: {
  value: number;
  onChange: (v: number) => void;
  className?: string;
}) {
  return (
    <input
      inputMode="numeric"
      value={Number.isFinite(value) ? value : ""}
      onChange={(e) => {
        const raw = e.target.value.trim();
        if (raw === "") return onChange(0);
        const n = parseInt(raw, 10);
        if (!Number.isNaN(n)) onChange(n);
      }}
      className={`rounded-lg border border-line bg-surface2 py-1.5 text-center font-mono text-[15px] font-semibold text-ink outline-none ${className}`}
    />
  );
}
