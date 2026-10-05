import ProblemList from "./ProblemList.jsx";
import Section from "./Section.jsx";
import { Empty } from "./States.jsx";

export default function Recommendations({ problems, range, hasWeakTopics }) {
  const highlight = [...new Set(problems.flatMap((p) => p.matched_tags))];
  return (
    <Section
      id="recommendations"
      title="Practise next"
      subtitle={`Unsolved problems rated ${range.lo}–${range.hi} that train your weak topics`}
      className="span-5"
    >
      {problems.length === 0 ? (
        <Empty>
          {hasWeakTopics
            ? "You have solved every problem in this range that trains your weak topics."
            : "No recommendations without weak topics to train."}
        </Empty>
      ) : (
        <ProblemList problems={problems} highlightTags={highlight} />
      )}
    </Section>
  );
}
