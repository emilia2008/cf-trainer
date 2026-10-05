import ProblemList from "./ProblemList.jsx";
import Section from "./Section.jsx";
import { Empty } from "./States.jsx";

function emptyMessage(range, hasWeakTopics, problemsInRange) {
  if (problemsInRange === 0) {
    return `Codeforces has no rated problems in your target range (${range.lo}–${range.hi}) yet.`;
  }
  if (!hasWeakTopics) return "No weak topics at this level, so there is nothing specific to recommend.";
  return "You have solved every problem in this range that trains your weak topics.";
}

export default function Recommendations({ problems, range, hasWeakTopics, problemsInRange }) {
  const highlight = [...new Set(problems.flatMap((p) => p.matched_tags))];
  return (
    <Section
      id="recommendations"
      title="Practise next"
      subtitle={`Unsolved problems rated ${range.lo}–${range.hi} that train your weak topics`}
      className="span-5"
    >
      {problems.length === 0 ? (
        <Empty>{emptyMessage(range, hasWeakTopics, problemsInRange)}</Empty>
      ) : (
        <ProblemList problems={problems} highlightTags={highlight} />
      )}
    </Section>
  );
}
