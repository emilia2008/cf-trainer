const EXAMPLES = ["tourist", "jiangly", "Benq"];

const SECTIONS = [
  ["Overview", "Rank, rating and the points you need for the next rank"],
  ["Rating trend", "Your rating history, recent momentum, best gain and worst drop"],
  ["Difficulty", "Solves per problem rating, your comfort level and target range"],
  ["Weak topics", "Tags common at your next level that you rarely solve, with study links"],
  ["Habits", "Verdict mix with advice, and how far you usually get in live contests"],
  ["Practice", "Upsolve list and 10 unsolved problems picked for your weak topics"],
];

export function Welcome({ onPick }) {
  return (
    <section className="welcome">
      <h1>Find out what is holding your Codeforces rating back</h1>
      <p className="lead">
        Enter a handle to get a deep analysis of one account: where you stand, which topics to
        study, and exactly which problems to practise next.
      </p>
      <p className="examples">
        Try:{" "}
        {EXAMPLES.map((handle) => (
          <button key={handle} type="button" className="chip-button" onClick={() => onPick(handle)}>
            {handle}
          </button>
        ))}
      </p>
      <ul className="feature-list">
        {SECTIONS.map(([title, text]) => (
          <li key={title}>
            <strong>{title}</strong>
            <span>{text}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

const STEPS = [
  ["sync", "Fetching profile, rating history and submissions from Codeforces"],
  ["report", "Analysing topics, difficulty and habits"],
];

export function LoadingState({ step }) {
  const current = STEPS.findIndex(([key]) => key === step);
  return (
    <div className="status-panel" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <div>
        <ol className="steps">
          {STEPS.map(([key, text], i) => (
            <li key={key} className={i < current ? "done" : i === current ? "active" : ""}>
              {text}
            </li>
          ))}
        </ol>
        <p className="muted small">
          Codeforces allows one API call every two seconds, so the first analysis takes about
          10 seconds.
        </p>
      </div>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="status-panel error" role="alert">
      <div>
        <p className="status-title">Could not build the report</p>
        <p>{message}</p>
      </div>
      <button type="button" className="secondary-button" onClick={onRetry}>
        Try again
      </button>
    </div>
  );
}

export function Empty({ children }) {
  return <p className="empty">{children}</p>;
}
