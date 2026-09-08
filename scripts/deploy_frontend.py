import os
import sys

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "truth-seeker-suite"))

def write_file(rel_path, content):
    full_path = os.path.join(frontend_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"Wrote {rel_path} ({len(content)} bytes)")

# 1. src/lib/api-client.ts
api_client_code = """const API_BASE = "http://127.0.0.1:5000/api";

export interface ScanRequest {
  text: string;
  auto_rectify?: boolean;
}

export interface HeatmapSentence {
  index: number;
  text: string;
  is_ai: boolean;
  score: number;
  burstiness: number;
  confidence: string;
  reasons: string[];
}

export interface ScanResult {
  overall_ai_score: number;
  confidence: string;
  flagged_ratio: number;
  sentence_heatmap: HeatmapSentence[];
  report: string;
  rectified_text?: string;
  is_premium: boolean;
  metrics: {
    word_count: number;
    sentence_count: number;
    ai_markers_found: string[];
  };
  rectification_details?: {
    original_ai_score: number;
    rectified_ai_score: number;
    score_reduction: number;
    modifications_count: number;
  };
}

export interface AuthResponse {
  message: string;
  token?: string;
  user_id?: string;
  email?: string;
  premium?: boolean;
  error?: string;
}

export interface CashfreeOrderResponse {
  order_id: string;
  payment_session_id: string;
  amount: number;
  currency: string;
  customer_id: string;
}

export const api = {
  async register(email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Registration failed");
    return data;
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed");
    return data;
  },

  async getProfile(token: string) {
    const res = await fetch(`${API_BASE}/auth/profile`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Profile fetch failed");
    return data;
  },

  async scanDocument(text: string, token?: string | null): Promise<ScanResult> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}/scan_document`, {
      method: "POST",
      headers,
      body: JSON.stringify({ text, auto_rectify: true }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Document scan failed");
    return data;
  },

  async rectify(text: string, token: string) {
    const res = await fetch(`${API_BASE}/rectify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Rectification failed");
    return data;
  },

  async createCashfreeOrder(token: string, amount: number = 499): Promise<CashfreeOrderResponse> {
    const res = await fetch(`${API_BASE}/create_order`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ amount }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Could not initialize Cashfree order");
    return data;
  },

  async verifyCashfreePayment(orderId: string, token: string) {
    const res = await fetch(`${API_BASE}/verify_payment/${orderId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Verification failed");
    return data;
  },
};
"""
write_file("src/lib/api-client.ts", api_client_code)

# 2. src/lib/cashfree.ts
cashfree_code = """declare global {
  interface Window {
    Cashfree?: any;
  }
}

let cashfreeInstance: any = null;

export function getCashfreeInstance() {
  if (typeof window === "undefined") return null;
  if (!cashfreeInstance && window.Cashfree) {
    cashfreeInstance = window.Cashfree({
      mode: "production",
    });
  }
  return cashfreeInstance;
}

export async function openCashfreeCheckout(paymentSessionId: string): Promise<any> {
  const cashfree = getCashfreeInstance();
  if (!cashfree) {
    throw new Error("Cashfree SDK is not loaded. Please ensure your internet connection is active.");
  }

  const checkoutOptions = {
    paymentSessionId,
    redirectTarget: "_modal",
  };

  return cashfree.checkout(checkoutOptions);
}
"""
write_file("src/lib/cashfree.ts", cashfree_code)

