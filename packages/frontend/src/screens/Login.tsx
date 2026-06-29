import { useState } from "react";
import { useAuth } from "../lib/auth";

export default function Login() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      if (mode === "login") await login(email, password);
      else await register(name, email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    }
  }

  return (
    <div className="mx-auto flex h-full max-w-[440px] flex-col justify-center px-6">
      <div className="font-serif text-3xl text-ink">FitVise</div>
      <p className="mt-1 text-sm text-ink2">
        {mode === "login" ? "Sign in to your journal." : "Create your account."}
      </p>
      <form onSubmit={submit} className="mt-6 flex flex-col gap-3">
        {mode === "register" && (
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name"
            className="rounded-xl border border-line bg-surface p-3 text-ink outline-none"
            required
          />
        )}
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          type="email"
          placeholder="Email"
          className="rounded-xl border border-line bg-surface p-3 text-ink outline-none"
          required
        />
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          type="password"
          placeholder="Password"
          className="rounded-xl border border-line bg-surface p-3 text-ink outline-none"
          required
        />
        {error && <div className="text-sm text-accent">{error}</div>}
        <button type="submit" className="h-12 rounded-2xl bg-accent font-semibold text-white">
          {mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>
      <button
        onClick={() => setMode(mode === "login" ? "register" : "login")}
        className="mt-4 text-sm text-ink2 underline"
      >
        {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
      </button>
    </div>
  );
}
