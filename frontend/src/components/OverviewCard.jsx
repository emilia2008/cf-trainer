import { formatNumber, rankColor, rankFor } from "../format.js";
import Section from "./Section.jsx";

export function Tile({ label, value, note, style }) {
  return (
    <div className="tile" style={style}>
      <dt className="tile-label">{label}</dt>
      <dd className="tile-value">{value}</dd>
      {note && <dd className="tile-note">{note}</dd>}
    </div>
  );
}

export default function OverviewCard({ overview }) {
  const rating = overview.rating ?? 0;
  const bandStart = rankFor(rating).min;
  const next = overview.next_threshold;
  const progress = next == null ? 1 : (rating - bandStart) / (next - bandStart);

  return (
    <Section id="overview" title="Overview" className="span-12">
      <div className="overview">
        <div className="rank-block" style={{ "--rank-color": rankColor(overview.rank) }}>
          <span className="rank-swatch" aria-hidden="true" />
          <div>
            <p className="tile-label">Current rank</p>
            <p className="rank-title">{overview.rank}</p>
            {overview.rating == null && <p className="muted small">Unrated: no rated contests yet</p>}
          </div>
        </div>

        <dl className="tiles">
          <Tile label="Rating" value={overview.rating == null ? "Unrated" : formatNumber(overview.rating)} />
          <Tile
            label="Max rating"
            value={formatNumber(overview.max_rating)}
            note={overview.max_rating == null ? null : overview.max_rank}
          />
          <Tile label="Problems solved" value={formatNumber(overview.solved_count)} note="distinct problems" />
          <Tile label="Rated contests" value={formatNumber(overview.contests)} />
        </dl>
      </div>

      <div className="next-rank" style={{ "--rank-color": rankColor(overview.next_rank ?? overview.rank) }}>
        {overview.next_rank ? (
          <>
            <p>
              <strong>{formatNumber(overview.points_to_next)}</strong> points to{" "}
              <span className="rank-inline">
                <span className="rank-swatch small" aria-hidden="true" />
                {overview.next_rank}
              </span>{" "}
              <span className="muted">({formatNumber(next)})</span>
            </p>
            <div
              className="meter"
              role="progressbar"
              aria-label={`Progress from ${formatNumber(bandStart)} to ${formatNumber(next)}`}
              aria-valuemin={bandStart}
              aria-valuemax={next}
              aria-valuenow={rating}
            >
              <span style={{ width: `${Math.max(0, Math.min(1, progress)) * 100}%` }} />
            </div>
          </>
        ) : (
          <p>Top rank reached. There is no higher title on Codeforces.</p>
        )}
      </div>
    </Section>
  );
}
