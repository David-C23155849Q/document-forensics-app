import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";
import { Api, Assignment, Submission } from "../lib/api";

export default function AssignmentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);

  useEffect(() => {
    if (!id) return;
    Api.assignment(Number(id)).then(setAssignment);
    Api.submissionsForAssignment(Number(id)).then(setSubmissions);
  }, [id]);

  return (
    <DashboardLayout title={assignment?.title || "Assignment"}>
      <div className="max-w-6xl mx-auto space-y-6">
        {assignment && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h1 className="text-xl font-semibold">{assignment.title}</h1>
            <p className="text-sm text-slate-500">{assignment.course}</p>
            <div className="grid grid-cols-3 gap-6 mt-4 text-sm">
              <div>
                <p className="text-slate-500 text-xs">Deadline</p>
                <p>{new Date(assignment.deadline).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs">Submissions</p>
                <p>{submissions.length}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs">Status</p>
                <p>{assignment.status}</p>
              </div>
            </div>
          </div>
        )}

        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-800/60 text-slate-400 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3">Student</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Word count</th>
                <th className="text-left px-4 py-3">Submitted</th>
                <th className="text-left px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {submissions.map((s) => (
                <tr key={s.id} className="border-t border-slate-800 hover:bg-slate-800/40">
                  <td className="px-4 py-3">{s.student_name}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">{s.status}</span>
                  </td>
                  <td className="px-4 py-3">{s.final_word_count || "—"}</td>
                  <td className="px-4 py-3">{s.submitted_at ? new Date(s.submitted_at).toLocaleString() : "—"}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      className="text-indigo-400 hover:text-indigo-300 text-xs font-medium"
                      onClick={() => navigate(`/submissions/${s.id}`)}
                    >
                      Inspect →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {submissions.length === 0 && <p className="p-6 text-sm text-slate-500">No submissions yet.</p>}
        </div>
      </div>
    </DashboardLayout>
  );
}
