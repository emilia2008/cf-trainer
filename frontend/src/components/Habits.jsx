import { useState } from "react";
import { formatNumber, formatPercent } from "../format.js";
import Section from "./Section.jsx";
import { Empty } from "./States.jsx";
import { Tile } from "./OverviewCard.jsx";

function BarRow({ label, share, value }) {
  return (
    <div className="bar-row">
      <span className="bar-label">{label}</span>
      <span className="bar-track" aria-hidden="true">
        <span className="bar-fill" style={{ width: `${Math.min(1, share) * 100}%` }} />
      </span>
      <span className="bar-value">{value}</span>
    </div>
  );
}

// ICPC-style rounds have problems up to M or later; show the usual Div. 1/2 range first.
const LETTERS_SHOWN = 8;
// Verdicts arrive most frequent first; the long tail is mostly under 1%.
const VERDICTS_SHOWN = 5;

export default function Habits({ habits }) {
  const [showAllLetters, setShowAllLetters] = useState(false);
  const [showAllVerdicts, setShowAllVerdicts] = useState(false);
  const acceptance = habits.total_submissions ? habits.accepted / habits.total_submissions : null;
  const visibleLetters = showAllLetters
    ? habits.contest_level
    : habits.contest_level.slice(0, LETTERS_SHOWN);
  const visibleVerdicts = showAllVerdicts ? habits.verdicts : habits.verdicts.slice(0, VERDICTS_SHOWN);

  return (
    <Section
      id="habits"
      title="Habits"
      subtitle="How your submissions end, and how far you get in live contests"
      className="span-7"
    >
      <dl className="tiles compact-tiles">
        <Tile label="Submissions" value={formatNumber(habits.total_submissions)} />
        <Tile
          label="Accepted"
          value={formatPercent(acceptance)}
          note={`${formatNumber(habits.accepted)} of ${formatNumber(habits.total_submissions)}`}
        />
        <Tile label="First-try AC" value={formatPercent(habits.first_try_rate)} note="of solved problems" />
      </dl>

      <h3 className="subheading">Why submissions fail</h3>
      {habits.verdicts.length === 0 ? (
        <Empty>No failed submissions. Impressive.</Empty>
      ) : (
        <>
          <ul className="bar-list">
            {visibleVerdicts.map((v) => (
              <li key={v.verdict}>
                <BarRow
                  label={v.label}
                  share={v.share}
                  value={
                    <>
                      {formatPercent(v.share)} <span className="muted">({formatNumber(v.count)})</span>
                    </>
                  }
                />
                {v.advice && <p className="advice">{v.advice}</p>}
              </li>
            ))}
          </ul>
          {habits.verdicts.length > VERDICTS_SHOWN && (
            <button type="button" className="link-button" onClick={() => setShowAllVerdicts((v) => !v)}>
              {showAllVerdicts ? "Show fewer verdicts" : `Show all ${habits.verdicts.length} verdicts`}
            </button>
          )}
        </>
      )}

      <h3 className="subheading">In live contests</h3>
      {habits.live_contests === 0 ? (
        <Empty>No live contest participation yet.</Empty>
      ) : (
        <>
          <p className="headline">
            {habits.usually_solves_up_to ? (
              <>
                You usually solve up to problem <strong>{habits.usually_solves_up_to}</strong>
              </>
            ) : (
              "You solve problem A in fewer than half of your live contests"
            )}
            <span className="muted"> · {formatNumber(habits.live_contests)} contests</span>
          </p>
          <p className="muted small">
            Share of your live contests in which you solved a problem with each letter.
          </p>
          {habits.contest_level.length === 0 ? (
            <Empty>No problems solved during a live contest yet.</Empty>
          ) : (
            <>
              <ul className="bar-list letters">
                {visibleLetters.map((level) => (
                  <li key={level.letter}>
                    <BarRow label={level.letter} share={level.rate} value={formatPercent(level.rate)} />
                  </li>
                ))}
              </ul>
              {habits.contest_level.length > LETTERS_SHOWN && (
                <button type="button" className="link-button" onClick={() => setShowAllLetters((v) => !v)}>
                  {showAllLetters
                    ? "Show fewer letters"
                    : `Show all ${habits.contest_level.length} letters`}
                </button>
              )}
            </>
          )}
        </>
      )}
    </Section>
  );
}
