import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { mutate } from "../lib/offline";
import { ScreenHeader, Label, PrimaryButton } from "../components/ui";

// Optional circumference / composition measures, hidden behind "More measures"
// so the common weight + waist snapshot stays quick.
const MORE_FIELDS: { key: string; label: string }[] = [
  { key: "chest_cm", label: "Chest" },
  { key: "hip_cm", label: "Hip" },
  { key: "left_arm_cm", label: "Left arm" },
  { key: "right_thigh_cm", label: "Right thigh" },
  { key: "body_fat_pct", label: "Body fat %" },
];

export default function Metrics() {
  const nav = useNavigate();
  const [weight, setWeight] = useState("");
  const [waist, setWaist] = useState("");
  const [notes, setNotes] = useState("");
  const [more, setMore] = useState<Record<string, string>>({});
  const [showMore, setShowMore] = useState(false);
  const [saved, setSaved] = useState(false);

  async function save() {
    const extra: Record<string, number> = {};
    for (const { key } of MORE_FIELDS) {
      if (more[key]) extra[key] = Number(more[key]);
    }
    await mutate("/api/v1/metrics", "POST", {
      logged_at: new Date().toISOString(),
      weight: weight ? Number(weight) : null,
      waist_cm: waist ? Number(waist) : null,
      notes: notes || null,
      ...extra,
    });
    setSaved(true);
    setTimeout(() => nav("/"), 900);
  }

  return (
    <div className="px-5 pt-2">
      <ScreenHeader title="Body metrics" subtitle="Weekly snapshot" back />
      {saved && (
        <div className="mt-3.5 rounded-2xl border border-green bg-greenSoft p-3.5 text-sm text-ink">
          Saved ✓
        </div>
      )}
      <div className="mt-3.5 flex gap-3">
        <div className="flex-1 rounded-2xl border border-line bg-surface p-4">
          <Label>Weight</Label>
          <input
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            inputMode="decimal"
            placeholder="—"
            className="mt-2 w-full bg-transparent font-mono text-2xl font-semibold text-ink outline-none"
          />
        </div>
        <div className="flex-1 rounded-2xl border border-line bg-surface p-4">
          <Label>Waist</Label>
          <input
            value={waist}
            onChange={(e) => setWaist(e.target.value)}
            inputMode="decimal"
            placeholder="—"
            className="mt-2 w-full bg-transparent font-mono text-2xl font-semibold text-ink outline-none"
          />
        </div>
      </div>

      <button
        onClick={() => setShowMore((v) => !v)}
        className="mt-3 flex w-full items-center justify-between rounded-2xl border border-line bg-surface px-4 py-3 text-sm font-medium text-ink"
      >
        <span>More measures</span>
        <span className="text-ink3">{showMore ? "−" : "+"}</span>
      </button>
      {showMore && (
        <div className="mt-3 grid grid-cols-2 gap-3">
          {MORE_FIELDS.map(({ key, label }) => (
            <div key={key} className="rounded-2xl border border-line bg-surface p-4">
              <Label>{label}</Label>
              <input
                value={more[key] ?? ""}
                onChange={(e) => setMore((m) => ({ ...m, [key]: e.target.value }))}
                inputMode="decimal"
                placeholder="—"
                className="mt-2 w-full bg-transparent font-mono text-xl font-semibold text-ink outline-none"
              />
            </div>
          ))}
        </div>
      )}

      <div className="mt-3 rounded-2xl border border-line bg-surface p-4">
        <Label>Notes</Label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Felt bloated, travel week…"
          className="mt-2 h-16 w-full resize-none bg-transparent text-sm text-ink outline-none"
        />
      </div>
      <div className="mt-3.5">
        <PrimaryButton onClick={save}>Save snapshot</PrimaryButton>
      </div>
    </div>
  );
}
