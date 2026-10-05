import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { RANKS, formatDate, formatMonthYear, formatNumber, formatSigned } from "../format.js";
import Section from "./Section.jsx";
import { Empty } from "./States.jsx";
import { Tile } from "./OverviewCard.jsx";

const AXIS_TICK = { fill: "var(--muted)", fontSize: 12 };

function yDomain(points) {
  const values = points.map((p) => p.rating);
  const lo = Math.max(0, Math.floor((Math.min(...values) - 100) / 100) * 100);
  const hi = Math.ceil((Math.max(...values) + 100) / 100) * 100;
  return [lo, hi];
}

// Rank colour bands behind the line, like the chart on a Codeforces profile.
function rankBands([lo, hi]) {
  return RANKS.map((rank, i) => ({
    ...rank,
    from: Math.max(rank.min, lo),
    to: Math.min(RANKS[i + 1]?.min ?? Infinity, hi),
  })).filter((band) => band.from < band.to);
}

function timeTicks(points, count = 5) {
  const first = points[0].time;
  const last = points[points.length - 1].time;
  if (first === last) return [first];
  return Array.from({ length: count }, (_, i) => first + ((last - first) * i) / (count - 1));
}

function RatingTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-value">
        {formatNumber(point.rating)}{" "}
        <span className={point.delta >= 0 ? "delta-up" : "delta-down"}>{formatSigned(point.delta)}</span>
      </p>
      <p className="tooltip-label">{point.name}</p>
      <p className="tooltip-meta">
        {formatDate(point.time / 1000)} · place {formatNumber(point.rank)}
      </p>
    </div>
  );
}

function Delta({ value }) {
  if (value == null) return "—";
  return <span className={value >= 0 ? "delta-up" : "delta-down"}>{formatSigned(value)}</span>;
}

export default function RatingChart({ trend }) {
  const points = trend.history.map((c) => ({
    time: c.time * 1000,
    rating: c.new_rating,
    delta: c.delta,
    name: c.contest_name,
    rank: c.rank,
  }));
  const hasDrop = trend.worst_drop != null && trend.worst_drop < 0;

  return (
    <Section
      id="rating"
      title="Rating trend"
      subtitle="Rating after every rated contest"
      className="span-12"
    >
      {points.length === 0 ? (
        <Empty>No rated contests yet. Take part in a rated round to start a rating history.</Empty>
      ) : (
        <>
          <dl className="tiles compact-tiles">
            <Tile
              label={`Last ${trend.recent_window} contest${trend.recent_window === 1 ? "" : "s"}`}
              value={<Delta value={trend.recent_change} />}
            />
            <Tile label="Best gain" value={<Delta value={trend.best_gain} />} />
            <Tile label="Worst drop" value={hasDrop ? <Delta value={trend.worst_drop} /> : "No drops yet"} />
            <Tile label="Peak" value={formatNumber(trend.max_rating)} />
          </dl>

          <div className="chart" role="img" aria-label={`Rating history over ${points.length} contests`}>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={points} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
                {rankBands(yDomain(points)).map((band) => (
                  <ReferenceArea
                    key={band.title}
                    y1={band.from}
                    y2={band.to}
                    fill={`var(--rank-${band.color})`}
                    fillOpacity={0.1}
                    stroke="none"
                    ifOverflow="hidden"
                  />
                ))}
                <CartesianGrid stroke="var(--grid)" vertical={false} />
                <XAxis
                  dataKey="time"
                  type="number"
                  scale="time"
                  domain={["dataMin", "dataMax"]}
                  ticks={timeTicks(points)}
                  tickFormatter={formatMonthYear}
                  tick={AXIS_TICK}
                  stroke="var(--axis)"
                  tickLine={false}
                  minTickGap={24}
                />
                <YAxis
                  domain={yDomain(points)}
                  tick={AXIS_TICK}
                  stroke="var(--axis)"
                  tickLine={false}
                  axisLine={false}
                  width={48}
                  allowDecimals={false}
                />
                <Tooltip
                  content={<RatingTooltip />}
                  cursor={{ stroke: "var(--axis)", strokeWidth: 1 }}
                />
                <Line
                  type="linear"
                  dataKey="rating"
                  stroke="var(--series-1)"
                  strokeWidth={2}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  dot={points.length <= 30 ? { r: 3, fill: "var(--series-1)", strokeWidth: 0 } : false}
                  activeDot={{ r: 5, fill: "var(--series-1)", stroke: "var(--surface)", strokeWidth: 2 }}
                  isAnimationActive={false}
                />
                <ReferenceDot
                  x={points[points.length - 1].time}
                  y={points[points.length - 1].rating}
                  r={5}
                  fill="var(--series-1)"
                  stroke="var(--surface)"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <details className="data-table">
            <summary>Show contest table</summary>
            <div className="table-scroll tall">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Date</th>
                    <th scope="col">Contest</th>
                    <th scope="col" className="num">Place</th>
                    <th scope="col" className="num">Change</th>
                    <th scope="col" className="num">Rating</th>
                  </tr>
                </thead>
                <tbody>
                  {[...trend.history].reverse().map((c) => (
                    <tr key={`${c.contest_id}-${c.time}`}>
                      <td className="nowrap">{formatDate(c.time)}</td>
                      <td>{c.contest_name}</td>
                      <td className="num">{formatNumber(c.rank)}</td>
                      <td className="num">
                        <Delta value={c.delta} />
                      </td>
                      <td className="num">{formatNumber(c.new_rating)}</td>
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
