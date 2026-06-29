import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Card, Label, NotificationBell } from "../components/ui";

export default function Home() {
  const nav = useNavigate();
  const { user } = useAuth();
  const { data: programme } = useQuery({
    queryKey: ["programme"],
    queryFn: Api.currentProgramme,
    retry: false,
  });
  const { data: metrics } = useQuery({ queryKey: ["metrics"], queryFn: () => Api.metrics() });

  const latest = metrics?.[0];
  const todaySession = programme?.sessions?.[0];
  const greetName = user?.name ?? "there";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <div className="px-5 pt-2">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-serif text-2xl text-ink">
            {greeting}, {greetName}
          </div>
          {programme && (
            <div className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.12em] text-ink3">
              Week {programme.current_week} of {programme.total_weeks}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <NotificationBell />
          <button
            onClick={() => nav("/settings")}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-line bg-[#e9c9a0] font-serif text-lg text-[#8a5a2a]"
          >
            {greetName[0]?.toUpperCase()}
          </button>
        </div>
      </div>

      {/* Hero — today */}
      <div
        className="relative mt-4 overflow-hidden rounded-3xl p-5"
        style={{ background: "linear-gradient(160deg,var(--heroA),var(--heroB))", color: "var(--heroInk)" }}
      >
        <div className="font-mono text-[10px] uppercase tracking-[0.16em] opacity-70">
          {todaySession ? `Today · ${todaySession.session_type}` : "Today"}
        </div>
        <div className="mt-2 font-serif text-3xl leading-none">
          {todaySession ? (
            <>
              {todaySession.exercises.length} exercises
              <br />~50 minutes
            </>
          ) : (
            <>No session
              <br />planned</>
          )}
        </div>
        <div className="mt-4 flex items-center gap-2">
          <button
            onClick={() => nav("/workout")}
            className="h-11 rounded-xl bg-accent px-5 text-[15px] font-semibold text-white"
          >
            Start workout
          </button>
          <button
            onClick={() => nav("/programme")}
            className="h-11 rounded-xl border border-white/25 px-4 text-[13px] font-medium"
            style={{ color: "var(--heroInk)" }}
          >
            Preview
          </button>
        </div>
      </div>

      {/* Streak + check-in */}
      <div className="mt-3.5 flex gap-3">
        <Card className="flex-1">
          <Label>Streak</Label>
          <div className="mt-1.5 font-mono text-3xl font-semibold leading-none text-ink">—</div>
          <div className="mt-1 text-xs text-ink2">days on plan</div>
        </Card>
        <button onClick={() => nav("/checkins")} className="flex-1 text-left">
          <Card>
            <Label>Check-in</Label>
            <div className="mt-2 font-serif text-xl leading-none text-ink">Weekly</div>
            <div className="mt-1.5 text-xs text-ink2">with your coach</div>
          </Card>
        </button>
      </div>

      {/* Metric tiles */}
      <div className="mt-3.5 flex gap-3">
        <button onClick={() => nav("/progress")} className="flex-1 text-left">
          <Card>
            <Label>Weight</Label>
            <div className="mt-1 font-mono text-2xl font-semibold text-ink">
              {latest?.weight ?? "—"}
              <span className="text-xs text-ink2"> {user?.weight_unit}</span>
            </div>
          </Card>
        </button>
        <button onClick={() => nav("/progress")} className="flex-1 text-left">
          <Card>
            <Label>Waist</Label>
            <div className="mt-1 font-mono text-2xl font-semibold text-ink">
              {latest?.waist_cm ?? "—"}
              <span className="text-xs text-ink2"> {user?.measurement_unit}</span>
            </div>
          </Card>
        </button>
      </div>
    </div>
  );
}
