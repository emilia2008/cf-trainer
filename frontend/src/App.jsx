import { useState } from "react";

// Starter page: enter a handle, sync it, then show the raw report JSON.
// TODO (BUILD_GUIDE.md, step 8): replace the JSON dump with real sections:
//   - Overview card: rank, rating, points to next rank
//   - Rating history line chart
//   - Difficulty bar chart (solved per rating) with the target range highlighted
//   - Topic table, weak topics with study links
//   - Habits: verdict breakdown with advice, "you usually solve up to problem C"
//   - Upsolve list and recommended problems (links to Codeforces)

export default function App() {
  const [handle, setHandle] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function analyse(event) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const h = encodeURIComponent(handle.trim());
      const sync = await fetch(`/api/users/${h}/sync`, { method: "POST" });
      if (!sync.ok) throw new Error(`Sync failed: ${sync.status}`);
      const response = await fetch(`/api/users/${h}/report`);
      if (!response.ok) throw new Error(`Report failed: ${response.status}`);
      setReport(await response.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 900, margin: "2rem auto", fontFamily: "system-ui", padding: "0 1rem" }}>
      <h1>CF Trainer</h1>
      <p>Deep analysis of a Codeforces account: where you are, what to fix, what to practise next.</p>
      <form onSubmit={analyse}>
        <input
          value={handle}
          onChange={(e) => setHandle(e.target.value)}
          placeholder="Codeforces handle"
        />
        <button type="submit" disabled={loading || !handle.trim()}>
          {loading ? "Analysing..." : "Analyse"}
        </button>
      </form>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {report && <pre>{JSON.stringify(report, null, 2)}</pre>}
    </main>
  );
}
