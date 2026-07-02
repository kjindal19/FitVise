import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Card, Label, NotificationBell } from "../components/ui";
import { CheckIcon, CoachIcon, FlameIcon } from "../components/Icon";
import { DAYS, currentWeekSessions, toISODate, todayDow, todaySession } from "../lib/programme";

export default function Home() {
  const nav = useNavigate();
  const { user } = useAuth();
  const { data: programme } = useQuery({
    queryKey: ["programme"],
    queryFn: Api.currentProgramme,
    retry: false,
  });
  const { data: metrics } = useQuery({ queryKey: ["metrics"], queryFn: () => Api.metrics() });
  const { data: profile } = useQuery({ queryKey: ["profile"], queryFn: Api.profile, retry: false });

  // Today's recovery log — used to prompt for sleep until it's been entered.
  const todayISO = toISODate();
  const { data: recovery } = useQuery({
    queryKey: ["recovery", todayISO],
    queryFn: () => Api.recovery(`?start_date=${todayISO}&end_date=${todayISO}`),
  });
  const sleepLogged = (recovery ?? []).some((r) => r.sleep_hours != null);

  // Pull a month of workout logs to derive the week strip + streak.
  const monthAgo = new Date(Date.now() - 31 * 86400_000).toISOString().slice(0, 10);
  const { data: workouts } = useQuery({
    queryKey: ["workouts", "recent"],
    queryFn: () => Api.workouts(`?start_date=${monthAgo}`),
  });

  const latest = metrics?.[0];
  const today = todaySession(programme);
  const greetName = user?.name ?? "there";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  // Body-metrics weight wins (most recent reading); fall back to the onboarding
  // profile so the tile isn't empty before the first snapshot is logged.
  const weightValue = latest?.weight ?? profile?.current_weight ?? null;
  const waistValue = latest?.waist_cm ?? profile?.target_waist ?? null;

  // ---- This week strip -------------------------------------------------
  const dow = todayDow();
  const monday = new Date();
  monday.setHours(0, 0, 0, 0);
  monday.setDate(monday.getDate() - dow);
  const sessions = currentWeekSessions(programme);
  const doneDates = new Set((workouts ?? []).map((w) => w.date));

  const week = DAYS.map((label, i) => {
    const date = new Date(monday);
    date.setDate(monday.getDate() + i);
    const iso = toISODate(date);
    const hasSession = sessions.some((s) => s.day_of_week === i);
    const isDone = doneDates.has(iso) && (hasSession || i <= dow);
    return { label, dow: i, isDone, isNow: i === dow, hasSession };
  });
  const plannedCount = sessions.filter((s) => s.day_of_week != null).length || sessions.length;
  const doneCount = week.filter((d) => d.isDone).length;
  const loggedToday = doneDates.has(todayISO);

  const streak = computeStreak(workouts);

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
          {today ? `Today · ${today.label ?? today.session_type}` : "Today"}
        </div>
        <div className="mt-2 font-serif text-3xl leading-none">
          {today ? (
            <>
              {today.exercises.length} exercises
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
            {loggedToday ? "Update workout" : "Start workout"}
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

      {/* Sleep prompt — hidden once today's sleep is logged */}
      {!sleepLogged && (
        <button
          onClick={() => nav("/journal")}
          className="mt-3.5 flex w-full items-center gap-3 rounded-2xl border border-line bg-surface p-4 text-left"
        >
          <span className="text-xl">🌙</span>
          <div className="flex-1">
            <div className="text-sm font-semibold text-ink">Log last night's sleep</div>
            <div className="mt-0.5 text-xs text-ink2">Add your sleep hours for today</div>
          </div>
          <span className="text-ink3">›</span>
        </button>
      )}

      {/* Streak + check-in */}
      <div className="mt-3.5 flex gap-3">
        <Card className="flex-1">
          <div className="flex items-center gap-1.5">
            <FlameIcon size={15} stroke="var(--accent)" />
            <Label>Streak</Label>
          </div>
          <div className="mt-1.5 font-mono text-3xl font-semibold leading-none text-ink">
            {streak || "—"}
          </div>
          <div className="mt-1 text-xs text-ink2">days on plan</div>
        </Card>
        <button onClick={() => nav("/checkins")} className="flex-1 text-left">
          <Card>
            <div className="flex items-center gap-1.5">
              <CoachIcon size={15} stroke="var(--blue)" />
              <Label>Check-in</Label>
            </div>
            <div className="mt-2 font-serif text-xl leading-none text-ink">Weekly</div>
            <div className="mt-1.5 text-xs text-ink2">with your coach</div>
          </Card>
        </button>
      </div>

      {/* This week */}
      {sessions.length > 0 && (
        <Card className="mt-3.5">
          <div className="mb-3 flex items-baseline justify-between">
            <Label>This week</Label>
            <button onClick={() => nav("/workout/history")} className="text-xs text-accent">
              History
            </button>
          </div>
          <div className="mb-3 -mt-2 text-xs text-ink2">
            <b className="text-ink">{doneCount}</b> of {plannedCount} sessions done
          </div>
          <div className="flex gap-1.5">
            {week.map((d) => (
              <div key={d.dow} className="flex flex-1 flex-col items-center gap-1.5">
                {d.isDone ? (
                  <div className="flex h-10 w-full items-center justify-center rounded-[10px] bg-green">
                    <CheckIcon size={15} stroke="#fff" />
                  </div>
                ) : d.isNow ? (
                  <div className="flex h-10 w-full items-center justify-center rounded-[10px] border-[1.5px] border-accent font-mono text-[11px] font-bold text-accent">
                    NOW
                  </div>
                ) : d.hasSession ? (
                  <div className="h-10 w-full rounded-[10px] border border-line" />
                ) : (
                  <div className="flex h-10 w-full items-center justify-center rounded-[10px] bg-surface2 text-[10px] text-ink3">
                    Rest
                  </div>
                )}
                <span className="font-mono text-[10px] text-ink3">{d.label}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Metric tiles */}
      <div className="mt-3.5 flex gap-3">
        <button onClick={() => nav("/progress")} className="flex-1 text-left">
          <Card>
            <Label>Weight</Label>
            <div className="mt-1 font-mono text-2xl font-semibold text-ink">
              {weightValue ?? "—"}
              <span className="text-xs text-ink2"> {user?.weight_unit}</span>
            </div>
          </Card>
        </button>
        <button onClick={() => nav("/progress")} className="flex-1 text-left">
          <Card>
            <Label>Waist</Label>
            <div className="mt-1 font-mono text-2xl font-semibold text-ink">
              {waistValue ?? "—"}
              <span className="text-xs text-ink2"> {user?.measurement_unit}</span>
            </div>
          </Card>
        </button>
      </div>
    </div>
  );
}

/** Consecutive-day run of workout logs ending today or yesterday. */
function computeStreak(workouts?: { date: string }[]): number {
  if (!workouts?.length) return 0;
  const days = new Set(workouts.map((w) => w.date));
  const cursor = new Date();
  cursor.setHours(0, 0, 0, 0);
  // Allow the streak to hold if today's session isn't logged yet.
  if (!days.has(toISODate(cursor))) {
    cursor.setDate(cursor.getDate() - 1);
  }
  let streak = 0;
  while (days.has(toISODate(cursor))) {
    streak++;
    cursor.setDate(cursor.getDate() - 1);
  }
  return streak;
}
