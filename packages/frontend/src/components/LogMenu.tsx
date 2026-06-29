import { useNavigate } from "react-router-dom";

const ITEMS = [
  { label: "Workout", to: "/workout", emoji: "🏋️" },
  { label: "Diet", to: "/diet", emoji: "🥗" },
  { label: "Body metrics", to: "/metrics", emoji: "⚖️" },
  { label: "Energy & recovery", to: "/journal", emoji: "🔋" },
];

export default function LogMenu({ onClose }: { onClose: () => void }) {
  const nav = useNavigate();
  return (
    <>
      <div className="anim-fade absolute inset-0 z-30 bg-black/45" onClick={onClose} />
      <div className="anim-sheet absolute inset-x-0 bottom-0 z-40 rounded-t-3xl bg-surface px-5 pb-7 pt-2">
        <div className="mx-auto my-3 h-1 w-10 rounded bg-line" />
        <div className="mb-3 font-serif text-xl text-ink">What are you logging?</div>
        <div className="flex flex-col gap-2.5">
          {ITEMS.map((it) => (
            <button
              key={it.to}
              onClick={() => {
                onClose();
                nav(it.to);
              }}
              className="flex items-center gap-3.5 rounded-2xl border border-line bg-surface2 p-4 text-left"
            >
              <span className="text-2xl">{it.emoji}</span>
              <span className="text-[15px] font-semibold text-ink">{it.label}</span>
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
