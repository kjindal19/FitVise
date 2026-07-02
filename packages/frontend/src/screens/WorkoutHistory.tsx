import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Api } from "../lib/api";
import { ScreenHeader } from "../components/ui";
import { toISODate } from "../lib/programme";

export default function WorkoutHistory() {
  const nav = useNavigate();

  // A year of logged sessions — plenty to browse and edit.
  const since = toISODate(new Date(Date.now() - 365 * 86400_000));
  const { data: logs } = useQuery({
    queryKey: ["workouts", "history", since],
    queryFn: () => Api.workouts(`?start_date=${since}`),
  });

  const today = toISODate();

  return (
    <div className="px-5 pt-2">
      <ScreenHeader title="Workout history" subtitle="Tap to view or update" back />

      {logs && logs.length === 0 && (
        <div className="mt-10 text-center text-sm text-ink2">
          No workouts logged yet. Finish a session and it'll show up here.
        </div>
      )}

      <div className="mt-4 flex flex-col gap-2.5">
        {(logs ?? []).map((w) => {
          const exercises = new Set(w.sets.map((s) => s.exercise_name));
          const d = new Date(`${w.date}T00:00:00`);
          return (
            <button
              key={w.id}
              onClick={() => nav(`/workout?date=${w.date}`)}
              className="flex items-center gap-3 rounded-2xl border border-line bg-surface p-4 text-left"
            >
              <div className="flex-1">
                <div className="text-base font-semibold text-ink">
                  {d.toLocaleDateString(undefined, {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                  })}
                  {w.date === today && <span className="ml-2 text-xs text-accent">Today</span>}
                </div>
                <div className="mt-0.5 font-mono text-xs text-ink3">
                  {exercises.size} {exercises.size === 1 ? "exercise" : "exercises"} ·{" "}
                  {w.sets.length} {w.sets.length === 1 ? "set" : "sets"}
                </div>
              </div>
              <span className="font-mono text-xs text-ink2">Edit ›</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
