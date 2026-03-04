function StatCard({ title, value, hint, accent = "default" }) {
  return (
    <article className={`stat-card ${accent}`}>
      <p>{title}</p>
      <h3>{value}</h3>
      {hint ? <span>{hint}</span> : null}
    </article>
  );
}

export default StatCard;

