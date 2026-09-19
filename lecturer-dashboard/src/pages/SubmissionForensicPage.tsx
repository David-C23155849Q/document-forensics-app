import { AlertTriangle, Circle, Diamond, FileWarning, Square } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useParams } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";
import { Api, AnalyticsResponse, ForensicEventRow, Submission } from "../lib/api";

const EVENT_ICON: Record<string, JSX.Element> = {
  insertion: <Diamond className="w-3.5 h-3.5 text-sky-400" />,
  large_insertion: <Square className="w-3.5 h-3.5 text-amber-400" />,
  deletion: <Circle className="w-3.5 h-3.5 text-rose-400" />,
  large_deletion: <Square className="w-3.5 h-3.5 text-rose-500" />,
  replacement: <AlertTriangle className="w-3.5 h-3.5 text-fuchsia-400" />,
  idle_started: <Circle className="w-3.5 h-3.5 text-slate-500" />,
};

function eventLabel(type: string) {
  return type
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export default function SubmissionForensicPage() {
  const { id } = useParams();
  const submissionId = Number(id);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [events, setEvents] = useState<ForensicEventRow[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<ForensicEventRow | null>(null);
  const [documentText, setDocumentText] = useState<string>("");
  const [mlSignals, setMlSignals] = useState<{ type: string; severity: string; description: string }[]>([]);

  useEffect(() => {
    if (!submissionId) return;
    Api.submission(submissionId).then(setSubmission);
    Api.events(submissionId).then((rows) => {
      setEvents(rows);
      const firstLarge = rows.find((r) => r.event_type === "large_insertion") || rows[rows.length - 1];
      if (firstLarge) setSelectedEvent(firstLarge);
    });
    Api.analytics(submissionId).then(setAnalytics);
    Api.mlAnalysis(submissionId)
      .then((data: any) => {
        const latest = Array.isArray(data) ? data[0] : data?.results?.[0];
        setMlSignals(latest?.signals || []);
      })
      .catch(() => setMlSignals([]));
    Api.documentState(submissionId).then((d) => setDocumentText(d.content || ""));
  }, [submissionId]);

  useEffect(() => {
    if (selectedEvent) {
      Api.documentState(submissionId, selectedEvent.timestamp).then((d) => setDocumentText(d.content || ""));
    }
  }, [selectedEvent, submissionId]);

  const chartData = useMemo(
    () =>
      (analytics?.word_count_trajectory || []).map((p) => ({
        time: new Date(p.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        words: p.word_count,
      })),
    [analytics]
  );

  const highlightedText = useMemo(() => {
    if (!selectedEvent?.inserted_text) return null;
    const idx = documentText.indexOf(selectedEvent.inserted_text.slice(0, 40));
    if (idx === -1) return null;
    return {
      before: documentText.slice(0, idx),
      highlighted: selectedEvent.inserted_text,
      after: documentText.slice(idx + selectedEvent.inserted_text.length),
    };
  }, [documentText, selectedEvent]);

  return (
    <DashboardLayout title={submission ? `${submission.student_name} — ${submission.assignment_title}` : "Submission"}>
      <div className="max-w-[1600px] mx-auto space-y-4">
        {/* Stats bar */}
        <div className="grid grid-cols-4 gap-4">
          <StatCard label="Words" value={submission?.final_word_count ?? "—"} />
          <StatCard label="Events" value={analytics?.events.total_events ?? "—"} />
          <StatCard label="Large insertions" value={analytics?.events.counts_by_type?.large_insertion ?? 0} />
          <StatCard label="Longest inactivity" value={`${Math.round((analytics?.events.longest_inactivity_seconds ?? 0) / 60)} min`} />
        </div>

        <div className="grid grid-cols-12 gap-4">
          {/* Timeline */}
          <div className="col-span-3 bg-slate-900 border border-slate-800 rounded-xl p-4 max-h-[70vh] overflow-y-auto">
            <h3 className="text-xs uppercase text-slate-500 mb-3 tracking-wide">Timeline</h3>
            <ul className="space-y-1">
              {events.map((e) => (
                <li key={e.id}>
                  <button
                    onClick={() => setSelectedEvent(e)}
                    className={`w-full text-left flex items-center gap-2 px-2 py-1.5 rounded-md text-xs transition ${
                      selectedEvent?.id === e.id ? "bg-indigo-950 text-indigo-300" : "hover:bg-slate-800 text-slate-300"
                    }`}
                  >
                    {EVENT_ICON[e.event_type] || <Circle className="w-3.5 h-3.5 text-slate-500" />}
                    <span className="text-slate-500 w-14 shrink-0">
                      {new Date(e.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <span className="truncate">{eventLabel(e.event_type)}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Document viewer */}
          <div className="col-span-6 bg-slate-900 border border-slate-800 rounded-xl p-6 max-h-[70vh] overflow-y-auto">
            <h3 className="text-xs uppercase text-slate-500 mb-3 tracking-wide">Document</h3>
            <div className="prose prose-invert prose-sm max-w-none leading-relaxed">
              {highlightedText ? (
                <p>
                  {highlightedText.before}{" "}
                  <mark className="bg-amber-500/30 text-amber-200 rounded px-1">{highlightedText.highlighted}</mark>{" "}
                  {highlightedText.after}
                </p>
              ) : (
                <p className="whitespace-pre-wrap">{documentText || "No content recorded at this point yet."}</p>
              )}
            </div>
          </div>

          {/* Event details */}
          <div className="col-span-3 bg-slate-900 border border-slate-800 rounded-xl p-4 max-h-[70vh] overflow-y-auto">
            <h3 className="text-xs uppercase text-slate-500 mb-3 tracking-wide">Event Details</h3>
            {selectedEvent ? (
              <div className="space-y-3 text-sm">
                <p className="font-medium">{eventLabel(selectedEvent.event_type)}</p>
                <DetailRow label="Time" value={new Date(selectedEvent.timestamp).toLocaleString()} />
                <DetailRow label="Words affected" value={selectedEvent.words_affected} />
                <DetailRow label="Characters" value={selectedEvent.characters_affected} />
                <DetailRow label="Confidence" value={selectedEvent.classification_confidence} />
                <p className="text-xs text-slate-500 pt-2 border-t border-slate-800">
                  Confidence reflects certainty in the event classification only — not a judgment about intent
                  or academic misconduct.
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Select an event from the timeline.</p>
            )}

            {mlSignals.length > 0 && (
              <div className="mt-6 pt-4 border-t border-slate-800 space-y-2">
                <h4 className="text-xs uppercase text-slate-500 tracking-wide flex items-center gap-1">
                  <FileWarning className="w-3.5 h-3.5" /> Forensic Indicators
                </h4>
                {mlSignals.map((s, i) => (
                  <div key={i} className="text-xs bg-slate-800/60 rounded-md p-2">
                    <p className="text-amber-300 font-medium">{eventLabel(s.type)} ({s.severity})</p>
                    <p className="text-slate-400 mt-0.5">{s.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Word count trajectory */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <h3 className="text-xs uppercase text-slate-500 mb-3 tracking-wide">Word Count Trajectory</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", fontSize: 12 }} />
              <Line type="monotone" dataKey="words" stroke="#818cf8" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <p className="text-xs text-slate-600 text-center pb-4">
          These indicators describe observed document activity and system-generated anomalies.
          They are not, by themselves, proof of academic misconduct.
        </p>
      </div>
    </DashboardLayout>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold mt-1">{value}</p>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-500 text-xs">{label}</span>
      <span>{value}</span>
    </div>
  );
}
