import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Api } from "../lib/api";
import { ScreenHeader } from "../components/ui";
import { CloseIcon } from "../components/Icon";

export default function NotificationsScreen() {
  const qc = useQueryClient();
  const nav = useNavigate();
  const { data: items } = useQuery({ queryKey: ["notifications"], queryFn: () => Api.notifications() });

  function refresh() {
    qc.invalidateQueries({ queryKey: ["notifications"] });
    qc.invalidateQueries({ queryKey: ["unread"] });
  }

  async function open(id: string, screen?: string) {
    await Api.markRead(id);
    refresh();
    if (screen) nav(`/${screen === "home" ? "" : screen}`);
  }
  async function markAll() {
    await Api.markAllRead();
    refresh();
  }
  async function dismiss(id: string) {
    await Api.deleteNotification(id);
    refresh();
  }
  async function clearRead() {
    await Api.clearRead();
    refresh();
  }

  const hasRead = (items ?? []).some((n) => n.read_at);

  return (
    <div className="px-5 pt-2">
      <ScreenHeader title="Notifications" back bell={false} />
      <div className="mt-2 flex items-center gap-4">
        <button onClick={markAll} className="text-[13px] font-semibold text-accent">
          Mark all read
        </button>
        {hasRead && (
          <button onClick={clearRead} className="text-[13px] font-semibold text-ink3">
            Clear read
          </button>
        )}
      </div>

      {!items?.length ? (
        <div className="mt-10 text-center text-sm text-ink2">You're all caught up. 🎉</div>
      ) : (
        <div className="mt-3 flex flex-col gap-2.5">
          {items.map((n) => (
            <div
              key={n.id}
              className="flex items-start gap-2 rounded-2xl border border-line p-4"
              style={{ background: n.read_at ? "var(--surface)" : "var(--accentSoft)" }}
            >
              <button
                onClick={() => open(n.id, n.data?.screen as string | undefined)}
                className="flex-1 text-left"
              >
                <div className="flex items-center gap-2">
                  {!n.read_at && <span className="h-2 w-2 shrink-0 rounded-full bg-accent" />}
                  <div className="text-[15px] font-semibold text-ink">{n.title}</div>
                </div>
                {n.body && <div className="mt-1 text-[13px] text-ink2">{n.body}</div>}
                <div className="mt-1.5 font-mono text-[10px] text-ink3">
                  {new Date(n.created_at).toLocaleString()}
                </div>
              </button>
              <button
                onClick={() => dismiss(n.id)}
                aria-label="Dismiss notification"
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-line bg-surface"
              >
                <CloseIcon size={14} stroke="var(--ink3)" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
