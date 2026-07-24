"use client";

import { useMemo, useState } from "react";

const stages = [
  { id: "01", name: "Ingest", tool: "ADF · Glue · Kafka", detail: "9 linked source tables" },
  { id: "02", name: "Bronze", tool: "ADLS · S3", detail: "Immutable raw records" },
  { id: "03", name: "Validate", tool: "Databricks · PySpark", detail: "20 quality controls" },
  { id: "04", name: "Curate", tool: "Delta Lake", detail: "Deduped silver + KPIs" },
  { id: "05", name: "Serve", tool: "Snowflake", detail: "Analytics-ready gold" },
];

const datasets = [
  ["Medical claims", "5,000", "claim_id", "Validated"],
  ["Claim lines", "10,034", "claim_line_id", "Validated"],
  ["Members", "1,000", "member_id", "Masked"],
  ["Eligibility", "1,000", "eligibility_id", "Validated"],
  ["Providers", "100", "provider_id", "Validated"],
  ["Pharmacy claims", "1,666", "rx_claim_id", "Validated"],
  ["Authorizations", "1,109", "authorization_id", "Validated"],
  ["Payments", "4,125", "payment_id", "Reconciled"],
  ["Encounters", "5,000", "encounter_id", "Validated"],
];

const preview = [
  ["CLM000000001", "MBR0000655", "PRV000015", "PROFESSIONAL", "APPROVED", "$1,842.61"],
  ["CLM000000002", "MBR0000115", "PRV000070", "INSTITUTIONAL", "DENIED", "$0.00"],
  ["CLM000000003", "MBR0000760", "PRV000036", "PROFESSIONAL", "APPROVED", "$624.19"],
  ["CLM000000004", "MBR0000282", "PRV000088", "INSTITUTIONAL", "PENDING", "$0.00"],
];

