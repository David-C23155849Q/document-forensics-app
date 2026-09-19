import { useEffect, useState } from "react";
import {
  currentUser,
  endSession,
  fetchMyAssignments,
  isAuthenticated,
  login,
  startSession,
  startSubmission,
  submitAssignment,
} from "./services/api";
import { DEFAULT_CONFIG, DocumentMonitor } from "./services/documentMonitor";
import { NetworkStatus, SyncService } from "./services/syncService";

type Screen = "login" | "assignments" | "consent" | "writing";

export default function App() {
  const [screen, setScreen] = useState<Screen>(isAuthenticated() ? "assignments" : "login");
  const [assignments, setAssignments] = useState<any[]>([]);
  const [selectedAssignment, setSelectedAssignment] = useState<any | null>(null);
  const [submission, setSubmission] = useState<any | null>(null);
  const [session, setSession] = useState<any | null>(null);
  const [status, setStatus] = useState<NetworkStatus>("connected");
  const [words, setWords] = useState(0);
  const [queueSize, setQueueSize] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (screen === "assignments") {
      fetchMyAssignments().then(setAssignments).catch(() => setError("Could not load assignments."));
    }
  }, [screen]);

  useEffect(() => {
    if (screen !== "writing" || !submission || !session) return;
    const monitor = new DocumentMonitor(submission.id, session.id, DEFAULT_CONFIG, (state) => {
      setWords(state.wordCount);
      setQueueSize(state.queueSize);
    });
    const sync = new SyncService(submission.id, DEFAULT_CONFIG.snapshotIntervalMs * 10, setStatus);
    monitor.start();
    sync.start();
    return () => {
      monitor.stop();
      sync.stop();
    };
  }, [screen, submission, session]);

  async function handleLogin(username: string, password: string) {
    try {
      await login(username, password);
      setScreen("assignments");
    } catch {
      setError("Login failed. Check your credentials or backend connection.");
    }
  }

  async function handleOpenAssignment(assignment: any) {
    setSelectedAssignment(assignment);
    setScreen("consent");
  }

  async function handleStartWriting() {
    if (!selectedAssignment) return;
    const sub = await startSubmission(selectedAssignment.id);
    const sess = await startSession(sub.id);
    setSubmission(sub);
    setSession(sess);
    setScreen("writing");
  }

  async function handleSubmit() {
    if (!submission || !session) return;
    
    // Optional: If you want a confirmation, you can use a React state variable instead of window.confirm.
    // For now, we execute the submission flow directly:
    try {
      await new SyncService(submission.id, 1000, setStatus).flush();
      await endSession(session.id, 0, 0);
      await submitAssignment(submission.id);
      setScreen("assignments");
    } catch (err) {
      setError("Failed to submit assignment.");
    }
  }

  return (
    <div style={styles.container}>
      {error && <p style={styles.error}>{error}</p>}
      {screen === "login" && <LoginScreen onLogin={handleLogin} />}
      {screen === "assignments" && (
        <AssignmentListScreen assignments={assignments} onOpen={handleOpenAssignment} user={currentUser()} />
      )}
      {screen === "consent" && (
        <ConsentScreen assignment={selectedAssignment} onContinue={handleStartWriting} onBack={() => setScreen("assignments")} />
      )}
      {screen === "writing" && (
        <WritingScreen
          assignment={selectedAssignment}
          status={status}
          words={words}
          queueSize={queueSize}
          onSubmit={handleSubmit}
        />
      )}
    </div>
  );
}

function LoginScreen({ onLogin }: { onLogin: (u: string, p: string) => void }) {
  const [username, setUsername] = useState("student1");
  const [password, setPassword] = useState("password123");
  return (
    <div>
      <h2 style={styles.h2}>Word Forensics</h2>
      <input style={styles.input} value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
      <input
        style={styles.input}
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <button style={styles.button} onClick={() => onLogin(username, password)}>
        Login
      </button>
      <button style={styles.linkButton}>Forgot password</button>
    </div>
  );
}

function AssignmentListScreen({ assignments, onOpen, user }: { assignments: any[]; onOpen: (a: any) => void; user: any }) {
  return (
    <div>
      <h2 style={styles.h2}>My Assignments</h2>
      <p style={styles.muted}>{user?.first_name || user?.username}</p>
      {assignments.map((a) => (
        <div key={a.id} style={styles.card}>
          <p style={{ fontWeight: 600 }}>{a.title}</p>
          <p style={styles.muted}>{a.course}</p>
          <p style={styles.muted}>Deadline: {new Date(a.deadline).toLocaleDateString()}</p>
          <p style={styles.muted}>Status: {a.status}</p>
          <button style={styles.button} onClick={() => onOpen(a)}>
            Open Assignment
          </button>
        </div>
      ))}
      {assignments.length === 0 && <p style={styles.muted}>No assignments available.</p>}
    </div>
  );
}

function ConsentScreen({ assignment, onContinue, onBack }: { assignment: any; onContinue: () => void; onBack: () => void }) {
  return (
    <div>
      <h2 style={styles.h2}>{assignment?.title}</h2>
      <p style={styles.consentText}>
        The Word Forensics System records document activity associated with this assignment, including document
        changes, timestamps, writing sessions, and document snapshots where applicable. It does not monitor
        unrelated applications or general computer activity.
      </p>
      <button style={styles.button} onClick={onContinue}>
        Continue
      </button>
      <button style={styles.linkButton} onClick={onBack}>
        Back
      </button>
    </div>
  );
}

function WritingScreen({
  assignment,
  status,
  words,
  queueSize,
  onSubmit,
}: {
  assignment: any;
  status: NetworkStatus;
  words: number;
  queueSize: number;
  onSubmit: () => void;
}) {
  const statusLabel: Record<NetworkStatus, string> = {
    connected: "Connected",
    synchronizing: "Synchronizing...",
    offline: "Offline — activity is being stored securely and will synchronize when connection is restored.",
    sync_failed: "Sync failed — will retry automatically.",
    sync_complete: "Synced",
  };
  return (
    <div>
      <h2 style={styles.h2}>{assignment?.title}</h2>
      <div style={styles.card}>
        <Row label="Connection" value={navigator.onLine ? "Connected" : "Offline"} />
        <Row label="Synchronization" value={statusLabel[status]} />
        <Row label="Words" value={String(words)} />
        <Row label="Pending sync items" value={String(queueSize)} />
      </div>
      <button style={{ ...styles.button, background: "#b91c1c" }} onClick={onSubmit}>
        Submit Assignment
      </button>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "4px 0" }}>
      <span style={styles.muted}>{label}</span>
      <span>{value}</span>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { fontFamily: "Segoe UI, sans-serif", padding: 16, fontSize: 13, color: "#1a1a1a" },
  h2: { fontSize: 16, marginBottom: 8 },
  input: { display: "block", width: "100%", padding: 8, marginBottom: 8, border: "1px solid #ccc", borderRadius: 4 },
  button: {
    display: "block",
    width: "100%",
    padding: 10,
    background: "#4f46e5",
    color: "white",
    border: "none",
    borderRadius: 4,
    marginTop: 8,
    cursor: "pointer",
  },
  linkButton: { background: "none", border: "none", color: "#4f46e5", marginTop: 8, cursor: "pointer" },
  card: { border: "1px solid #e2e2e2", borderRadius: 6, padding: 12, marginBottom: 10 },
  muted: { color: "#666", fontSize: 12 },
  consentText: { fontSize: 12, lineHeight: 1.5, color: "#333", marginBottom: 12 },
  error: { color: "#b91c1c", fontSize: 12 },
};
