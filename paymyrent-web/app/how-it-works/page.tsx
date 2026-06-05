import Link from "next/link";

export default function HowItWorksPage() {
  return (
    <div className="terminal-shell">
      <header className="topbar">
        <Link href="/" className="logo">
          PAYMYRENT.AI
        </Link>
        <nav className="nav">
          <Link href="/">Dashboard</Link>
          <Link href="/signals">Signals</Link>
          <Link href="/hire">Hire agent</Link>
          <span style={{ color: "var(--accent)" }}>How it works</span>
        </nav>
      </header>
      <main className="main-cockpit section">
        <h1 style={{ fontSize: "1.75rem" }}>How the agent works</h1>

        <div className="panel" style={{ marginBottom: "1rem" }}>
          <h3>Confluence Core</h3>
          <p>
            Each closed bar, the agent scores up to seven independent signals
            (liquidity sweep, pools, CVD, order blocks, structure, trend,
            volume). Points sum into a <strong>confluence score</strong>. A
            direction (long/short) must be set from structure or liquidity
            context.
          </p>
        </div>

        <div className="panel" style={{ marginBottom: "1rem" }}>
          <h3>Entry gates</h3>
          <p>
            Even with a high score, the agent only enters when flat, equity is
            sufficient, entry spacing since the last trade is satisfied, and the
            bar is new. Optional filters can block exhausted CVD or liquidity
            voids.
          </p>
        </div>

        <div className="panel" style={{ marginBottom: "1rem" }}>
          <h3>Exits</h3>
          <p>
            No stop-loss. Exits are time- and return-based: target leveraged
            return before the hold window ends, minimum return at window end, or
            forced exit after the window.
          </p>
        </div>

        <div className="panel">
          <h3>Paper vs live</h3>
          <p style={{ color: "var(--muted)" }}>
            This site shows a <strong>paper forward test</strong> running on our
            infrastructure (simulated fills, real market data). It is research
            and transparency—not a promise of future returns. Hiring the agent
            for your exchange account is coming in a later release.
          </p>
          <p style={{ color: "var(--amber)", fontSize: "0.9rem" }}>
            Not financial advice. Trading with leverage is risky.
          </p>
        </div>

        <p style={{ marginTop: "2rem" }}>
          <Link href="/">← Back to live dashboard</Link>
        </p>
      </main>
    </div>
  );
}
