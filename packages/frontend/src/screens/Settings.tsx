import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Api, API_BASE, getToken } from "../lib/api";
import { useTheme } from "../lib/theme";
import { useAuth } from "../lib/auth";
import { enablePush } from "../lib/push";
import { ScreenHeader, Label } from "../components/ui";

export default function Settings() {
  const nav = useNavigate();
  const { theme, toggle } = useTheme();
  const { user } = useAuth();
  const qc = useQueryClient();
  const [pushMsg, setPushMsg] = useState<string>("");

  const { data: prefs } = useQuery({
    queryKey: ["notif-prefs"],
    queryFn: Api.notificationPrefs,
  });
  const { data: profile } = useQuery({ queryKey: ["profile"], queryFn: Api.profile, retry: false });

  async function setPref(key: string, value: boolean | string) {
    await Api.updateNotificationPrefs({ [key]: value } as never);
    qc.invalidateQueries({ queryKey: ["notif-prefs"] });
  }

  async function onEnablePush() {
    setPushMsg("Requesting permission…");
    const r = await enablePush();
    setPushMsg(r.ok ? "Web Push enabled ✓" : `Couldn't enable: ${r.reason}`);
  }

  function download(path: string) {
    // include the bearer token via query is not supported; open in same tab works
    // for single_user; for multi_user the browser sends the SPA token only via fetch.
    const token = getToken();
    if (token) {
      fetch(`${API_BASE}${path}`, { headers: { Authorization: `Bearer ${token}` } })
        .then((r) => r.blob())
        .then((b) => {
          const url = URL.createObjectURL(b);
          const a = document.createElement("a");
          a.href = url;
          a.download = path.endsWith("csv") ? "fitvise-export-csv.zip" : "fitvise-export.json";
          a.click();
        });
    } else {
      window.open(`${API_BASE}${path}`, "_blank");
    }
  }

  return (
    <div className="px-5 pt-2">
      <ScreenHeader title="Settings" back />

      <div className="mt-4 flex items-center gap-3.5 rounded-2xl border border-line bg-surface p-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#e9c9a0] font-serif text-xl text-[#8a5a2a]">
          {user?.name?.[0]?.toUpperCase() ?? "?"}
        </div>
        <div className="flex-1">
          <div className="text-base font-semibold text-ink">{user?.name}</div>
          <div className="text-xs text-ink3">{user?.email ?? "self-hosted"}</div>
        </div>
      </div>

      {/* Your details — surfaced from onboarding / the AI coach */}
      <div className="mt-3.5 rounded-2xl border border-line bg-surface p-4">
        <Label>Your details</Label>
        <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3">
          <Detail label="Age" value={user?.age != null ? `${user.age}` : null} />
          <Detail label="Gender" value={user?.gender} />
          <Detail
            label="Height"
            value={profile?.height != null ? `${profile.height} ${user?.measurement_unit}` : null}
          />
          <Detail
            label="Weight"
            value={
              profile?.current_weight != null
                ? `${profile.current_weight} ${user?.weight_unit}`
                : null
            }
          />
          <Detail
            label="Target weight"
            value={
              profile?.target_weight != null
                ? `${profile.target_weight} ${user?.weight_unit}`
                : null
            }
          />
          <Detail label="Goal" value={pretty(profile?.goal_type)} />
          <Detail label="Diet" value={pretty(profile?.diet_type)} />
          <Detail label="Training" value={pretty(profile?.training_modality)} />
          <Detail
            label="Days / week"
            value={profile?.training_days_per_week != null ? `${profile.training_days_per_week}` : null}
          />
        </div>
        {profile?.equipment_available && profile.equipment_available.length > 0 && (
          <div className="mt-3.5">
            <Label>Equipment available</Label>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {profile.equipment_available.map((eq) => (
                <span
                  key={eq}
                  className="rounded-full border border-line bg-surface2 px-2.5 py-1 text-[11px] text-ink2"
                >
                  {pretty(eq)}
                </span>
              ))}
            </div>
          </div>
        )}
        <p className="mt-3 text-xs leading-relaxed text-ink3">
          Edit these by chatting with your AI coach — it keeps your profile in sync.
        </p>
      </div>

      {/* Appearance */}
      <div className="mt-3.5 overflow-hidden rounded-2xl border border-line bg-surface">
        <Row label="Appearance">
          <button onClick={toggle} className="rounded-lg border border-line bg-surface2 px-3 py-1.5 text-xs font-semibold text-ink">
            {theme === "dark" ? "Dark" : "Light"}
          </button>
        </Row>
        <Row label="Weight units">
          <span className="text-xs text-ink2">{user?.weight_unit}</span>
        </Row>
        <Row label="Length units" last>
          <span className="text-xs text-ink2">{user?.measurement_unit}</span>
        </Row>
      </div>

      {/* Notifications */}
      <div className="mt-3.5 rounded-2xl border border-line bg-surface p-4">
        <Label>Notifications</Label>
        <div className="mt-3 flex flex-col gap-3">
          <Toggle
            label="In-app notifications"
            checked={prefs?.inapp_enabled ?? true}
            onChange={(v) => setPref("inapp_enabled", v)}
          />
          <Toggle
            label="Web push (browser)"
            checked={prefs?.webpush_enabled ?? true}
            onChange={(v) => setPref("webpush_enabled", v)}
          />
          <Toggle
            label="Daily reminder"
            checked={prefs?.daily_reminder_enabled ?? true}
            onChange={(v) => setPref("daily_reminder_enabled", v)}
          />
          <Toggle
            label="Missed-workout nudge"
            checked={prefs?.missed_workout_enabled ?? true}
            onChange={(v) => setPref("missed_workout_enabled", v)}
          />
          <div className="flex items-center justify-between">
            <span className="text-sm text-ink">Reminder time</span>
            <input
              type="time"
              value={prefs?.daily_reminder_time ?? "18:00"}
              onChange={(e) => setPref("daily_reminder_time", e.target.value)}
              className="rounded-lg border border-line bg-surface2 px-2 py-1 text-xs text-ink"
            />
          </div>
        </div>
        <div className="mt-3 flex gap-2">
          <button onClick={onEnablePush} className="flex-1 rounded-xl border border-line bg-surface2 py-2.5 text-[13px] font-semibold text-ink">
            Enable push on this device
          </button>
          <button
            onClick={() => Api.testNotification().then(() => setPushMsg("Test sent ✓"))}
            className="rounded-xl border border-line bg-surface2 px-3 py-2.5 text-[13px] font-semibold text-ink"
          >
            Test
          </button>
        </div>
        {pushMsg && <div className="mt-2 text-xs text-ink2">{pushMsg}</div>}
      </div>

      {/* MCP connection */}
      <div className="mt-3.5 rounded-2xl border border-line bg-surface p-4">
        <Label>AI / MCP connection</Label>
        <p className="mt-2.5 text-[13px] leading-relaxed text-ink2">
          Your AI client reads and writes your log through the FitVise MCP server.
        </p>
        <button
          onClick={() => nav("/connect")}
          className="mt-3 h-11 w-full rounded-xl border border-line bg-surface2 text-sm font-semibold text-ink"
        >
          Connection details
        </button>
      </div>

      {/* Export */}
      <div className="mt-3.5 flex gap-3 pb-4">
        <button onClick={() => download("/api/v1/export/json")} className="flex-1 h-11 rounded-xl border border-line bg-surface text-[13px] font-semibold text-ink">
          Export JSON
        </button>
        <button onClick={() => download("/api/v1/export/csv")} className="flex-1 h-11 rounded-xl border border-line bg-surface text-[13px] font-semibold text-ink">
          Export CSV
        </button>
      </div>
    </div>
  );
}

function pretty(value?: string | null): string | null {
  if (!value) return null;
  return value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function Detail({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-ink3">{label}</div>
      <div className="mt-0.5 text-sm text-ink">{value ?? "—"}</div>
    </div>
  );
}

function Row({ label, children, last }: { label: string; children: React.ReactNode; last?: boolean }) {
  return (
    <div className={`flex items-center justify-between p-4 ${last ? "" : "border-b border-line"}`}>
      <span className="text-sm text-ink">{label}</span>
      {children}
    </div>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-ink">{label}</span>
      <button
        onClick={() => onChange(!checked)}
        className="relative h-6 w-11 rounded-full transition-colors"
        style={{ background: checked ? "var(--accent)" : "var(--surface2)" }}
      >
        <span
          className="absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all"
          style={{ left: checked ? 22 : 2 }}
        />
      </button>
    </div>
  );
}
