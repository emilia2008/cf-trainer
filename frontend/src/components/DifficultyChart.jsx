import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatNumber } from "../format.js";
import Section from "./Section.jsx";
import { Empty } from "./States.jsx";
import { Tile } from "./OverviewCard.jsx";

const AXIS_TICK = { fill: "var(--muted)", fontSize: 12 };

// One row per 100 rating points from the easiest bucket to the end of the target range,
// so the target range is drawn even where the user has not tried anything yet.
function rows(buckets, lo, hi) {
  const byRating = new Map(buckets.map((b) => [b.rating, b]));
  const ratings = buckets.map((b) => b.rating);
  const start = Math.min(...ratings, lo);
  const end = Math.max(...ratings, hi);
  const result = [];
  for (let rating = start; rating <= end; rating += 100) {
    const bucket = byRating.get(rating) ?? { solved: 0, attempted: 0 };
    result.push({
      rating,
      solved: bucket.solved,
      unsolved: bucket.attempted - bucket.solved,
      attempted: bucket.attempted,
      inTarget: rating >= lo && rating <= hi,
    });
  }
  return result;
}

// Whole-number ticks on a clean step (1, 2, 5, 10, 20, 25, 50, ...), at most 5 intervals.
function countTicks(rows) {
  const max = Math.max(1, ...rows.map((r) => r.attempted));
  const steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000];
  const step = steps.find((s) => max / s <= 5) ?? Math.ceil(max / 5);
  const ticks = [];
  for (let t = 0; t < max + step; t += step) ticks.push(t);
  return ticks;
}

function DifficultyTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">
        Rated {row.rating}
        {row.inTarget ? " · target range" : ""}
      </p>
      <p className="tooltip-row">
        <span className="key-line" style={{ background: "var(--series-1)" }} />
        <strong>{row.solved}</strong> solved
      </p>
      <p className="tooltip-row">
        <span className="key-line" style={{ background: "var(--series-2)" }} />
        <strong>{row.unsolved}</strong> tried, not solved
      </p>
    </div>
  );
}

export default function DifficultyChart({ difficulty }) {
  const { buckets, comfort_rating: comfort, target_range: range } = difficulty;
  const data = buckets.length ? rows(buckets, range.lo, range.hi) : [];
  const yTicks = countTicks(data);

  return (
    <Section
      id="difficulty"
      title="Difficulty"
      subtitle="Distinct problems per problem rating"
      className="span-12"
    >
      <dl className="tiles compact-tiles">
        <Tile
          label="Comfort level"
          value={comfort == null ? "Not yet" : formatNumber(comfort)}
          note="highest rating with 3+ solves"
        />
        <Tile
          label="Target range"
          value={`${range.lo}–${range.hi}`}
          note="practise here to improve"
        />
        <Tile
          label="Problems in range"
          value={formatNumber(difficulty.problems_in_range)}
          note="on Codeforces"
        />
      </dl>

      {data.length === 0 ? (
        <Empty>No attempts on rated problems yet. Start with problems rated {range.lo}.</Empty>
      ) : (
        <>
          <ul className="legend" aria-label="Legend">
            <li><span className="swatch" style={{ background: "var(--series-1)" }} />Solved</li>
            <li><span className="swatch" style={{ background: "var(--series-2)" }} />Tried, not solved</li>
            <li><span className="swatch target" />Target range</li>
          </ul>
          <div className="chart" role="img" aria-label="Solved and attempted problems per rating">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data} margin={{ top: 20, right: 12, bottom: 0, left: 0 }} barCategoryGap="20%">
                <ReferenceArea
                  x1={range.lo}
                  x2={range.hi}
                  fill="var(--target-wash)"
                  stroke="none"
                  ifOverflow="extendDomain"
                  label={{ value: "Target", position: "insideTop", fill: "var(--text-2)", fontSize: 12 }}
                />
                <CartesianGrid stroke="var(--grid)" vertical={false} />
                <XAxis
                  dataKey="rating"
                  tick={AXIS_TICK}
                  stroke="var(--axis)"
                  tickLine={false}
                  interval="preserveStartEnd"
                  minTickGap={12}
                />
                <YAxis
                  ticks={yTicks}
                  domain={[0, yTicks[yTicks.length - 1]]}
                  tick={AXIS_TICK}
                  stroke="var(--axis)"
                  tickLine={false}
                  axisLine={false}
                  allowDecimals={false}
                  width={40}
                />
                <Tooltip content={<DifficultyTooltip />} cursor={{ fill: "var(--hover-wash)" }} />
                <Bar
                  dataKey="solved"
                  stackId="problems"
                  fill="var(--series-1)"
                  stroke="var(--surface)"
                  strokeWidth={2}
                  maxBarSize={24}
                  isAnimationActive={false}
                />
                <Bar
                  dataKey="unsolved"
                  stackId="problems"
                  fill="var(--series-2)"
                  stroke="var(--surface)"
                  strokeWidth={2}
                  maxBarSize={24}
                  radius={[4, 4, 0, 0]}
                  isAnimationActive={false}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <details className="data-table">
            <summary>Show table</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Rating</th>
                    <th scope="col" className="num">Solved</th>
                    <th scope="col" className="num">Attempted</th>
                  </tr>
                </thead>
                <tbody>
                  {buckets.map((b) => (
                    <tr key={b.rating}>
                      <td>{b.rating}</td>
                      <td className="num">{b.solved}</td>
                      <td className="num">{b.attempted}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </>
      )}
    </Section>
  );
}
