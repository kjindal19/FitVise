import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Api, API_BASE } from "../lib/api";
import { ScreenHeader } from "../components/ui";

const STARTER =
  "I'd like to start onboarding with FitVise. Please read my profile and walk me through setup.";

export default function Connect() {
  const nav = useNavigate();
  const [copied, setCopied] = useState(false);
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: Api.health });
  const mcpUrl = `${API_BASE}/mcp`;
  const multiUser = health?.auth_mode !== "single_user";

  function copy(text: string) {
    navigator.clipboard?.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="px-5 pb-10 pt-2">
      <ScreenHeader title="Connect your AI coach" back bell={false} />
      <p className="mt-2 text-sm leading-relaxed text-ink2">
        FitVise is your journal. The coaching happens in your AI client — let's link them.
      </p>

      <Step n={1} title="Add FitVise to your AI client">
        <p className="text-[13px] leading-relaxed text-ink2">
          In Claude (or any MCP client), add a custom connector pointing at:
        </p>
        <div className="mt-2 break-all rounded-xl border border-line bg-accentSoft px-3 py-2.5 font-mono text-[13px] text-accent">
          {mcpUrl}
        </div>
        {multiUser ? (
          <p className="mt-2 text-xs text-ink3">
            You'll be asked to authorize via OAuth — no keys to copy.
          </p>
        ) : (
          <p className="mt-2 text-xs text-ink3">
            Single-user mode: use the stdio config + static key from your server setup.
          </p>
        )}
      </Step>

      <Step n={2} title="Start onboarding">
        <p className="text-[13px] text-ink2">In your AI client, run the slash command:</p>
        <div className="mt-2 rounded-xl border border-line bg-accentSoft px-3 py-2.5 font-mono text-[13px] text-accent">
          /mcp__fitvise__onboard
        </div>
        <p className="mt-3 text-xs text-ink3">No slash commands in your client? Copy this starter:</p>
        <button
          onClick={() => copy(STARTER)}
          className="mt-2 w-full rounded-xl border border-dashed border-line bg-surface2 p-3 text-left font-mono text-[13px] text-ink"
        >
          “{STARTER}”
          <div className="mt-2 text-xs font-semibold text-accent">
            {copied ? "Copied!" : "Copy starter prompt"}
          </div>
        </button>
      </Step>

      <button
        onClick={() => nav("/")}
        className="mt-4 h-12 w-full rounded-2xl border border-line bg-surface font-semibold text-ink"
      >
        Skip to app →
      </button>
    </div>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <div className="mt-4 rounded-2xl border border-line bg-surface p-4">
      <div className="flex items-center gap-2.5">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent font-mono text-xs font-semibold text-white">
          {n}
        </span>
        <span className="text-[15px] font-semibold text-ink">{title}</span>
      </div>
      <div className="mt-2.5">{children}</div>
    </div>
  );
}
