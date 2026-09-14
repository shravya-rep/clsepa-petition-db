import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import client from "../api/client";
import { User } from "../api/types";

interface AuthState {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));

  useEffect(() => {
    if (!token) {
      setUser(null);
      return;
    }
    // Decode JWT payload to get user info
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      setUser({ id: payload.sub, email: "", full_name: null, is_admin: true, created_at: "" });
    } catch {
      setUser(null);
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const res = await client.post("/api/auth/login", form);
    const newToken = res.data.access_token;
    localStorage.setItem("token", newToken);
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAdmin: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
