/* Chronos Web Dashboard Frontend Logic */

const PRESET_SCHEMAS = {
  university: `CREATE TABLE TB_DEPARTMENT (
    dept_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE TB_STUDENT (
    student_id VARCHAR(36) PRIMARY KEY,
    dept_id VARCHAR(36) REFERENCES TB_DEPARTMENT(dept_id),
    cgpa FLOAT,
    attendance_pct FLOAT,
    fee_status VARCHAR(20),
    placement_eligible BOOLEAN
);

CREATE TABLE TB_ATTENDANCE (
    attendance_id VARCHAR(36) PRIMARY KEY,
    student_id VARCHAR(36) REFERENCES TB_STUDENT(student_id),
    timestamp DATETIME,
    is_present BOOLEAN
);

CREATE TABLE TB_EXAM_RESULT (
    result_id VARCHAR(36) PRIMARY KEY,
    student_id VARCHAR(36) REFERENCES TB_STUDENT(student_id),
    score FLOAT
);`,

  banking: `CREATE TABLE TB_BRANCH (
    branch_id VARCHAR(36) PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    cash_reserve FLOAT
);

CREATE TABLE TB_CUSTOMER (
    customer_id VARCHAR(36) PRIMARY KEY,
    branch_id VARCHAR(36) REFERENCES TB_BRANCH(branch_id),
    credit_score INTEGER,
    income FLOAT,
    account_balance FLOAT,
    loan_approved BOOLEAN,
    risk_status VARCHAR(20)
);

CREATE TABLE TB_ACCOUNT (
    account_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) REFERENCES TB_CUSTOMER(customer_id),
    account_type VARCHAR(20),
    balance FLOAT
);

CREATE TABLE TB_LOAN_APPLICATION (
    loan_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) REFERENCES TB_CUSTOMER(customer_id),
    requested_amount FLOAT,
    status VARCHAR(20)
);

CREATE TABLE TB_TRANSACTION_LOG (
    txn_id VARCHAR(36) PRIMARY KEY,
    account_id VARCHAR(36) REFERENCES TB_ACCOUNT(account_id),
    amount FLOAT,
    txn_type VARCHAR(20),
    timestamp DATETIME
);`,

  retail: `CREATE TABLE TB_STORE (
    store_id VARCHAR(36) PRIMARY KEY,
    location VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL
);

CREATE TABLE TB_PRODUCT (
    product_id VARCHAR(36) PRIMARY KEY,
    product_code VARCHAR(20) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price FLOAT NOT NULL,
    stock_level INTEGER
);

CREATE TABLE TB_SHOPPER (
    shopper_id VARCHAR(36) PRIMARY KEY,
    store_id VARCHAR(36) REFERENCES TB_STORE(store_id),
    disposable_income FLOAT,
    impulse_buy_index FLOAT,
    total_spent FLOAT,
    vip_status BOOLEAN
);

CREATE TABLE TB_ORDER (
    order_id VARCHAR(36) PRIMARY KEY,
    shopper_id VARCHAR(36) REFERENCES TB_SHOPPER(shopper_id),
    order_date VARCHAR(20),
    total_amount FLOAT,
    status VARCHAR(20)
);`
};

let currentSimulationData = null;

// Initialize Preset
window.addEventListener("DOMContentLoaded", () => {
  loadPresetSchema();
});

function loadPresetSchema() {
  const presetKey = document.getElementById("domainPreset").value;
  if (presetKey !== "custom" && PRESET_SCHEMAS[presetKey]) {
    document.getElementById("sqlEditor").value = PRESET_SCHEMAS[presetKey];
  }
}

async function runIntrospection() {
  const sql = document.getElementById("sqlEditor").value;
  const outDiv = document.getElementById("introspectOutput");
  
  outDiv.innerHTML = `<p style="color: var(--cyan-accent)">Parsing DDL schema & extracting topological dependencies...</p>`;

  try {
    const res = await fetch("/api/introspect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sql_ddl: sql })
    });
    const data = await res.json();

    if (!data.success) {
      outDiv.innerHTML = `<p style="color: var(--rose-accent)">Error: ${data.error}</p>`;
      return;
    }

    let html = `<div style="margin-bottom: 12px;"><b>Tables Discovered (${data.tables.length}):</b></div>`;
    data.tables.forEach(t => {
      html += `
        <div style="background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; border: 1px solid var(--border-color);">
          <span class="node-badge">${t.name}</span>
          <span style="color: var(--cyan-accent); font-size: 12px; margin-left: 8px;">Role: ${t.role}</span>
          <div style="color: var(--text-muted); font-size: 11px; margin-top: 4px;">Columns: ${t.columns.join(", ")}</div>
        </div>`;
    });

    outDiv.innerHTML = html;
  } catch (err) {
    outDiv.innerHTML = `<p style="color: var(--rose-accent)">Network error during introspection.</p>`;
  }
}

async function compileToIR() {
  const sql = document.getElementById("sqlEditor").value;
  const seed = parseInt(document.getElementById("simSeed").value);
  const irPre = document.getElementById("irPreview");

  irPre.textContent = "Compiling AST to Chronos IR...";

  try {
    const res = await fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sql_ddl: sql, seed: seed })
    });
    const data = await res.json();

    if (!data.success) {
      irPre.textContent = "Compilation Error: " + data.error;
      return;
    }

    irPre.textContent = JSON.stringify(data.ir, null, 2);
  } catch (err) {
    irPre.textContent = "Compilation Error: " + err.message;
  }
}

