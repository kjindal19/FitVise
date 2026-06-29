import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { Api } from "../lib/api";
import { BackIcon, BellIcon } from "./Icon";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-line bg-surface p-4 ${className}`}>{children}</div>
  );
}

export function Label({ children }: { children: ReactNode }) {
  return (
    <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-ink3">{children}</div>
  );
}

export function NotificationBell() {
  const nav = useNavigate();
  const { data } = useQuery({
    queryKey: ["unread"],
    queryFn: Api.unreadCount,
    refetchInterval: 30_000,
  });
  const unread = data?.unread ?? 0;
  return (
    <button
      onClick={() => nav("/notifications")}
      className="relative flex h-10 w-10 items-center justify-center rounded-full border border-line bg-surface"
      aria-label="Notifications"
    >
      <BellIcon size={19} stroke="var(--ink)" />
      {unread > 0 && (
        <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[10px] font-bold text-white">
          {unread > 9 ? "9+" : unread}
        </span>
      )}
    </button>
  );
}

export function ScreenHeader({
  title,
  subtitle,
  back,
  bell = true,
}: {
  title: string;
  subtitle?: string;
  back?: boolean;
  bell?: boolean;
}) {
  const nav = useNavigate();
  return (
    <div className="flex items-center gap-3">
      {back && (
        <button
          onClick={() => nav(-1)}
          className="flex h-9 w-9 items-center justify-center rounded-full border border-line bg-surface"
        >
          <BackIcon size={17} stroke="var(--ink)" />
        </button>
      )}
      <div className="flex-1">
        <div className="font-serif text-2xl text-ink">{title}</div>
        {subtitle && (
          <div className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.12em] text-ink3">
            {subtitle}
          </div>
        )}
      </div>
      {bell && <NotificationBell />}
    </div>
  );
}

export function PrimaryButton({
  children,
  onClick,
  className = "",
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  type?: "button" | "submit";
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      className={`h-12 w-full rounded-2xl bg-accent text-base font-semibold text-white ${className}`}
    >
      {children}
    </button>
  );
}
