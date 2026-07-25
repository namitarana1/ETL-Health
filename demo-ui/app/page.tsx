"use client";

import { useMemo, useRef, useState } from "react";

type RunMode = "full" | "incremental";
type LogEntry = { time: string; tone: "info" | "ok" | "warn"; message: string };

const stages = [
  { id: "01", name: "Ingest", tool: "ADF · Glue · Kafka", detail: "Read 9 linked sources", records: 29034 },
  { id: "02", name: "Bronze", tool: "ADLS · S3", detail: "Write immutable raw rows", records: 29034 },
  { id: "03", name: "Validate", tool: "Databricks · PySpark", detail: "Apply 20 quality rules", records: 28980 },
  { id: "04", name: "Curate", tool: "Delta Lake", detail: "Merge accepted silver rows", records: 28980 },
  { id: "05", name: "Serve", tool: "Snowflake", detail: "Publish 5 gold models", records: 1106 },
];

const datasets = [
  ["Medical claims", "5,000", "claim_id", "Validated"], ["Claim lines", "10,034", "claim_line_id", "Validated"],
  ["Members", "1,000", "member_id", "Masked"], ["Eligibility", "1,000", "eligibility_id", "Validated"],
  ["Providers", "100", "provider_id", "Validated"], ["Pharmacy claims", "1,666", "rx_claim_id", "Validated"],
  ["Authorizations", "1,109", "authorization_id", "Validated"], ["Payments", "4,125", "payment_id", "54 quarantined"],
  ["Encounters", "5,000", "encounter_id", "Validated"],
];

const preview = [
  ["CLM000000001", "MBR0000877", "PRV000041", "INSTITUTIONAL", "DENIED", "$0.00"],
  ["CLM000000002", "MBR0000080", "PRV000093", "PROFESSIONAL", "APPROVED", "$2,986.89"],
  ["CLM000000003", "MBR0000702", "PRV000074", "PROFESSIONAL", "APPROVED", "$1,707.16"],
  ["CLM000000004", "MBR0000931", "PRV000099", "INSTITUTIONAL", "PENDING", "$0.00"],
];

const now = () => new Date().toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });

