import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Api } from "../lib/api";
import { ScreenHeader } from "../components/ui";

export default function NotificationsScreen() {
  const qc = useQueryClient();
  const nav = useNavigate();
  const { data: items } = useQuery({ queryKey: ["notifications"], queryFn: () => Api.notifications() });

  async function open(id: string, screen?: string) {
    await Api.markRead(id);
    qc.invalidateQueries({ queryKey: ["notifications"] });
    qc.invalidateQueries({ queryKey: ["unread"] });
    if (screen) nav(`/${screen === "home" ? "" : screen}`);
  }
  async function markAll() {
    await Api.markAllRead();
    qc.invalidateQueries({ queryKey: ["notifications"] });
    qc.invalidateQueries({ queryKey: ["unread"] });
  }

  return (
    <div className="px-5 pt-2">
      <ScreenHeader title="Notifications" back bell={false} />
      <button onClick={markAll} className="mt-2 text-[13px] font-semibold text-accent">
        Mark all read
      </button>

      {!items?.length ? (
        <div className="mt-10 text-center text-sm text-ink2">You're all caught up. 🎉</div>
      ) : (
        <div className="mt-3 flex flex-col gap-2.5">
          {items.map((n) => (
            <button
              key={n.id}
              onClick={() => open(n.id, n.data?.screen as string | undefined)}
              className="rounded-2xl border border-line p-4 text-left"
              style={{ background: n.read_at ? "var(--surface)" : "var(--accentSoft)" }}
            >
              <div className="flex items-center justify-between">
                <div className="text-[15px] font-semibold text-ink">{n.title}</div>
                {!n.read_at && <span className="h-2 w-2 rounded-full bg-accent" />}
              </div>
              {n.body && <div className="mt-1 text-[13px] text-ink2">{n.body}</div>}
              <div className="mt-1.5 font-mono text-[10px] text-ink3">
                {new Date(n.created_at).toLocaleString()}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
