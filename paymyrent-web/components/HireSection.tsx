export function HireSection({ compact }: { compact?: boolean }) {
  return (
    <section className="hire-section" id="hire">
      <h2
        style={{
          fontFamily: "var(--font-mono)",
          color: "var(--neon-green)",
          letterSpacing: "0.12em",
          fontSize: "0.9rem",
        }}
      >
        HIRE THIS AGENT
      </h2>
      <p
        style={{
          color: "var(--muted)",
          maxWidth: 520,
          margin: "0 auto",
          fontSize: "0.85rem",
        }}
      >
        {compact
          ? "Connect exchange API keys and deploy the same Confluence Core engine on your account."
          : "Full self-serve deployment with risk confirmation and live execution."}
      </p>
      <div
        className="steps"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: "0.75rem",
          marginTop: "1rem",
          textAlign: "left",
        }}
      >
        {["PLAN", "CONNECT", "CONFIRM", "RUN"].map((label, i) => (
          <div
            key={label}
            style={{
              padding: "0.6rem",
              border: "1px solid var(--border)",
              background: "#0a0a0a",
            }}
          >
            <div style={{ color: "var(--neon-green)", fontWeight: 700 }}>
              {i + 1}
            </div>
            <strong style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
              {label}
            </strong>
          </div>
        ))}
      </div>
      <span className="hire-cta">COMING SOON</span>
    </section>
  );
}
