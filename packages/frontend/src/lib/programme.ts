// Shared helpers for reading a Programme the way the UI needs it.
// The backend stores day_of_week as 0=Mon … 6=Sun; JS Date.getDay() is
// 0=Sun … 6=Sat, so we convert between the two here in one place.

import type { Programme, ProgrammeSession } from "./api";

export const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

/**
 * YYYY-MM-DD from a Date's LOCAL calendar components. Use this for anything that
 * represents a day the user experiences — never `toISOString().slice(0,10)`, which
 * converts to UTC and shifts the date across midnight in non-UTC timezones.
 */
export function toISODate(d: Date = new Date()): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** Today's weekday in the backend's scheme (0=Mon … 6=Sun). */
export function todayDow(now = new Date()): number {
  return (now.getDay() + 6) % 7;
}

/** Sessions belonging to the programme's current week (falls back to all). */
export function currentWeekSessions(programme?: Programme | null): ProgrammeSession[] {
  if (!programme) return [];
  const wk = programme.sessions.filter((s) => s.week_number === programme.current_week);
  return wk.length ? wk : programme.sessions;
}

/**
 * The session to treat as "today". Prefers an exact day-of-week match within
 * the current week; otherwise the next upcoming session this week; otherwise
 * the first session — so the app never silently shows the wrong day.
 */
export function todaySession(
  programme?: Programme | null,
  now = new Date()
): ProgrammeSession | undefined {
  const sessions = currentWeekSessions(programme);
  if (!sessions.length) return undefined;
  const dow = todayDow(now);

  const exact = sessions.find((s) => s.day_of_week === dow);
  if (exact) return exact;

  // Next session later this week, if days are assigned.
  const upcoming = sessions
    .filter((s) => s.day_of_week != null && (s.day_of_week as number) >= dow)
    .sort((a, b) => (a.day_of_week as number) - (b.day_of_week as number))[0];
  if (upcoming) return upcoming;

  return sessions[0];
}
