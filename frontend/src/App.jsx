import { useState } from "react";

// Starter page: enter a handle, register it, then show stats.
// TODO (LEARNING.md, section 5):
//   - show the tag stats as a table or bar chart
//   - show recommended problems as links to codeforces.com/problemset/problem/<contestId>/<index>
//   - add a Leaderboard page
//   - handle loading and error states

export default function App() {
  const [handle, setHandle] = useState("");
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  async function lookUp(event) {
    event.preventDefault();
    setError(null);
    try {
      const register = await fetch(`/api/users/${encodeURIComponent(handle)}`, { method: "POST" });
      if (!register.ok) throw new Error(`Register failed: ${register.status}`);
      const response = await fetch(`/api/users/${encodeURIComponent(handle)}/stats`);
      if (!response.ok) throw new Error(`Stats failed: ${response.status}`);
      setStats(await response.json());
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "2rem auto", fontFamily: "system-ui", padding: "0 1rem" }}>
      <h1>CF Trainer</h1>
      <form onSubmit={lookUp}>
        <input
          value={handle}
          onChange={(e) => setHandle(e.target.value)}
          placeholder="Codeforces handle"
        />
        <button type="submit">Analyse</button>
      </form>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {stats && <pre>{JSON.stringify(stats, null, 2)}</pre>}
    </main>
  );
}
