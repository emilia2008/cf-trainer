import { useMemo, useState } from "react";
import { formatNumber, formatPercent } from "../format.js";
import Section from "./Section.jsx";
import { Empty } from "./States.jsx";

const COLUMNS = [
  { key: "tag", label: "Topic", numeric: false },
  { key: "solved", label: "Solved", numeric: true },
  { key: "attempted", label: "Attempted", numeric: true },
  { key: "first_try_rate", label: "First-try AC", numeric: true },
  { key: "max_solved_rating", label: "Hardest solved", numeric: true },
];
const COLLAPSED_ROWS = 12;

function compare(a, b, key, direction) {
  const x = a[key];
  const y = b[key];
  if (x == null && y == null) return a.tag.localeCompare(b.tag);
  if (x == null) return 1; // empty values always last
  if (y == null) return -1;
  const order = typeof x === "string" ? x.localeCompare(y) : x - y;
  return (direction === "asc" ? order : -order) || a.tag.localeCompare(b.tag);
}

export default function TopicTable({ topics, weakTags }) {
  const [sort, setSort] = useState({ key: "solved", direction: "desc" });
  const [showAll, setShowAll] = useState(false);
  const weak = useMemo(() => new Set(weakTags), [weakTags]);

  const sorted = useMemo(
    () => [...topics].sort((a, b) => compare(a, b, sort.key, sort.direction)),
    [topics, sort],
  );
  const visible = showAll ? sorted : sorted.slice(0, COLLAPSED_ROWS);

  function sortBy(column) {
    setSort((current) =>
      current.key === column.key
        ? { key: column.key, direction: current.direction === "asc" ? "desc" : "asc" }
        : { key: column.key, direction: column.numeric ? "desc" : "asc" },
    );
  }

  return (
    <Section
      id="topics"
      title="Topics"
      subtitle="Every tag you have tried. First-try AC is the share of solved problems accepted on the first submission."
      className="span-12"
    >
      {topics.length === 0 ? (
        <Empty>No submissions yet, so there are no topics to show.</Empty>
      ) : (
        <>
          <div className="table-scroll">
            <table className="topic-table">
              <thead>
                <tr>
                  {COLUMNS.map((column) => {
                    const active = sort.key === column.key;
                    return (
                      <th
                        key={column.key}
                        scope="col"
                        className={column.numeric ? "num" : ""}
                        aria-sort={active ? (sort.direction === "asc" ? "ascending" : "descending") : "none"}
                      >
                        <button type="button" className="sort-button" onClick={() => sortBy(column)}>
                          {column.label}
                          <span className="sort-indicator" aria-hidden="true">
                            {active ? (sort.direction === "asc" ? "▲" : "▼") : ""}
                          </span>
                        </button>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {visible.map((topic) => (
                  <tr key={topic.tag}>
                    <th scope="row">
                      {topic.tag}
                      {weak.has(topic.tag) && <span className="badge">weak</span>}
                    </th>
                    <td className="num">{formatNumber(topic.solved)}</td>
                    <td className="num">{formatNumber(topic.attempted)}</td>
                    <td className="num">{topic.solved ? formatPercent(topic.first_try_rate) : "—"}</td>
                    <td className="num">{formatNumber(topic.max_solved_rating)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {sorted.length > COLLAPSED_ROWS && (
            <button type="button" className="link-button" onClick={() => setShowAll((v) => !v)}>
              {showAll ? "Show fewer topics" : `Show all ${sorted.length} topics`}
            </button>
          )}
        </>
      )}
    </Section>
  );
}
