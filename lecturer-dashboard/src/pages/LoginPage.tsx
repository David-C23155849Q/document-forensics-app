import { ShieldCheck } from "lucide-react";
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../lib/api";

export default function LoginPage() {
  const [username, setUsername] = useState("lecturer1");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate("/");
    } catch {
      setError("Invalid credentials, or the backend isn't running yet.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-xl p-8 space-y-5">
        <div className="flex items-center gap-2 justify-center mb-2">
          <ShieldCheck className="w-6 h-6 text-indigo-400" />
          <h1 className="text-lg font-semibold">Word Forensics</h1>
        </div>
        <p className="text-center text-sm text-slate-500">Lecturer Dashboard</p>

        <div>
          <label className="block text-xs text-slate-400 mb-1">Username</label>
          <input
            className="w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Password</label>
          <input
            type="password"
            className="w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-500 transition rounded-md py-2 text-sm font-medium disabled:opacity-50"
        >
          {loading ? "Signing in..." : "Log in"}
        </button>
        <p className="text-xs text-slate-600 text-center">
          Demo: lecturer1 / password123 (after running seed_demo_data)
        </p>
      </form>
    </div>
  );
}
