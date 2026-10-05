import { formatCompact, problemCode, rankColor, rankFor } from "../format.js";

export default function ProblemList({ problems, highlightTags = [] }) {
  const highlight = new Set(highlightTags);
  return (
    <ol className="problem-list">
      {problems.map((problem) => (
        <li key={problemCode(problem)} className="problem">
          <div className="problem-main">
            <a className="problem-name" href={problem.url} target="_blank" rel="noreferrer">
              {problem.name ?? problemCode(problem)}
            </a>
            <span className="problem-code">{problemCode(problem)}</span>
          </div>
          <div className="problem-meta">
            {problem.rating != null ? (
              <span
                className="rating-badge"
                style={{ "--rank-color": rankColor(rankFor(problem.rating).title) }}
              >
                {problem.rating}
              </span>
            ) : (
              <span className="rating-badge unrated">unrated</span>
            )}
            {problem.solved_count != null && (
              <span className="muted small">{formatCompact(problem.solved_count)} solved</span>
            )}
          </div>
          {problem.tags.length > 0 && (
            <ul className="tags" aria-label="Tags">
              {problem.tags.map((tag) => (
                <li key={tag} className={highlight.has(tag) ? "tag highlight" : "tag"}>
                  {tag}
                </li>
              ))}
            </ul>
          )}
        </li>
      ))}
    </ol>
  );
}
