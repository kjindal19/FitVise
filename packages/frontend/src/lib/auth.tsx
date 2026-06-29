import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { Api, setToken, type HealthResponse, type User } from "./api";

interface AuthCtx {
  user: User | null;
  health: HealthResponse | null;
  loading: boolean;
  isMultiUser: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const Ctx = createContext<AuthCtx>(null as unknown as AuthCtx);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const isMultiUser = health?.auth_mode !== "single_user";

  async function loadUser() {
    try {
      setUser(await Api.me());
    } catch {
      setUser(null);
    }
  }

  async function bootstrap() {
    setLoading(true);
    try {
      const h = await Api.health();
      setHealth(h);
      // single_user: /auth/me works without a token. multi_user: only if a token exists.
      if (h.auth_mode === "single_user" || localStorage.getItem("fitvise.token")) {
        await loadUser();
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    bootstrap();
  }, []);

  async function login(email: string, password: string) {
    const t = await Api.login(email, password);
    setToken(t.access_token);
    await loadUser();
  }
  async function register(name: string, email: string, password: string) {
    const t = await Api.register(name, email, password);
    setToken(t.access_token);
    await loadUser();
  }
  function logout() {
    setToken(null);
    setUser(null);
  }

  return (
    <Ctx.Provider
      value={{ user, health, loading, isMultiUser, login, register, logout, refresh: loadUser }}
    >
      {children}
    </Ctx.Provider>
  );
}

export const useAuth = () => useContext(Ctx);
