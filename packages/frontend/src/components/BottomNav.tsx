import { useLocation, useNavigate } from "react-router-dom";
import { HomeIcon, ProgrammeIcon, ProgressIcon, JournalIcon, PlusIcon } from "./Icon";

const NAV = [
  { to: "/", Icon: HomeIcon, key: "home" },
  { to: "/programme", Icon: ProgrammeIcon, key: "programme" },
  { to: "/progress", Icon: ProgressIcon, key: "progress" },
  { to: "/journal", Icon: JournalIcon, key: "journal" },
];

export default function BottomNav({ onLog }: { onLog: () => void }) {
  const nav = useNavigate();
  const { pathname } = useLocation();
  const active = (to: string) => (to === "/" ? pathname === "/" : pathname.startsWith(to));

  return (
    <nav className="absolute inset-x-0 bottom-0 z-20 flex h-16 items-center justify-around border-t border-line bg-[var(--navBg)] pb-1">
      {NAV.slice(0, 2).map(({ to, Icon, key }) => (
        <button key={key} className="p-2" onClick={() => nav(to)}>
          <Icon stroke={active(to) ? "var(--ink)" : "var(--ink3)"} />
        </button>
      ))}
      <button onClick={onLog} className="-mt-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent shadow-lg">
          <PlusIcon stroke="#fff" size={23} />
        </div>
      </button>
      {NAV.slice(2).map(({ to, Icon, key }) => (
        <button key={key} className="p-2" onClick={() => nav(to)}>
          <Icon stroke={active(to) ? "var(--ink)" : "var(--ink3)"} />
        </button>
      ))}
    </nav>
  );
}
