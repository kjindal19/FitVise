import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Api, type ExerciseItem } from "../lib/api";
import { ScreenHeader } from "../components/ui";
import { CoachIcon } from "../components/Icon";
import { DAYS, todayDow } from "../lib/programme";

export default function Programme() {
  const { data: programme, isError } = useQuery({
    queryKey: ["programme"],
    queryFn: Api.currentProgramme,
    retry: false,
  });

  const dow = todayDow();
  // Default the open accordion to today's session if there is one.
  const [open, setOpen] = useState<string | null>(null);

  return (
    <div className="px-5 pt-2">
      <ScreenHeader title="Programme" />
      {isError || !programme ? (
        <div className="mt-8 rounded-2xl border border-blueLine bg-blueBg p-4 text-sm text-blueInk">
          No programme yet. Connect your AI coach and run{" "}
          <span className="font-mono text-accent">/mcp__fitvise__onboard</span> to have one authored.
        </div>
      ) : (
        <>
          <div className="mt-1.5 font-mono text-[10px] uppercase tracking-[0.1em] text-ink3">
            Week {programme.current_week} of {programme.total_weeks} · {programme.goal_type ?? "—"}
          </div>
          <div className="mt-2.5 h-1.5 overflow-hidden rounded bg-surface2">
            <div
              className="h-full bg-accent"
              style={{ width: `${(programme.current_week / programme.total_weeks) * 100}%` }}
            />
          </div>

          <div className="mt-4 flex items-center gap-2.5 rounded-2xl border border-blueLine bg-blueBg p-3.5">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue">
              <CoachIcon size={13} stroke="#fff" />
            </span>
            <span className="text-[12.5px] text-blueInk">
              Authored by your coach. Tap a day to see its exercises.
            </span>
          </div>

          <div className="mt-4 flex flex-col gap-2.5">
            {programme.sessions.map((s) => {
              const isOpen = open === s.id;
              const isToday = s.day_of_week === dow && s.week_number === programme.current_week;
              return (
                <div
                  key={s.id}
                  className="overflow-hidden rounded-2xl border bg-surface"
                  style={{ borderColor: isToday ? "var(--accent)" : "var(--line)" }}
                >
                  <button
                    onClick={() => setOpen(isOpen ? null : s.id)}
                    className="flex w-full items-center gap-3 p-4 text-left"
                  >
                    <span
                      className="h-2.5 w-2.5 rounded-full border-2"
                      style={{ borderColor: isToday ? "var(--accent)" : "var(--ink3)" }}
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 text-[15px] font-semibold text-ink">
                        {s.day_of_week != null ? DAYS[s.day_of_week] : "—"} ·{" "}
                        {s.label ?? s.session_type}
                        {isToday && (
                          <span className="rounded-full bg-accentSoft px-1.5 py-0.5 font-mono text-[9px] font-bold uppercase tracking-wide text-accent">
                            Today
                          </span>
                        )}
                      </div>
                      <div className="mt-0.5 flex items-center gap-1.5 text-xs text-ink3">
                        <span>{s.exercises.length} exercises</span>
                        {s.warmup && s.warmup.length > 0 && (
                          <span className="rounded-full bg-surface2 px-1.5 py-0.5 text-[10px]">warm-up</span>
                        )}
                        {s.cooldown && s.cooldown.length > 0 && (
                          <span className="rounded-full bg-surface2 px-1.5 py-0.5 text-[10px]">cool-down</span>
                        )}
                      </div>
                    </div>
                    <span
                      className="text-ink3 transition-transform"
                      style={{ transform: isOpen ? "rotate(90deg)" : "none" }}
                    >
                      ›
                    </span>
                  </button>

                  {isOpen && (
                    <div className="border-t border-line px-4 pb-3 pt-1">
                      {s.exercises.length === 0 ? (
                        <div className="py-3 text-xs text-ink3">Rest / recovery day — no exercises.</div>
                      ) : (
                        s.exercises.map((e) => <ExerciseRow key={e.id} ex={e} />)
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

function repsLabel(e: ExerciseItem): string {
  if (e.reps_raw) return e.reps_raw;
  if (e.reps_min && e.reps_max && e.reps_min !== e.reps_max) return `${e.reps_min}-${e.reps_max}`;
  if (e.reps_min) return `${e.reps_min}`;
  return "—";
}

function ExerciseRow({ ex }: { ex: ExerciseItem }) {
  return (
    <div className="border-b border-line py-2.5 last:border-b-0">
      <div className="flex items-center justify-between">
        <span className="text-[14px] font-medium text-ink">{ex.name}</span>
        <span className="font-mono text-xs text-ink2">
          {ex.sets ?? 3} × {repsLabel(ex)}
        </span>
      </div>
      <div className="mt-0.5 flex flex-wrap gap-x-3 gap-y-0.5 font-mono text-[10px] text-ink3">
        {ex.rest_seconds != null && <span>rest {ex.rest_seconds}s</span>}
        {ex.form_notes && <span className="text-ink2">{ex.form_notes}</span>}
      </div>
    </div>
  );
}