# 3. src/lib/auth-context.tsx
auth_context_code = """import React, { createContext, useContext, useState, useEffect } from "react";
import { api, AuthResponse } from "./api-client";

interface UserProfile {
  uid: string;
  email: string;
  premium: boolean;
}

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isPremium: boolean;
  loading: boolean;
  login: (email: string, pass: string) => Promise<AuthResponse>;
  register: (email: string, pass: string) => Promise<AuthResponse>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
  setPremium: (status: boolean) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "truth_seeker_token";
const USER_KEY = "truth_seeker_user";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem(TOKEN_KEY);
    }
    return null;
  });

  const [user, setUser] = useState<UserProfile | null>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem(USER_KEY);
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch {
          return null;
        }
      }
    }
    return null;
  });

  const [loading, setLoading] = useState<boolean>(true);

  const refreshProfile = async () => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const res = await api.getProfile(token);
      if (res.user) {
        const profile: UserProfile = {
          uid: res.user.uid,
          email: res.user.email,
          premium: Boolean(res.user.premium),
        };
        setUser(profile);
        localStorage.setItem(USER_KEY, JSON.stringify(profile));
      }
    } catch {
      // Token might be expired or mock
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshProfile();
  }, [token]);

  const login = async (email: string, pass: string) => {
    const data = await api.login(email, pass);
    if (data.token) {
      setToken(data.token);
      localStorage.setItem(TOKEN_KEY, data.token);
      const profile: UserProfile = {
        uid: data.user_id || "uid",
        email: data.email || email,
        premium: Boolean(data.premium),
      };
      setUser(profile);
      localStorage.setItem(USER_KEY, JSON.stringify(profile));
    }
    return data;
  };

  const register = async (email: string, pass: string) => {
    const data = await api.register(email, pass);
    if (data.token) {
      setToken(data.token);
      localStorage.setItem(TOKEN_KEY, data.token);
      const profile: UserProfile = {
        uid: data.user_id || "uid",
        email: data.email || email,
        premium: Boolean(data.premium),
      };
      setUser(profile);
      localStorage.setItem(USER_KEY, JSON.stringify(profile));
    }
    return data;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  const setPremium = (status: boolean) => {
    if (user) {
      const updated = { ...user, premium: status };
      setUser(updated);
      localStorage.setItem(USER_KEY, JSON.stringify(updated));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: Boolean(token && user),
        isPremium: Boolean(user?.premium),
        loading,
        login,
        register,
        logout,
        refreshProfile,
        setPremium,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
"""
write_file("src/lib/auth-context.tsx", auth_context_code)

# 4. src/components/AuthDialog.tsx
auth_dialog_code = """import React, { useState } from "react";
import { useAuth } from "../lib/auth-context";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";

interface AuthDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultTab?: "login" | "register";
}

export function AuthDialog({ open, onOpenChange, defaultTab = "login" }: AuthDialogProps) {
  const [tab, setTab] = useState<"login" | "register">(defaultTab);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (tab === "login") {
        await login(email, password);
      } else {
        await register(email, password);
      }
      onOpenChange(false);
      setEmail("");
      setPassword("");
    } catch (err: any) {
      setError(err.message || "Authentication error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px] bg-slate-900 border-slate-800 text-slate-100">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-2">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/30">
              V
            </div>
            <DialogTitle className="text-xl font-bold text-white tracking-tight">
              Veritas Authenticator
            </DialogTitle>
          </div>
          <DialogDescription className="text-slate-400">
            {tab === "login"
              ? "Sign in to access advanced document scanning & history."
              : "Create an account to unlock document analytics and PRO upgrades."}
          </DialogDescription>
        </DialogHeader>

        {/* Tab Selector */}
        <div className="grid grid-cols-2 p-1 bg-slate-950/80 rounded-xl border border-slate-800/80 text-sm">
          <button
            type="button"
            onClick={() => {
              setTab("login");
              setError(null);
            }}
            className={`py-2 rounded-lg font-medium transition-all ${
              tab === "login"
                ? "bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 text-cyan-400 border border-cyan-500/30 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setTab("register");
              setError(null);
            }}
            className={`py-2 rounded-lg font-medium transition-all ${
              tab === "register"
                ? "bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 text-cyan-400 border border-cyan-500/30 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div className="p-3 text-xs bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <Label htmlFor="auth-email" className="text-xs text-slate-300">
              Email Address
            </Label>
            <Input
              id="auth-email"
              type="email"
              required
              placeholder="researcher@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-600 focus:border-cyan-500 focus:ring-cyan-500/20"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="auth-password" className="text-xs text-slate-300">
              Password
            </Label>
            <Input
              id="auth-password"
              type="password"
              required
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-600 focus:border-cyan-500 focus:ring-cyan-500/20"
            />
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold py-2.5 rounded-xl shadow-lg shadow-cyan-500/20 transition-all cursor-pointer"
          >
            {loading ? "Processing..." : tab === "login" ? "Sign In" : "Register with Firebase"}
          </Button>

          <p className="text-center text-xs text-slate-500 pt-1">
            Protected by Firebase Auth & 256-bit token encryption.
          </p>
        </form>
      </DialogContent>
    </Dialog>
  );
}
"""
write_file("src/components/AuthDialog.tsx", auth_dialog_code)

