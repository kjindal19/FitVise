import { useQuery } from "@tanstack/react-query";
import { Api } from "../lib/api";
import { ScreenHeader } from "../components/ui";
import { CoachIcon } from "../components/Icon";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function Programme() {
  const { data: programme, isError } = useQuery({
    queryKey: ["programme"],
    queryFn: Api.currentProgramme,
    retry: false,
  });

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
              Authored by your coach. Ask to adjust in your AI client.
            </span>
          </div>

          <div className="mt-4 flex flex-col gap-2.5">
            {programme.sessions.map((s) => (
              <div
                key={s.id}
                className="flex items-center gap-3 rounded-2xl border border-line bg-surface p-4"
              >
                <span className="h-2.5 w-2.5 rounded-full border-2 border-ink3" />
                <div className="flex-1">
                  <div className="text-[15px] font-semibold text-ink">
                    {s.day_of_week != null ? DAYS[s.day_of_week] : "—"} ·{" "}
                    {s.label ?? s.session_type}
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-ink3">
                    <span>{s.exercises.length} exercises</span>
                    {s.warmup && s.warmup.length > 0 && (
                      <span className="rounded-full bg-surface2 px-1.5 py-0.5 text-[10px]">warm-up</span>
                    )}
                    {s.cooldown && s.cooldown.length > 0 && (
                      <span className="rounded-full bg-surface2 px-1.5 py-0.5 text-[10px]">cool-down</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
