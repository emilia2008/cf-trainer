import { formatPercent } from "../format.js";
import Section from "./Section.jsx";
import { Empty } from "./States.jsx";

export default function WeakTopics({ topics, range, problemsInRange }) {
  return (
    <Section
      id="weak-topics"
      title="Weak topics: what to study"
      subtitle={`Tags common at ${range.lo}–${range.hi} that you have rarely solved there`}
      className="span-7"
    >
      {topics.length === 0 ? (
        <Empty>
          {problemsInRange === 0
            ? `Codeforces has no rated problems in your target range (${range.lo}–${range.hi}) yet: you are past the top of the problem rating scale.`
            : "No weak topics: you have solved problems with every common tag at this level."}
        </Empty>
      ) : (
        <ol className="weak-list">
          {topics.map((topic, i) => (
            <li key={topic.tag} className="weak-item">
              <div className="weak-head">
                <span className="weak-rank" aria-hidden="true">{i + 1}</span>
                <h3>{topic.tag}</h3>
                <span className="weak-share">in {formatPercent(topic.importance)} of problems</span>
              </div>
              <div className="meter thin" aria-hidden="true">
                <span style={{ width: `${Math.min(1, topic.importance) * 100}%` }} />
              </div>
              <p className="weak-reason">{topic.reason}</p>
              <ul className="resource-list" aria-label={`Study resources for ${topic.tag}`}>
                {topic.resources.map((resource) => (
                  <li key={resource.title}>
                    <a href={resource.url} target="_blank" rel="noreferrer">
                      {resource.title}
                    </a>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      )}
    </Section>
  );
}