export default function Home() {
  const [running, setRunning] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [activeStage, setActiveStage] = useState(-1);
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => datasets.filter((d) => d[0].toLowerCase().includes(query.toLowerCase())), [query]);

  const runPipeline = () => {
    if (running) return;
    setRunning(true); setCompleted(false); setActiveStage(0);
    let step = 0;
    const timer = window.setInterval(() => {
      step += 1;
      if (step === stages.length) {
        window.clearInterval(timer); setRunning(false); setCompleted(true); setActiveStage(stages.length);
      } else setActiveStage(step);
    }, 650);
  };

  return (
    <main>
      <nav className="topbar">
        <div className="brand"><span className="brand-mark">H</span><span>HealthLake</span><small>DEMO</small></div>
        <div className="navlinks"><a href="#pipeline">Pipeline</a><a href="#data">Datasets</a><a href="#quality">Quality</a></div>
        <span className="environment"><i /> Synthetic data only</span>
      </nav>

      <section className="hero">
        <div className="hero-copy">
          <p className="kicker">MULTI-CLOUD HEALTHCARE DATA PLATFORM</p>
          <h1>From raw payer data<br />to trusted decisions.</h1>
          <p className="lede">A functional demonstration of how medical claims, eligibility, provider, pharmacy, authorization, payment, and encounter data move through a secure medallion pipeline.</p>
          <div className="actions">
            <button className="run-button" onClick={runPipeline} disabled={running}><span>{running ? "◌" : completed ? "✓" : "▶"}</span>{running ? "Processing pipeline…" : completed ? "Run completed" : "Run pipeline demo"}</button>
            <a href="#data" className="text-link">Explore the data →</a>
          </div>
        </div>
        <div className="hero-panel">
          <div className="panel-head"><span>LAST SUCCESSFUL RUN</span><strong>98.7% quality score</strong></div>
          <div className="big-number">28,934</div><div className="subnumber">records processed across 9 datasets</div>
          <div className="mini-grid"><div><b>3m 18s</b><span>runtime</span></div><div><b>0</b><span>orphan keys</span></div><div><b>9 / 9</b><span>tables loaded</span></div></div>
          <div className="spark"><span style={{height:"32%"}}/><span style={{height:"45%"}}/><span style={{height:"38%"}}/><span style={{height:"62%"}}/><span style={{height:"57%"}}/><span style={{height:"83%"}}/><span style={{height:"74%"}}/><span style={{height:"100%"}}/></div>
        </div>
      </section>

      <section className="pipeline section" id="pipeline">
        <div className="section-heading"><div><p className="kicker">HOW IT WORKS</p><h2>One governed path from source to insight</h2></div><p>Airflow coordinates every stage with retries, audit logs, checkpoints, and reconciliation gates.</p></div>
        <div className="stage-row">
          {stages.map((stage, index) => <div className={`stage-card ${activeStage === index ? "active" : ""} ${activeStage > index ? "done" : ""}`} key={stage.id}><div className="stage-number">{activeStage > index ? "✓" : stage.id}</div><h3>{stage.name}</h3><b>{stage.tool}</b><p>{stage.detail}</p>{index < stages.length - 1 && <span className="connector">→</span>}</div>)}
        </div>
        {completed && <div className="success-banner"><strong>Pipeline complete.</strong> 28,934 records processed, 9 tables published, and all reconciliation checks passed.</div>}
      </section>

      <section className="dataset-section section" id="data">
        <div className="section-heading"><div><p className="kicker">SYNTHETIC PAYER DATA</p><h2>Nine connected healthcare domains</h2></div><label className="search">⌕<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter datasets" aria-label="Filter datasets" /></label></div>
        <div className="data-layout">
          <div className="dataset-list"><div className="list-head"><span>Dataset</span><span>Records</span><span>Primary key</span><span>Status</span></div>{filtered.map((d) => <div className="data-row" key={d[0]}><strong>{d[0]}</strong><span>{d[1]}</span><code>{d[2]}</code><em>{d[3]}</em></div>)}</div>
          <aside className="relationship-card"><p className="kicker">CORE RELATIONSHIPS</p><div className="entity primary">MEMBERS <small>member_id</small></div><span className="down">↓</span><div className="entity-row"><div className="entity">CLAIMS</div><div className="entity">ELIGIBILITY</div><div className="entity">PHARMACY</div></div><span className="down">↓</span><div className="entity-row"><div className="entity">LINES</div><div className="entity">PAYMENTS</div><div className="entity">PROVIDERS</div></div><p className="relation-note">All foreign keys validated · no orphan records</p></aside>
        </div>
        <div className="preview-card"><div className="preview-title"><div><p className="kicker">DATA PREVIEW</p><h3>medical_claims.csv</h3></div><span>PHI masked</span></div><div className="table-scroll"><table><thead><tr>{["claim_id","member_id","provider_id","claim_type","status","paid_amount"].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{preview.map((row,i)=><tr key={i}>{row.map((cell,j)=><td key={j} className={j===4?cell.toLowerCase():""}>{cell}</td>)}</tr>)}</tbody></table></div></div>
      </section>

      <section className="quality-section section" id="quality">
        <div className="section-heading"><div><p className="kicker">TRUST LAYER</p><h2>Quality gates before every load</h2></div><p>Invalid records are quarantined with explainable error codes, then corrected and replayed independently.</p></div>
        <div className="quality-grid">
          <div className="score-card"><div className="score-ring"><b>98.7</b><span>QUALITY SCORE</span></div><div><h3>20 reusable rules</h3><p>Schema, completeness, validity, uniqueness, and financial accuracy.</p></div></div>
          <div className="checks"><div><span className="check-icon">✓</span><p><b>Referential integrity</b><small>0 orphan claim or payment keys</small></p><strong>PASS</strong></div><div><span className="check-icon">✓</span><p><b>Financial reconciliation</b><small>Source and target totals balanced</small></p><strong>PASS</strong></div><div><span className="warn-icon">!</span><p><b>Rejected records</b><small>378 quarantined for correction</small></p><strong className="warn">REVIEW</strong></div></div>
          <div className="kpi-card"><p className="kicker">GOLD KPI OUTPUT</p><div><span>Claim approval rate</span><b>82.5%</b></div><div><span>Average paid claim</span><b>$2,104</b></div><div><span>Authorization volume</span><b>1,109</b></div><div><span>Payment match rate</span><b>100%</b></div></div>
        </div>
      </section>

      <footer><div className="brand"><span className="brand-mark">H</span><span>HealthLake</span></div><p>Portfolio demonstration · Synthetic data · No real PHI · Not affiliated with UnitedHealthcare</p><span>Azure · AWS · Databricks · Snowflake · Airflow</span></footer>
    </main>
  );
}