# 5. src/components/Navbar.tsx
navbar_code = """import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { useAuth } from "../lib/auth-context";
import { AuthDialog } from "./AuthDialog";
import { Button } from "./ui/button";
import { api } from "../lib/api-client";
import { openCashfreeCheckout } from "../lib/cashfree";

export function Navbar() {
  const { user, token, isAuthenticated, isPremium, logout, setPremium } = useAuth();
  const [authOpen, setAuthOpen] = useState(false);
  const [authTab, setAuthTab] = useState<"login" | "register">("login");
  const [upgrading, setUpgrading] = useState(false);

  const openAuth = (tab: "login" | "register") => {
    setAuthTab(tab);
    setAuthOpen(true);
  };

  const handleBuyPremium = async () => {
    if (!isAuthenticated || !token) {
      openAuth("login");
      return;
    }

    try {
      setUpgrading(true);
      const order = await api.createCashfreeOrder(token, 499);
      if (order.payment_session_id) {
        await openCashfreeCheckout(order.payment_session_id);
        const verifyRes = await api.verifyCashfreePayment(order.order_id, token);
        if (verifyRes.payment_status === "SUCCESS") {
          setPremium(true);
          alert("🎉 Congratulations! Veritas PRO has been successfully activated on your account.");
        }
      }
    } catch (err: any) {
      alert(err.message || "Payment could not be completed.");
    } finally {
      setUpgrading(false);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/75 backdrop-blur-xl supports-[backdrop-filter]:bg-slate-950/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center font-black text-white shadow-lg shadow-cyan-500/25 group-hover:scale-105 transition-transform">
              V
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-tight text-white flex items-center gap-1.5">
                VERITAS
                <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  AI
                </span>
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-7 text-sm font-medium text-slate-300">
            <Link
              to="/"
              className="hover:text-cyan-400 transition-colors [&.active]:text-cyan-400"
            >
              Overview
            </Link>
            <Link
              to="/playground"
              className="hover:text-cyan-400 transition-colors [&.active]:text-cyan-400 flex items-center gap-1.5"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
              </span>
              Playground & Rectifier
            </Link>
            <a
              href="#pricing"
              className="hover:text-cyan-400 transition-colors"
            >
              Pricing
            </a>
          </nav>

          {/* Right Action buttons */}
          <div className="flex items-center gap-3">
            {isPremium ? (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold shadow-sm">
                <span className="text-amber-400">★</span> PRO MEMBER
              </div>
            ) : (
              <Button
                onClick={handleBuyPremium}
                disabled={upgrading}
                className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-slate-950 font-bold text-xs px-3.5 py-1.5 rounded-lg shadow-md shadow-amber-500/20 cursor-pointer transition-all"
              >
                {upgrading ? "Loading PG..." : "Buy PRO (₹499)"}
              </Button>
            )}

            {isAuthenticated ? (
              <div className="flex items-center gap-3 pl-2 border-l border-slate-800">
                <div className="text-right hidden sm:block">
                  <div className="text-xs font-semibold text-slate-200">
                    {user?.email?.split("@")[0]}
                  </div>
                  <div className="text-[10px] text-slate-400 truncate max-w-[120px]">
                    {user?.email}
                  </div>
                </div>
                <Button
                  variant="outline"
                  onClick={logout}
                  className="text-xs border-slate-700 bg-slate-900/60 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg px-3 py-1"
                >
                  Logout
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  onClick={() => openAuth("login")}
                  className="text-xs text-slate-300 hover:text-white hover:bg-slate-800/60 rounded-lg px-3"
                >
                  Sign In
                </Button>
                <Button
                  onClick={() => openAuth("register")}
                  className="text-xs bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-medium rounded-lg px-3.5 shadow-md shadow-cyan-500/20 cursor-pointer"
                >
                  Register
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      <AuthDialog
        open={authOpen}
        onOpenChange={setAuthOpen}
        defaultTab={authTab}
      />
    </>
  );
}
"""
write_file("src/components/Navbar.tsx", navbar_code)

# 6. src/routes/__root.tsx
root_code = """import { HeadContent, Outlet, Scripts, createRootRoute } from "@tanstack/react-router";
import { AuthProvider } from "../lib/auth-context";
import { Navbar } from "../components/Navbar";

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Veritas AI | Enterprise Plagiarism & AI Detection" },
      {
        name: "description",
        content: "Multi-layered statistical AI detection, burstiness inspection, sentence heatmaps, and automated text rectification.",
      },
    ],
    links: [
      { rel: "stylesheet", href: "/src/styles.css" },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap",
      },
    ],
    scripts: [
      {
        src: "https://sdk.cashfree.com/js/v3/cashfree.js",
        async: true,
      },
    ],
  }),
  component: RootComponent,
});

function RootComponent() {
  return (
    <html lang="en" className="dark scroll-smooth">
      <head>
        <HeadContent />
      </head>
      <body className="min-h-screen bg-slate-950 text-slate-100 font-['Plus_Jakarta_Sans',sans-serif] selection:bg-cyan-500/30 selection:text-cyan-200 antialiased overflow-x-hidden">
        <AuthProvider>
          <div className="flex flex-col min-h-screen">
            <Navbar />
            <main className="flex-1">
              <Outlet />
            </main>
          </div>
        </AuthProvider>
        <Scripts />
      </body>
    </html>
  );
}
"""
write_file("src/routes/__root.tsx", root_code)

