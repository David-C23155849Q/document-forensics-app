import { LogOut, ShieldCheck } from "lucide-react";
import React from "react";
import { useNavigate } from "react-router-dom";
import { currentUser, logout } from "../lib/api";

export default function DashboardLayout({ title, children }: { title: string; children: React.ReactNode }) {
  const navigate = useNavigate();
  const user = currentUser();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-indigo-400" />
          <span className="font-semibold tracking-tight">Word Forensics</span>
          <span className="text-slate-500">/</span>
          <span className="text-slate-300">{title}</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-slate-400">{user?.first_name || user?.username}</span>
          <button
            className="flex items-center gap-1 text-slate-400 hover:text-slate-100 transition"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            <LogOut className="w-4 h-4" /> Log out
          </button>
        </div>
      </header>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
