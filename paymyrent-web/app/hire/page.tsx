import Link from "next/link";
import { HireSection } from "@/components/HireSection";

export default function HirePage() {
  return (
    <div className="terminal-shell">
      <div className="disclaimer">
        <strong>PHASE 2</strong> — exchange connect not available yet
      </div>
      <header className="topbar">
        <Link href="/" className="logo">
          PAYMYRENT.AI
        </Link>
        <nav className="nav">
          <Link href="/">Dashboard</Link>
          <Link href="/signals">Signals</Link>
          <span style={{ color: "var(--lime)" }}>Hire agent</span>
        </nav>
      </header>
      <main className="main-cockpit">
        <HireSection />
        <section className="section panel">
          <h3>What you get when we launch</h3>
          <ul>
            <li>
              Same <strong>Confluence Core</strong> rules you see on the live
              dashboard
            </li>
            <li>
              Connect via <strong>exchange API keys</strong> (Kraken, CoinDCX,
              and more over time)
            </li>
            <li>Transparent decision log on your account</li>
            <li>No on-chain wallet required for spot/perp API trading</li>
          </ul>
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            Until then, watch the public paper agent on the{" "}
            <Link href="/">dashboard</Link>.
          </p>
        </section>
      </main>
    </div>
  );
}
