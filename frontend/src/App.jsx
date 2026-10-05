import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, getReport, syncUser } from "./api.js";
import Report from "./components/Report.jsx";
import { ErrorState, LoadingState, Welcome } from "./components/States.jsx";
import ThemeToggle from "./components/ThemeToggle.jsx";

function handleFromUrl() {
  return new URLSearchParams(window.location.search).get("handle")?.trim() ?? "";
}

function setUrlHandle(handle) {
  const url = new URL(window.location.href);
  if (handle) url.searchParams.set("handle", handle);
  else url.searchParams.delete("handle");
  window.history.replaceState(null, "", url);
}

export default function App() {
  const [input, setInput] = useState(handleFromUrl);
  const [status, setStatus] = useState("idle"); // idle | loading | ready | error
  const [step, setStep] = useState(null); // sync | report
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [warning, setWarning] = useState(null);
  const latestRequest = useRef(0);

  const analyse = useCallback(async (rawHandle) => {
    const handle = rawHandle.trim();
    if (!handle) return;
    // Only the most recent request may update the page.
    const id = ++latestRequest.current;
    const isCurrent = () => id === latestRequest.current;

    setStatus("loading");
    setStep("sync");
    setError(null);
    setWarning(null);
    setUrlHandle(handle);

    let syncError = null;
    try {
      try {
        await syncUser(handle);
      } catch (e) {
        // Codeforces unreachable: fall back to the last stored copy if there is one.
        if (!(e instanceof ApiError && e.status === 502)) throw e;
        syncError = e;
      }
      if (!isCurrent()) return;
      setStep("report");
      let data;
      try {
        data = await getReport(handle);
      } catch (e) {
        throw syncError && e instanceof ApiError && e.status === 404 ? syncError : e;
      }
      if (!isCurrent()) return;
      if (syncError) {
        setWarning(`${syncError.message} Showing the data from the last successful sync.`);
      }
      setReport(data);
      setStatus("ready");
    } catch (e) {
      if (!isCurrent()) return;
      setReport(null);
      setError(e.message);
      setStatus("error");
    }
  }, []);

  // Open shared links like /?handle=tourist straight away (once, even under StrictMode).
  const autoStarted = useRef(false);
  useEffect(() => {
    if (autoStarted.current) return;
    autoStarted.current = true;
    const handle = handleFromUrl();
    if (handle) analyse(handle);
  }, [analyse]);

  function onSubmit(event) {
    event.preventDefault();
    analyse(input);
  }

  function pickExample(handle) {
    setInput(handle);
    analyse(handle);
  }

  function goHome(event) {
    event.preventDefault();
    latestRequest.current += 1;
    setInput("");
    setReport(null);
    setError(null);
    setWarning(null);
    setStatus("idle");
    setUrlHandle("");
  }

  const loading = status === "loading";

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <a className="brand" href="./" onClick={goHome}>
            <span className="brand-mark" aria-hidden="true">CF</span>
            <span>Trainer</span>
          </a>
          <form className="search" onSubmit={onSubmit} role="search">
            <label htmlFor="handle" className="visually-hidden">
              Codeforces handle
            </label>
            <input
              id="handle"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Codeforces handle"
              autoComplete="off"
              autoCapitalize="none"
              spellCheck="false"
              maxLength={64}
            />
            <button type="submit" disabled={loading || !input.trim()}>
              {loading ? "Analysing…" : "Analyse"}
            </button>
          </form>
          <ThemeToggle />
        </div>
      </header>

      <main className="container">
        {loading && <LoadingState step={step} />}
        {status === "error" && <ErrorState message={error} onRetry={() => analyse(input)} />}
        {warning && (
          <p className="notice" role="status">
            {warning}
          </p>
        )}
        {report && <Report report={report} dimmed={loading} />}
        {status === "idle" && !report && <Welcome onPick={pickExample} />}
      </main>

      <footer className="footer">
        Data from the public <a href="https://codeforces.com/apiHelp">Codeforces API</a>. Not
        affiliated with Codeforces.
      </footer>
    </div>
  );
}