async function runSimulation() {
  const sql = document.getElementById("sqlEditor").value;
  const seed = parseInt(document.getElementById("simSeed").value);
  const ticks = parseInt(document.getElementById("simTicks").value);
  const scale = parseInt(document.getElementById("entityScale").value);

  const explorer = document.getElementById("tableExplorer");
  const eventLogExp = document.getElementById("eventLogExplorer");

  explorer.innerHTML = `<p style="color: var(--cyan-accent); padding: 24px; text-align: center;">Executing Discrete Event Simulation Kernel...</p>`;

  try {
    const res = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sql_ddl: sql,
        seed: seed,
        ticks: ticks,
        entity_counts: { "TB_STUDENT": scale, "TB_CUSTOMER": scale, "TB_SHOPPER": scale, "TB_FACULTY": 3 }
      })
    });
    const data = await res.json();

    if (!data.success) {
      explorer.innerHTML = `<p style="color: var(--rose-accent); padding: 24px;">Simulation Error: ${data.error}</p>`;
      return;
    }

    currentSimulationData = data;

    // Display Metrics
    document.getElementById("metricsRow").style.display = "grid";
    document.getElementById("metricDays").textContent = data.metrics.ticks;
    document.getElementById("metricEvents").textContent = data.metrics.total_events.toLocaleString();
    document.getElementById("metricSpeed").textContent = data.metrics.events_per_sec.toLocaleString() + " Evt/s";
    document.getElementById("metricTime").textContent = data.metrics.exec_time_ms + " ms";

    // Render Materialized Tables
    renderMaterializedTables(data.entity_store);

    // Render Event Stream Logs
    renderEventLogs(data.event_log_sample);

  } catch (err) {
    explorer.innerHTML = `<p style="color: var(--rose-accent); padding: 24px;">Network Error: ${err.message}</p>`;
  }
}

function renderMaterializedTables(store) {
  const explorer = document.getElementById("tableExplorer");
  explorer.innerHTML = "";

  Object.keys(store).forEach(tableName => {
    const records = store[tableName];
    if (!records || records.length === 0) return;

    const cols = Object.keys(records[0]).filter(k => k !== "type");

    let tableHtml = `
      <div style="margin-bottom: 24px;">
        <h4 style="color: var(--cyan-accent); margin-bottom: 8px;">Table: ${tableName} (${records.length} Records)</h4>
        <table>
          <thead>
            <tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>
          </thead>
          <tbody>`;

    records.forEach(r => {
      tableHtml += `<tr>`;
      cols.forEach(c => {
        let val = r[c];
        if (typeof val === "boolean" || c.includes("eligible") || c.includes("approved") || c.includes("status")) {
          let badgeClass = (val === true || val === 1 || val === "CLEAR" || val === "APPROVED" || val === "LOW_RISK" || val === "VIP MEMBER") ? "badge-eligible" : "badge-disqualified";
          tableHtml += `<td><span class="badge ${badgeClass}">${val}</span></td>`;
        } else if (typeof val === "number") {
          tableHtml += `<td>${val.toLocaleString()}</td>`;
        } else {
          tableHtml += `<td>${val || "-"}</td>`;
        }
      });
      tableHtml += `</tr>`;
    });

    tableHtml += `</tbody></table></div>`;
    explorer.innerHTML += tableHtml;
  });
}

function renderEventLogs(events) {
  const container = document.getElementById("eventLogExplorer");
  if (!events || events.length === 0) {
    container.innerHTML = "<p style='padding: 16px; color: var(--text-muted);'>No events logged.</p>";
    return;
  }

  let html = `
    <table>
      <thead>
        <tr>
          <th>Event ID</th>
          <th>Tick (Day)</th>
          <th>Event Type</th>
          <th>Actor ID</th>
          <th>Target Entity</th>
          <th>Payload Details</th>
        </tr>
      </thead>
      <tbody>`;

  events.forEach(e => {
    html += `
      <tr>
        <td style="font-family: var(--font-mono); color: #a5b4fc;">${e.event_id}</td>
        <td>Day ${e.tick}</td>
        <td><span class="badge badge-eligible">${e.event_type}</span></td>
        <td>${e.actor_id}</td>
        <td>${e.target_id}</td>
        <td style="font-family: var(--font-mono); font-size: 11px;">${JSON.stringify(e.payload)}</td>
      </tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}

function exportSQL() {
  if (!currentSimulationData) {
    alert("Please run a simulation first.");
    return;
  }

  let sql = "-- Chronos v2.0 Generated SQL Materialization Dump\nBEGIN;\n\n";
  const store = currentSimulationData.entity_store;

  Object.keys(store).forEach(tname => {
    const records = store[tname];
    if (!records || records.length === 0) return;

    const cols = Object.keys(records[0]).filter(k => k !== "type");
    const colNames = cols.map(c => `"${c}"`).join(", ");

    sql += `INSERT INTO "${tname}" (${colNames}) VALUES\n`;
    const rows = records.map(r => {
      const vals = cols.map(c => {
        let v = r[c];
        if (typeof v === "boolean") return v ? "TRUE" : "FALSE";
        if (typeof v === "number") return v;
        return `'${v}'`;
      });
      return `  (${vals.join(", ")})`;
    });
    sql += rows.join(",\n") + ";\n\n";
  });

  sql += "COMMIT;\n";

  const blob = new Blob([sql], { type: "text/sql" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "chronos_materialized_dump.sql";
  a.click();
}
