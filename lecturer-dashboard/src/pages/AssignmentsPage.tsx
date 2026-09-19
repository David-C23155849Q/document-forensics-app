import { FileText, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";
import { Api, Assignment } from "../lib/api";

const statusColors: Record<string, string> = {
  DRAFT: "bg-slate-700 text-slate-300",
  SCHEDULED: "bg-amber-900 text-amber-300",
  ACTIVE: "bg-emerald-900 text-emerald-300",
  CLOSED: "bg-rose-900 text-rose-300",
  ARCHIVED: "bg-slate-800 text-slate-500",
};

export default function AssignmentsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    Api.assignments()
      .then((data: any) => {
        // Handle both plain arrays and DRF paginated responses ({ results: [...] })
        const list = Array.isArray(data) ? data : (data?.results || []);
        setAssignments(list);
      })
      .catch(() => setError("Could not reach the API. Is the Django backend running on :8000?"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout title="Assignments">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Your Assignments</h1>
        </div>

        {error && <p className="text-rose-400 text-sm">{error}</p>}
        {loading && <p className="text-slate-500 text-sm">Loading...</p>}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {assignments.map((a) => (
            <button
              key={a.id}
              onClick={() => navigate(`/assignments/${a.id}`)}
              className="text-left bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-indigo-600 transition space-y-3"
            >
              <div className="flex items-center justify-between">
                <FileText className="w-5 h-5 text-indigo-400" />
                <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[a.status] || "bg-slate-800"}`}>
                  {a.status}
                </span>
              </div>
              <div>
                <h2 className="font-medium">{a.title}</h2>
                <p className="text-xs text-slate-500">{a.course}</p>
              </div>
              <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-800">
                <span>Deadline: {new Date(a.deadline).toLocaleDateString()}</span>
                <span className="flex items-center gap-1">
                  <Users className="w-3.5 h-3.5" /> {a.submission_count}
                </span>
              </div>
            </button>
          ))}
        </div>

        {!loading && !error && assignments.length === 0 && (
          <p className="text-slate-500 text-sm">No assignments yet. Run `python manage.py seed_demo_data` on the backend.</p>
        )}
      </div>
    </DashboardLayout>
  );
}
