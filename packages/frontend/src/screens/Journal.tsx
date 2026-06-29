import { useState } from "react";
import { mutate } from "../lib/offline";
import { ScreenHeader } from "../components/ui";

type Tab = "energy" | "flags" | "injury";
const FLAGS = [
  "late_night_eating",
  "sugar_craving",
  "skipped_session",
  "stress_eating",
  "overate_at_meal",
  "good_choice_moment",
];

export default function Journal() {
  const [tab, setTab] = useState<Tab>("energy");
  const today = new Date().toISOString().slice(0, 10);
  const [energy, setEnergy] = useState(3);
  const [sleep, setSleep] = useState("7.5");

  async function saveEnergy() {
    await mutate("/api/v1/recovery", "POST", {
      date: today,
      energy_level: energy,
      sleep_hours: Number(sleep),
    });
    alert("Recovery logged ✓");
  }
  async function tagFlag(flag: string) {
    await mutate("/api/v1/journal/flags", "POST", { date: today, flag_type: flag });
    alert(`Tagged: ${flag.replace(/_/g, " ")}`);
  }

  return (
    <div className="px-5 pt-2">
      <ScreenHeader title="Journal" />
      <div className="sa mt-3 flex gap-1.5 overflow-x-auto">
        {(["energy", "flags", "injury"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="whitespace-nowrap rounded-full border px-3 py-2 text-[13px] font-semibold capitalize"
            style={{
              borderColor: tab === t ? "var(--accent)" : "var(--line)",
              background: tab === t ? "var(--accent)" : "var(--surface)",
              color: tab === t ? "#fff" : "var(--ink2)",
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "energy" && (
        <div className="mt-3.5 rounded-2xl border border-line bg-surface p-4">
          <div className="text-sm font-semibold text-ink">How's your energy today?</div>
          <div className="mt-3.5 flex gap-2">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                onClick={() => setEnergy(n)}
                className="flex aspect-square flex-1 items-center justify-center rounded-xl border-2 text-lg"
                style={{
                  borderColor: energy === n ? "var(--accent)" : "var(--line)",
                  background: energy === n ? "var(--accentSoft)" : "var(--surface2)",
                }}
              >
                {["😣", "😕", "😐", "🙂", "😄"][n - 1]}
              </button>
            ))}
          </div>
          <div className="mt-3.5">
            <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-ink3">Sleep (hrs)</div>
            <input
              value={sleep}
              onChange={(e) => setSleep(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-line bg-surface2 p-2.5 font-mono text-base text-ink outline-none"
            />
          </div>
          <button onClick={saveEnergy} className="mt-3.5 h-11 w-full rounded-xl bg-accent font-semibold text-white">
            Save
          </button>
        </div>
      )}

      {tab === "flags" && (
        <div className="mt-3.5 rounded-2xl border border-line bg-surface p-4">
          <div className="text-sm font-semibold text-ink">Tag a moment — no judgment</div>
          <div className="mt-3.5 flex flex-wrap gap-2">
            {FLAGS.map((f) => (
              <button
                key={f}
                onClick={() => tagFlag(f)}
                className="rounded-full border border-line bg-surface2 px-3 py-2 text-xs text-ink2"
              >
                {f.replace(/_/g, " ")}
              </button>
            ))}
          </div>
          <div className="mt-3.5 text-xs leading-relaxed text-ink3">
            These are never shown back to you as counts. Your coach surfaces patterns gently during
            check-ins.
          </div>
        </div>
      )}

      {tab === "injury" && (
        <div className="mt-3.5 rounded-2xl border border-blueLine bg-blueBg p-3.5 text-[13px] leading-relaxed text-blueInk">
          Log discomfort here and your coach will see it via MCP before progressing any lift that
          loads the area. (Full injury form — flesh out next.)
        </div>
      )}
    </div>
  );
}
