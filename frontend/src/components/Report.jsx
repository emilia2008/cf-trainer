import { formatDateTime, rankColor } from "../format.js";
import DifficultyChart from "./DifficultyChart.jsx";
import Habits from "./Habits.jsx";
import OverviewCard from "./OverviewCard.jsx";
import RatingChart from "./RatingChart.jsx";
import Recommendations from "./Recommendations.jsx";
import TopicTable from "./TopicTable.jsx";
import UpsolveList from "./UpsolveList.jsx";
import WeakTopics from "./WeakTopics.jsx";

const NAV = [
  ["overview", "Overview"],
  ["rating", "Rating"],
  ["difficulty", "Difficulty"],
  ["weak-topics", "Weak topics"],
  ["recommendations", "Practice"],
  ["habits", "Habits"],
  ["upsolve", "Upsolve"],
  ["topics", "Topics"],
];

export default function Report({ report, dimmed }) {
  const { overview, difficulty } = report;
  const weakTags = report.weak_topics.map((w) => w.tag);

  return (
    <article className={`report${dimmed ? " dimmed" : ""}`} aria-busy={dimmed}>
      <header className="report-header">
        <div>
          <h1 className="handle" style={{ "--rank-color": rankColor(overview.rank) }}>
            {report.handle}
          </h1>
          <p className="muted small">
            Last synced {formatDateTime(report.last_synced_at)} ·{" "}
            <a href={`https://codeforces.com/profile/${encodeURIComponent(report.handle)}`}>
              Codeforces profile
            </a>
          </p>
        </div>
      </header>

      <nav className="section-nav" aria-label="Report sections">
        {NAV.map(([id, label]) => (
          <a key={id} href={`#${id}`}>
            {label}
          </a>
        ))}
      </nav>

      <div className="grid">
        <OverviewCard overview={overview} />
        <RatingChart trend={report.rating_trend} />
        <DifficultyChart difficulty={difficulty} />
        <WeakTopics topics={report.weak_topics} range={difficulty.target_range}
                    problemsInRange={difficulty.problems_in_range} />
        <Recommendations problems={report.recommendations} range={difficulty.target_range}
                         hasWeakTopics={weakTags.length > 0}
                         problemsInRange={difficulty.problems_in_range} />
        <Habits habits={report.habits} />
        <UpsolveList upsolve={report.upsolve} />
        <TopicTable topics={report.topics} weakTags={weakTags} />
      </div>
    </article>
  );
}
