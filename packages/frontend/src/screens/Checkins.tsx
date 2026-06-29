import { useQuery } from "@tanstack/react-query";
import { Api } from "../lib/api";
import { ScreenHeader } from "../components/ui";
import { CoachIcon } from "../components/Icon";

export default function Checkins() {
  const { data: checkins } = useQuery({ queryKey: ["checkins"], queryFn: Api.checkins });

  return (
    <div className="px-5 pt-2">
      <ScreenHeader title="Check-ins" back />
      {!checkins?.length ? (
        <div className="mt-8 rounded-2xl border border-blueLine bg-blueBg p-4 text-sm text-blueInk">
          No check-ins yet. Run <span className="font-mono text-accent">/mcp__fitvise__weekly_checkin</span>{" "}
          with your coach to get your first summary.
        </div>
      ) : (
        <div className="mt-4 flex flex-col gap-3">
          {checkins.map((c) => (
            <div key={c.id} className="overflow-hidden rounded-2xl border border-blueLine bg-blueBg">
              <div className="flex items-center gap-2 bg-blue px-4 py-2">
                <CoachIcon size={13} stroke="#fff" />
                <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-white">
                  Coaching report · {c.date}
                </span>
              </div>
              <div className="p-4">
                <div className="flex gap-5 font-mono">
                  <Stat label="Weight" value={c.weight_at_checkin} />
                  <Stat label="Waist" value={c.waist_at_checkin} />
                </div>
                {c.ai_summary && (
                  <div className="mt-3 font-serif text-[15px] italic leading-relaxed text-blueInk">
                    “{c.ai_summary}”
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | null }) {
  return (
    <div>
      <div className="font-mono text-[9px] uppercase tracking-[0.1em] text-ink3">{label}</div>
      <div className="font-mono text-lg font-semibold text-ink">{value ?? "—"}</div>
    </div>
  );
}
