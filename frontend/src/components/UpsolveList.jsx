import ProblemList from "./ProblemList.jsx";
import Section from "./Section.jsx";
import { Empty } from "./States.jsx";

export default function UpsolveList({ upsolve }) {
  const shown = upsolve.problems.length;
  return (
    <Section
      id="upsolve"
      title="Upsolve"
      subtitle={
        upsolve.total > shown
          ? `Tried during a live contest but never accepted · easiest ${shown} of ${upsolve.total}`
          : "Tried during a live contest but never accepted"
      }
      className="span-5"
    >
      {shown === 0 ? (
        <Empty>Nothing to upsolve: every problem you tried in a live contest is accepted.</Empty>
      ) : (
        <ProblemList problems={upsolve.problems} />
      )}
    </Section>
  );
}