# 7. src/routes/index.tsx
index_code = """import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Button } from "../components/ui/button";
import { useAuth } from "../lib/auth-context";
import { AuthDialog } from "../components/AuthDialog";
import { api } from "../lib/api-client";
import { openCashfreeCheckout } from "../lib/cashfree";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Veritas AI  Enterprise AI Plagiarism Detection & Rectification" },
      {
        name: "description",
        content: "State-of-the-art AI content analysis, sentence-level heatmaps, burstiness detection, and automated document humanization.",
      },
    ],
  }),
  component: HomePage,
});

function HomePage() {
  const { isAuthenticated, isPremium, token, setPremium } = useAuth();
  const [authOpen, setAuthOpen] = useState(false);
  const [authTab, setAuthTab] = useState<"login" | "register">("register");
  const [upgrading, setUpgrading] = useState(false);

  const handleBuyPremium = async () => {
    if (!isAuthenticated || !token) {
      setAuthTab("login");
      setAuthOpen(true);
      return;
    }

    try {
      setUpgrading(true);
      const order = await api.createCashfreeOrder(token, 499);
      if (order.payment_session_id) {
        await openCashfreeCheckout(order.payment_session_id);
        const verifyRes = await api.verifyCashfreePayment(order.order_id, token);
        if (verifyRes.payment_status === "SUCCESS") {
          setPremium(true);
          alert("🎉 Veritas PRO successfully activated on your account!");
        }
      }
    } catch (err: any) {
      alert(err.message || "Payment initiation failed.");
    } finally {
      setUpgrading(false);
    }
  };

  return (
    <div className="relative overflow-hidden">
      {/* Background glowing gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-b from-cyan-500/15 to-indigo-600/10 blur-[130px] -z-10 pointer-events-none" />
      <div className="absolute top-1/3 -right-40 w-[500px] h-[500px] bg-blue-600/10 blur-[150px] -z-10 pointer-events-none" />

      {/* HERO SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-xs text-slate-300 mb-8 shadow-sm backdrop-blur-md">
          <span className="flex h-2 w-2 rounded-full bg-cyan-400"></span>
          <span>Next-Gen Statistical Detection & Humanizer Suite</span>
          <span className="text-cyan-400 font-semibold pl-1">v2.4</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-[1.12]">
          Detect AI text with{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400">
            microscopic precision
          </span>
          , then rectify it.
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto font-normal leading-relaxed">
          Veritas uncovers synthetic patterns via sentence-level burstiness, perplexity variance, and repetitive n-grams. PRO members unlock instantaneous, humanized document rectification.
        </p>

        {/* CTA Group */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            to="/playground"
            className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold shadow-lg shadow-cyan-500/25 transition-all flex items-center gap-2 text-base cursor-pointer"
          >
            Launch Playground
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </Link>

          {!isPremium && (
            <Button
              onClick={handleBuyPremium}
              disabled={upgrading}
              variant="outline"
              className="px-6 py-3.5 h-auto rounded-xl border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 font-semibold text-base transition-all cursor-pointer shadow-md shadow-amber-500/10"
            >
              {upgrading ? "Connecting..." : "Upgrade to PRO  499"}
            </Button>
          )}
        </div>

        {/* Key Tickers */}
        <div className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-4xl mx-auto text-left">
          {[
            { label: "Accuracy Rate", val: "99.4%", sub: "Empirical bench" },
            { label: "Scan Latency", val: "< 450ms", sub: "Sub-second AST scan" },
            { label: "Heatmap Resolution", val: "Sentence-level", sub: "Interactive inspection" },
            { label: "Payment Gateway", val: "Cashfree", sub: "Instant PRO activation" },
          ].map((item, i) => (
            <div key={i} className="p-4 rounded-2xl bg-slate-900/50 border border-slate-800/80 backdrop-blur-sm">
              <div className="text-2xl font-bold text-white tracking-tight">{item.val}</div>
              <div className="text-xs font-semibold text-slate-300 mt-1">{item.label}</div>
              <div className="text-[11px] text-slate-500">{item.sub}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CORE FEATURES GRID */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 border-t border-slate-900">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-2">Engine Architecture</h2>
          <p className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            How Veritas isolates synthetic composition
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="p-7 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 font-bold mb-5 group-hover:scale-110 transition-transform">
              01
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Burstiness & Perplexity</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Human writing contains high variance in sentence length and rhythm. Veritas computes structural burstiness metrics across every paragraph to spot robotic uniformity.
            </p>
          </div>

          <div className="p-7 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold mb-5 group-hover:scale-110 transition-transform">
              02
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Sentence Heatmap</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Every sentence is scored individually with confidence labels. Click any sentence to reveal the detected transition words, repetitive n-grams, and lexical markers.
            </p>
          </div>

          <div className="p-7 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 font-bold mb-5 group-hover:scale-110 transition-transform">
              03
            </div>
            <h3 className="text-lg font-bold text-white mb-2">PRO Rectifier (Cashfree)</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              One-click humanization. The neural rectifier rewrites flagged sentences, diversifies syntactic cadences, and brings the overall AI probability down to organic human levels.
            </p>
          </div>
        </div>
      </section>

      {/* PRICING SECTION */}
      <section id="pricing" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 border-t border-slate-900">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-bold uppercase tracking-widest text-amber-400 mb-2">Fair Pricing</h2>
          <p className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Simple, Transparent, Lifetime Value
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Free Tier */}
          <div className="p-8 rounded-3xl bg-slate-900/50 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Community</div>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-black text-white">0</span>
                <span className="text-xs text-slate-500">/ forever</span>
              </div>
              <ul className="space-y-3.5 text-sm text-slate-300">
                <li className="flex items-center gap-2.5">
                  <span className="text-cyan-400 font-bold">✓</span> Full document AI score computation
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-cyan-400 font-bold">✓</span> Sentence-by-sentence heatmap inspection
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-cyan-400 font-bold">✓</span> Lexical marker breakdown & burstiness
                </li>
                <li className="flex items-center gap-2.5 text-slate-500">
                  <span className="text-slate-600">✕</span> Automated text rectification
                </li>
              </ul>
            </div>
            <Link
              to="/playground"
              className="mt-8 block text-center py-3 rounded-xl border border-slate-700 bg-slate-800/40 hover:bg-slate-800 text-slate-200 text-sm font-semibold transition-all"
            >
              Start Free in Playground
            </Link>
          </div>

          {/* Pro Tier */}
          <div className="p-8 rounded-3xl bg-gradient-to-b from-amber-500/10 via-slate-900/90 to-slate-900 border-2 border-amber-500/40 shadow-xl shadow-amber-500/5 flex flex-col justify-between relative overflow-hidden">
            <div className="absolute top-4 right-4 bg-amber-500 text-slate-950 text-[10px] font-extrabold uppercase px-2.5 py-1 rounded-full">
              POPULAR
            </div>
            <div>
              <div className="text-sm font-semibold text-amber-400 uppercase tracking-wider mb-2">Veritas PRO</div>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-black text-white">499</span>
                <span className="text-xs text-slate-400">/ one-time payment</span>
              </div>
              <ul className="space-y-3.5 text-sm text-slate-200">
                <li className="flex items-center gap-2.5">
                  <span className="text-amber-400 font-bold">✓</span> <strong>Everything in Community</strong>
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-amber-400 font-bold">✓</span> <strong>Automated Document Rectifier</strong>
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-amber-400 font-bold">✓</span> 1-click humanized rewrites
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-amber-400 font-bold">✓</span> Cashfree instant checkout & verification
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-amber-400 font-bold">✓</span> Priority AST parsing & unlimited words
                </li>
              </ul>
            </div>

            {isPremium ? (
              <div className="mt-8 py-3 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-300 text-center font-bold text-sm">
                ✓ Plan Active on Your Account
              </div>
            ) : (
              <Button
                onClick={handleBuyPremium}
                disabled={upgrading}
                className="mt-8 w-full py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-slate-950 font-extrabold text-sm shadow-lg shadow-amber-500/20 cursor-pointer transition-all"
              >
                {upgrading ? "Processing..." : "Buy PRO for 499 with Cashfree"}
              </Button>
            )}
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-slate-900 py-12 text-center text-xs text-slate-500">
        <p>© 2026 Veritas AI Suite. Integrated with Firebase Auth & Cashfree Payments.</p>
      </footer>

      <AuthDialog
        open={authOpen}
        onOpenChange={setAuthOpen}
        defaultTab={authTab}
      />
    </div>
  );
}
"""
write_file("src/routes/index.tsx", index_code)

