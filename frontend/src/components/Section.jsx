export default function Section({ id, title, subtitle, className = "", actions, children }) {
  return (
    <section id={id} className={`card ${className}`} aria-labelledby={`${id}-title`}>
      <header className="card-header">
        <div>
          <h2 id={`${id}-title`}>{title}</h2>
          {subtitle && <p className="card-subtitle">{subtitle}</p>}
        </div>
        {actions}
      </header>
      {children}
    </section>
  );
}