export default function Home() {
  const [running, setRunning] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [activeStage, setActiveStage] = useState(-1);
  const [progress, setProgress] = useState(0);
  const [processed, setProcessed] = useState(0);
  const [accepted, setAccepted] = useState(0);
  const [rejected, setRejected] = useState(0);
  const [mode, setMode] = useState<RunMode>("full");
  const [injectError, setInjectError] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [query, setQuery] = useState("");
  const consoleRef = useRef<HTMLDivElement>(null);
  const filtered = useMemo(() => datasets.filter((d) => d[0].toLowerCase().includes(query.toLowerCase())), [query]);

  const addLog = (message: string, tone: LogEntry["tone"] = "info") => setLogs((current) => [...current, { time: now(), tone, message }]);
  const delay = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

  const runPipeline = async () => {
    if (running) return;
    const total = mode === "full" ? 29034 : 417;
    const baseRejected = mode === "full" ? 54 : 0;
    setRunning(true); setCompleted(false); setActiveStage(0); setProgress(0); setProcessed(0); setAccepted(0); setRejected(0); setLogs([]);
    window.setTimeout(() => consoleRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 50);
    addLog(`Run initialized · ${mode === "full" ? "FULL REFRESH" : "INCREMENTAL"} · run_id=${Date.now()}`, "ok");
    await delay(450);
    for (let index = 0; index < stages.length; index += 1) {
      setActiveStage(index);
      addLog(`${stages[index].name}: ${stages[index].detail}`);
      const stageStart = index / stages.length;
      for (let tick = 1; tick <= 5; tick += 1) {
        await delay(180);
        const ratio = stageStart + tick / 5 / stages.length;
        setProgress(Math.round(ratio * 100));
        setProcessed(index < 2 ? Math.round(total * Math.min(1, ratio * 2.1)) : total);
      }
      if (index === 0) addLog(`Discovered 9 source datasets · ${total.toLocaleString()} changed rows`, "ok");
      if (index === 1) addLog(`Bronze commit complete · partition run_id=${new Date().toISOString().slice(0, 10)}`, "ok");
      if (index === 2) {
        const failures = baseRejected + (injectError ? 1 : 0);
        setRejected(failures); setAccepted(total - failures);
        addLog(`Quality gate: ${total - failures} accepted · ${failures} quarantined`, failures ? "warn" : "ok");
        if (injectError) addLog("PAY000004126 rejected · UNMATCHED_CLAIM_ID", "warn");
      }
      if (index === 3) addLog("Silver MERGE committed · primary-key row hashes checkpointed", "ok");
      if (index === 4) addLog("Published 5 gold models · reconciliation manifest written", "ok");
    }
    setActiveStage(stages.length); setProgress(100); setCompleted(true); setRunning(false);
    addLog("Pipeline status: SUCCEEDED", "ok");
  };

  return (
    <main>
      <nav className="topbar">
        <div className="brand"><span className="brand-mark">H</span><span>HealthLake</span><small>EXECUTION LAB</small></div>
        <div className="navlinks"><a href="#run">Run</a><a href="#pipeline">Pipeline</a><a href="#data">Datasets</a><a href="#quality">Quality</a></div>
        <span className="environment"><i /> Synthetic data only</span>
      </nav>

      <section className="hero" id="run">
        <div className="hero-copy">
          <p className="kicker">INTERACTIVE HEALTHCARE PIPELINE</p>
          <h1>Press run.<br />Watch data become trusted.</h1>
          <p className="lede">Execute a representative payer batch and follow every record through ingestion, validation, quarantine, silver merges, reconciliation, and gold analytics.</p>
          <div className="run-config">
            <div className="mode-switch" aria-label="Pipeline mode">
              <button className={mode === "full" ? "selected" : ""} onClick={() => setMode("full")} disabled={running}>Full refresh</button>
              <button className={mode === "incremental" ? "selected" : ""} onClick={() => setMode("incremental")} disabled={running}>Incremental</button>
            </div>
            <label className="error-toggle"><input type="checkbox" checked={injectError} onChange={(e) => setInjectError(e.target.checked)} disabled={running} /><span /> Inject a bad payment</label>
          </div>
          <button className="run-button large" onClick={runPipeline} disabled={running}><span>{running ? "◌" : completed ? "↻" : "▶"}</span>{running ? `Executing · ${progress}%` : completed ? "Run again" : "Execute pipeline"}</button>
        </div>
        <div className="execution-console" ref={consoleRef} aria-live="polite">
          <div className="console-head"><div><i className={running ? "pulse" : completed ? "success-dot" : ""}/><span>{running ? "RUNNING" : completed ? "SUCCEEDED" : "READY"}</span></div><code>{mode.toUpperCase()}</code></div>
          <div className="progress-track"><span style={{ width: `${progress}%` }}/></div>
          <div className="live-metrics"><div><span>Processed</span><b>{processed.toLocaleString()}</b></div><div><span>Accepted</span><b>{accepted.toLocaleString()}</b></div><div><span>Rejected</span><b className={rejected ? "amber" : ""}>{rejected.toLocaleString()}</b></div><div><span>Progress</span><b>{progress}%</b></div></div>
          <div className="terminal">
            {logs.length === 0 ? <p className="terminal-empty">Select a mode and execute the pipeline to stream run events here.</p> : logs.map((log, index) => <p key={`${log.time}-${index}`} className={log.tone}><time>{log.time}</time><span>{log.message}</span></p>)}
            {running && <p className="cursor"><time>{now()}</time><span>Processing<span className="blink">_</span></span></p>}
          </div>
          <p className="console-note">Browser execution mirrors the repository pipeline using synthetic aggregate counts.</p>
        </div>
      </section>

      <section className="pipeline section" id="pipeline">
        <div className="section-heading"><div><p className="kicker">LIVE DATA FLOW</p><h2>See each layer execute</h2></div><p>Every stage exposes its task, destination, and record result. A failed validation is quarantined before curated data is published.</p></div>
        <div className="stage-row">{stages.map((stage, index) => <div className={`stage-card ${activeStage === index ? "active" : ""} ${activeStage > index ? "done" : ""}`} key={stage.id}><div className="stage-number">{activeStage > index ? "✓" : stage.id}</div><h3>{stage.name}</h3><b>{stage.tool}</b><p>{stage.detail}</p><div className="stage-result">{activeStage >= index ? stage.records.toLocaleString() : "—"}<small>{index === 4 ? "model rows" : "records"}</small></div>{index < stages.length - 1 && <span className="connector">→</span>}</div>)}</div>
        {completed && <div className="success-banner"><strong>Run completed successfully.</strong> Audit manifest, row watermarks, rejection details, and five gold outputs are ready.</div>}
      </section>

      <section className="dataset-section section" id="data">
        <div className="section-heading"><div><p className="kicker">SYNTHETIC PAYER DATA</p><h2>Nine connected healthcare domains</h2></div><label className="search">⌕<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter datasets" aria-label="Filter datasets" /></label></div>
        <div className="data-layout"><div className="dataset-list"><div className="list-head"><span>Dataset</span><span>Records</span><span>Primary key</span><span>Status</span></div>{filtered.map((d) => <div className="data-row" key={d[0]}><strong>{d[0]}</strong><span>{d[1]}</span><code>{d[2]}</code><em className={d[3].includes("quarantined") ? "warn-status" : ""}>{d[3]}</em></div>)}</div><aside className="relationship-card"><p className="kicker">CORE RELATIONSHIPS</p><div className="entity primary">MEMBERS <small>member_id</small></div><span className="down">↓</span><div className="entity-row"><div className="entity">CLAIMS</div><div className="entity">ELIGIBILITY</div><div className="entity">PHARMACY</div></div><span className="down">↓</span><div className="entity-row"><div className="entity">LINES</div><div className="entity">PAYMENTS</div><div className="entity">PROVIDERS</div></div><p className="relation-note">Foreign keys checked before silver merge</p></aside></div>
        <div className="preview-card"><div className="preview-title"><div><p className="kicker">SOURCE PREVIEW</p><h3>medical_claims.csv</h3></div><span>PHI masked</span></div><div className="table-scroll"><table><thead><tr>{["claim_id","member_id","provider_id","claim_type","status","paid_amount"].map((h)=><th key={h}>{h}</th>)}</tr></thead><tbody>{preview.map((row,i)=><tr key={i}>{row.map((cell,j)=><td key={j} className={j===4?cell.toLowerCase():""}>{cell}</td>)}</tr>)}</tbody></table></div></div>
      </section>

      <section className="quality-section section" id="quality"><div className="section-heading"><div><p className="kicker">TRUST LAYER</p><h2>Quality gates before every load</h2></div><p>Invalid records retain stable error codes and can be corrected and replayed without reprocessing unaffected data.</p></div><div className="quality-grid"><div className="score-card"><div className="score-ring"><b>99.8</b><span>ACCEPTANCE RATE</span></div><div><h3>20 reusable rules</h3><p>Schema, completeness, validity, uniqueness, relationships, and financial accuracy.</p></div></div><div className="checks"><div><span className="check-icon">✓</span><p><b>Referential integrity</b><small>Member, provider, claim, and payment keys</small></p><strong>PASS</strong></div><div><span className="check-icon">✓</span><p><b>Incremental checkpoint</b><small>Primary-key row hashes persisted</small></p><strong>PASS</strong></div><div><span className="warn-icon">!</span><p><b>Future payment dates</b><small>54 records quarantined with error codes</small></p><strong className="warn">REVIEW</strong></div></div><div className="kpi-card"><p className="kicker">GOLD OUTPUTS</p><div><span>Provider KPIs</span><b>100</b></div><div><span>Member utilization</span><b>999</b></div><div><span>Plan performance</span><b>4</b></div><div><span>Authorization metrics</span><b>2</b></div><div><span>Reconciliation</span><b>1</b></div></div></div></section>

      <footer><div className="brand"><span className="brand-mark">H</span><span>HealthLake</span></div><p>Portfolio demonstration · Synthetic data · No real PHI · Not affiliated with UnitedHealthcare</p><span>Azure · AWS · Databricks · Snowflake · Airflow</span></footer>
    </main>
  );
}