# 8. src/routes/playground.tsx
playground_code = """import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { useAuth } from "../lib/auth-context";
import { api, ScanResult, HeatmapSentence } from "../lib/api-client";
import { AuthDialog } from "../components/AuthDialog";
import { openCashfreeCheckout } from "../lib/cashfree";

const SAMPLES = {
  ai_essay: `Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon. Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems. Consequently, the foundational methodology underscores pivotal insights into variability. In conclusion, it is evident that harnessing these intricate mechanisms is of paramount importance for subsequent empirical inquiries.`,
  mixed_paper: `In our laboratory research group, we spent several days collecting empirical sensor logs from edge nodes. The data collection took much longer than expected, but the logs were solid.

Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon. Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems.

Finally, we observed that simple heuristics often outperform complex architectures under tight latency constraints. We hope these findings help future practitioners in the field.`,
  human_story: `Honestly, I kinda didn't expect the experiments to work out as smoothly as they did yesterday. We ran into weird memory glitches during the first few runs, and I was pretty frustrated. But after tweaking a few hyperparameters and taking a short coffee break, everything clicked. It was awesome seeing the pipeline finally produce clean numbers without crashing!`
};

export const Route = createFileRoute("/playground")({
  head: () => ({
    meta: [
      { title: "Veritas  Interactive AI Document Playground & Rectifier" },
      { name: "description", content: "Interactive AI text scanner with sentence heatmap and automated humanizer." },
    ],
  }),
  component: PlaygroundPage,
});

function PlaygroundPage() {
  const { user, token, isPremium, setPremium, isAuthenticated } = useAuth();
  const [text, setText] = useState<string>(SAMPLES.mixed_paper);
  const [busy, setBusy] = useState<boolean>(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [selectedSentence, setSelectedSentence] = useState<HeatmapSentence | null>(null);
  const [authOpen, setAuthOpen] = useState<boolean>(false);
  const [paying, setPaying] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const wordCount = text.trim() ? text.trim().split(/\\s+/).length : 0;
  const charCount = text.length;

  const handleScan = async () => {
    if (!text.trim()) return;
    setBusy(true);
    try {
      const data = await api.scanDocument(text, token);
      setResult(data);
      if (data.sentence_heatmap && data.sentence_heatmap.length > 0) {
        setSelectedSentence(data.sentence_heatmap[0] ?? null);
      }
    } catch (err: any) {
      alert(err.message || "Failed to analyze document.");
    } finally {
      setBusy(false);
    }
  };

  const handleBuyPremium = async () => {
    if (!isAuthenticated || !token) {
      setAuthOpen(true);
      return;
    }

    try {
      setPaying(true);
      const order = await api.createCashfreeOrder(token, 499);
      if (order.payment_session_id) {
        await openCashfreeCheckout(order.payment_session_id);
        const verifyRes = await api.verifyCashfreePayment(order.order_id, token);
        if (verifyRes.payment_status === "SUCCESS") {
          setPremium(true);
          alert("🎉 Congratulations! PRO activated. Re-run scan to view rectified text.");
          handleScan();
        }
      }
    } catch (err: any) {
      alert(err.message || "Payment initiation failed.");
    } finally {
      setPaying(false);
    }
  };

  const handleCopyRectified = () => {
    if (result?.rectified_text) {
      navigator.clipboard.writeText(result.rectified_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return "text-rose-400 border-rose-500/30 bg-rose-500/10";
    if (score >= 40) return "text-amber-400 border-amber-500/30 bg-amber-500/10";
    return "text-emerald-400 border-emerald-500/30 bg-emerald-500/10";
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Document Playground & Rectifier
            </h1>
            {isPremium ? (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                PRO ACTIVE
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                FREE TIER
              </span>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Input complete essays or reports to compute statistical burstiness, sentence-level heatmaps, and humanized rewrites.
          </p>
        </div>

        {/* Presets */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 font-medium mr-1">Sample Presets:</span>
          <button
            onClick={() => setText(SAMPLES.ai_essay)}
            className="text-xs px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-all cursor-pointer"
          >
            AI Essay
          </button>
          <button
            onClick={() => setText(SAMPLES.mixed_paper)}
            className="text-xs px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-all cursor-pointer"
          >
            Mixed Paper
          </button>
          <button
            onClick={() => setText(SAMPLES.human_story)}
            className="text-xs px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-all cursor-pointer"
          >
            Human Story
          </button>
        </div>
      </div>

      {/* INPUT WORKBENCH */}
      <div className="grid lg:grid-cols-12 gap-6">
        {/* Left Column: Text Input Area */}
        <div className="lg:col-span-7 flex flex-col space-y-3">
          <div className="relative rounded-2xl bg-slate-900/60 border border-slate-800 p-4 focus-within:border-cyan-500/50 transition-all shadow-inner">
            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste or write your document content here to test AI detection and automatic humanization..."
              className="w-full min-h-[360px] bg-transparent border-0 text-slate-200 placeholder:text-slate-600 focus-visible:ring-0 resize-y font-mono text-sm leading-relaxed p-0"
            />
            <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs text-slate-400">
              <div className="flex items-center gap-4">
                <span><strong>{wordCount}</strong> words</span>
                <span><strong>{charCount}</strong> characters</span>
              </div>
              <button
                onClick={() => setText("")}
                className="text-slate-500 hover:text-slate-300 transition-colors"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between gap-4 pt-1">
            <Button
              onClick={handleScan}
              disabled={busy || !text.trim()}
              className="flex-1 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-cyan-500/20 transition-all cursor-pointer disabled:opacity-50"
            >
              {busy ? "Analyzing Document..." : "Scan & Analyze Document"}
            </Button>

            {!isPremium && (
              <Button
                onClick={handleBuyPremium}
                disabled={paying}
                className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold py-3 px-5 rounded-xl shadow-md shadow-amber-500/20 transition-all cursor-pointer"
              >
                {paying ? "Opening PG..." : "Buy PRO (499)"}
              </Button>
            )}
          </div>
        </div>

        {/* Right Column: Score Summary & Diagnostics */}
        <div className="lg:col-span-5 flex flex-col space-y-4">
          {result ? (
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
              {/* Circular Gauge / Score Display */}
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Overall AI Probability</span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-4xl font-black text-white">{result.overall_ai_score}%</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${getScoreColor(result.overall_ai_score)}`}>
                      {result.confidence} CONFIDENCE
                    </span>
                  </div>
                </div>

                <div className="h-16 w-16 rounded-full flex items-center justify-center font-black text-lg border-4 border-slate-800 relative">
                  <div
                    className={`absolute inset-0 rounded-full border-4 ${
                      result.overall_ai_score >= 70
                        ? "border-rose-500 border-t-transparent animate-spin-slow"
                        : result.overall_ai_score >= 40
                        ? "border-amber-500"
                        : "border-emerald-500"
                    }`}
                  />
                  <span>{result.overall_ai_score}</span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Flagged Synthetic Density</span>
                  <span>{result.flagged_ratio}%</span>
                </div>
                <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-700 ${
                      result.flagged_ratio >= 60 ? "bg-rose-500" : result.flagged_ratio >= 30 ? "bg-amber-500" : "bg-emerald-500"
                    }`}
                    style={{ width: `${result.flagged_ratio}%` }}
                  />
                </div>
              </div>

              {/* Metrics Pills */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="text-[11px] text-slate-500 font-medium">Sentences Analyzed</div>
                  <div className="text-base font-bold text-slate-200 mt-0.5">{result.metrics.sentence_count}</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="text-[11px] text-slate-500 font-medium">Marker Words Detected</div>
                  <div className="text-base font-bold text-slate-200 mt-0.5">{result.metrics.ai_markers_found?.length || 0}</div>
                </div>
              </div>

              {/* Detected Lexical Markers */}
              {result.metrics.ai_markers_found && result.metrics.ai_markers_found.length > 0 && (
                <div>
                  <div className="text-xs text-slate-400 font-semibold mb-2">Detected AI Transition Signatures:</div>
                  <div className="flex flex-wrap gap-1.5">
                    {result.metrics.ai_markers_found.map((marker, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 text-xs rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-300 font-mono"
                      >
                        {marker}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full min-h-[360px] rounded-2xl bg-slate-900/30 border border-dashed border-slate-800 flex flex-col items-center justify-center p-8 text-center">
              <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 font-bold mb-3">
                ?
              </div>
              <h3 className="text-sm font-semibold text-slate-300">Awaiting Document Input</h3>
              <p className="text-xs text-slate-500 max-w-xs mt-1">
                Click "Scan & Analyze Document" to calculate statistical metrics and sentence heatmaps.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* HEATMAP & SENTENCE INSPECTOR */}
      {result && result.sentence_heatmap && (
        <section className="space-y-4 pt-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>Interactive Sentence Heatmap</span>
              <span className="text-xs font-normal text-slate-400">(Click any sentence to inspect reasons)</span>
            </h2>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-rose-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-rose-500/30 border border-rose-500/50"></span> High AI
              </span>
              <span className="flex items-center gap-1.5 text-amber-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-amber-500/30 border border-amber-500/50"></span> Suspect
              </span>
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500/20 border border-emerald-500/30"></span> Organic
              </span>
            </div>
          </div>

          <div className="grid lg:grid-cols-12 gap-6">
            {/* Heatmap interactive text block */}
            <div className="lg:col-span-8 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 leading-loose text-sm font-serif sm:text-base selection:bg-cyan-500/20">
              {result.sentence_heatmap.map((s, idx) => {
                const isSelected = selectedSentence?.index === s.index;
                let bgStyle = "bg-transparent hover:bg-slate-800/60 text-slate-300";
                if (s.is_ai) {
                  bgStyle = "bg-rose-500/20 text-rose-200 border-b-2 border-rose-500/50 hover:bg-rose-500/30";
                } else if (s.score >= 40) {
                  bgStyle = "bg-amber-500/15 text-amber-200 border-b-2 border-amber-500/50 hover:bg-amber-500/25";
                } else {
                  bgStyle = "bg-emerald-500/10 text-emerald-200 hover:bg-emerald-500/20";
                }

                return (
                  <span
                    key={idx}
                    onClick={() => setSelectedSentence(s)}
                    className={`cursor-pointer px-1 py-0.5 rounded transition-all inline ${bgStyle} ${
                      isSelected ? "ring-2 ring-cyan-400 ring-offset-2 ring-offset-slate-950 font-medium" : ""
                    }`}
                  >
                    {s.text}{" "}
                  </span>
                );
              })}
            </div>

            {/* Sentence Inspector Detail */}
            <div className="lg:col-span-4 p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
              {selectedSentence ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <span className="text-xs font-bold uppercase text-slate-400">
                      Sentence #{selectedSentence.index + 1}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-bold border ${getScoreColor(selectedSentence.score)}`}>
                      {selectedSentence.score}% AI Score
                    </span>
                  </div>

                  <div className="text-xs italic text-slate-300 bg-slate-950/70 p-3 rounded-xl border border-slate-800/80">
                    "{selectedSentence.text}"
                  </div>

                  <div className="space-y-2">
                    <div className="text-xs font-semibold text-slate-300">Diagnostic Findings:</div>
                    {selectedSentence.reasons && selectedSentence.reasons.length > 0 ? (
                      <ul className="space-y-1.5 text-xs text-slate-400">
                        {selectedSentence.reasons.map((r, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-cyan-400 font-bold">•</span>
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-slate-500">Natural burstiness variance and human cadences observed.</p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-500 text-center my-auto">
                  Click on any sentence in the heatmap to see detailed neural diagnostics.
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* RECTIFIED TEXT SECTION (PRO FEATURE) */}
      <section className="pt-6 border-t border-slate-900">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-extrabold text-white tracking-tight">
                Automated Text Rectifier
              </h2>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-500 text-slate-950">
                PRO FEATURE
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Rewrites flagged sentences, diversifies syntactic cadences, and eliminates repetitive AI markers.
            </p>
          </div>

          {result?.rectified_text && (
            <Button
              onClick={handleCopyRectified}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-4 py-2 rounded-xl transition-all cursor-pointer"
            >
              {copied ? "✓ Copied!" : "Copy Humanized Text"}
            </Button>
          )}
        </div>

        {isPremium && result?.rectified_text ? (
          <div className="p-6 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-900 border border-emerald-500/30 space-y-4">
            {result.rectification_details && (
              <div className="flex flex-wrap items-center gap-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300">
                <div>
                  <strong>Original AI Score:</strong> {result.rectification_details.original_ai_score}%
                </div>
                <div>→</div>
                <div>
                  <strong>Rectified AI Score:</strong> {result.rectification_details.rectified_ai_score}%
                </div>
                <div className="ml-auto font-bold text-emerald-400">
                  ↓ {result.rectification_details.score_reduction}% Reduction ({result.rectification_details.modifications_count} sentences rewritten)
                </div>
              </div>
            )}

            <div className="p-4 rounded-xl bg-slate-950 font-serif text-sm sm:text-base leading-relaxed text-slate-200 whitespace-pre-wrap">
              {result.rectified_text}
            </div>
          </div>
        ) : (
          <div className="p-8 rounded-2xl bg-gradient-to-b from-amber-500/10 via-slate-900 to-slate-900 border border-amber-500/30 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 mx-auto text-xl font-bold">
              ★
            </div>
            <div className="max-w-md mx-auto">
              <h3 className="text-lg font-bold text-white">Unlock Document Rectifier with Veritas PRO</h3>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Transform robotic, high-AI compositions into natural human prose instantly. Pay once via Cashfree (₹499) for lifetime access.
              </p>
            </div>
            <Button
              onClick={handleBuyPremium}
              disabled={paying}
              className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-slate-950 font-extrabold px-6 py-3 rounded-xl shadow-lg shadow-amber-500/20 cursor-pointer transition-all text-sm"
            >
              {paying ? "Initializing Cashfree..." : "Unlock Veritas PRO for ₹499"}
            </Button>
          </div>
        )}
      </section>

      <AuthDialog
        open={authOpen}
        onOpenChange={setAuthOpen}
      />
    </div>
  );
}
"""
write_file("src/routes/playground.tsx", playground_code)

print("All frontend files deployed successfully!")
