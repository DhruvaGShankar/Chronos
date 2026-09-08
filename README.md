# ⏳ Chronos Engine v2.1

> **Enterprise-Grade Schema-Driven Organizational Simulation Engine**

Chronos Engine is a universal, domain-agnostic discrete-event simulation framework. Instead of writing custom simulation logic for every business domain (university, banking, retail, logistics), Chronos inspects raw relational database schemas (SQL DDL, SQLite, PostgreSQL), enriches them with behavioral semantics (Finite State Machines, Personas, Rules, Schedules), compiles them into an Intermediate Representation (`ChronosIR v2.1`), and executes deterministic simulations powered by a hierarchical PRNG seed tree.

---

## ✨ Key Features

- **Schema-Driven Introspection**: Automatically parses SQL DDL strings, SQLite database files, or live PostgreSQL schemas into a `StructuralDomainModel` AST with table dependency DAGs and column metadata.
- **Semantic Intelligence & Enrichment**: Discovers entity roles (`ROOT`, `ACTOR`, `EVENT_LOG`, `DIMENSION`), synthesizes Finite State Machines (FSMs), behavioral personas, and invariant business rules.
- **Bit-Exact Determinism**: Hierarchical `PRNGSeedTree` ensures 100% reproducible simulation runs down to individual entity decision trees when given the same root seed.
- **Domain-Agnostic Bytecode Runtime**: The `SimulationKernel` evaluates rules and state transitions dynamically without requiring hardcoded Python domain handlers.
- **Time-Travel Replay & Causal Explanations**: Supports deterministic time-travel state replay and causal root-cause event tracing for full observability.
- **Multi-Format Materialization & Projection**: Export synthetic datasets to SQLite databases, SQL DDL dumps, CSV files, JSON event logs, or Apache Parquet datasets.
- **Interactive Control Web Dashboard**: Includes a responsive web application (`web_dashboard/`) for uploading schemas, inspecting topology DAGs, reviewing candidate models, running live simulations, and exploring causal chains.

---

## 🏗️ Architecture Pipeline

```
       +-------------------------+
       |   Raw SQL / Database    |
       +-------------------------+
                    |
                    v
    [1. Introspection & Graph DAG]
                    |
                    v
    [2. Semantic Enrichment Engine]
  (FSMs, Personas, Invariant Rules)
                    |
                    v
       [3. Chronos IR Compiler]
       (Multi-pass optimization)
                    |
                    v
   [4. Declarative Simulation Kernel]
   (Virtual clock, PRNG seed tree)
                    |
                    v
  [5. Materialization & Projection]
 (SQLite, CSV, Parquet, Replay & Logs)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+

### Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/organization/chronos_engine.git
cd chronos_engine
pip install -e .
```

### Running Example Simulations

Chronos includes pre-configured enterprise domain simulation examples:

```bash
# Run University Organizational Simulation
python examples/run_university_simulation.py

# Run Banking System Simulation
python examples/run_banking_simulation.py

# Run Retail Store Simulation
python examples/run_retail_simulation.py

# Run 50-Table Enterprise Benchmark
python examples/run_50_table_performance_test.py
```

Generated outputs (SQL seeds, CSV files, JSON snapshots) are saved to `examples/output/`.

---

## 💻 Command Line Interface (CLI)

The `chronos` CLI allows introspecting schemas, compiling IR plans, and explaining simulation events directly from your shell:

```bash
# Introspect a SQL DDL schema and output structural intelligence report
chronos introspect --ddl examples/output/schema.sql

# Compile a SQL DDL into a Chronos IR v2.1 JSON execution plan
chronos compile --ddl examples/output/schema.sql --seed 1337

# Run causal explanation for a specific entity ID
chronos explain --actor tb_student_001
```

---

## 🌐 Web Dashboard

Launch the interactive control dashboard:

```bash
python web_dashboard/server.py
```

Then open your browser at `http://localhost:8000` to access:
- **Introspection Tab**: Upload DDL files or connect SQLite databases to visualize table schemas and execution DAGs.
- **Enrichment Tab**: Review and edit discovered state machines, personas, and invariant rules.
- **Simulation Control**: Run discrete-event simulations with real-time metrics and event streams.
- **Replay & Causal Explainer**: Inspect time-travel state checkpoints and trace event causal trees.

---

## 🧪 Running Tests

Execute the pytest suite to verify PRNG determinism and schema introspection:

```bash
python -m pytest tests/
```

---

## 📂 Codebase Directory Structure

```
chronos_engine/
├── chronos/
│   ├── cli/             # CLI command definitions (chronos)
│   ├── compiler/        # Chronos IR multi-pass compiler & lowering
│   ├── core/            # Core AST nodes, IR spec, types & PRNG seed tree
│   ├── enrichment/      # Semantic synthesis (FSMs, personas, rules)
│   ├── introspection/   # DDL, SQLite, Postgres parsers & topology DAG
│   ├── materialization/ # SQLite, CSV, JSON, and SQL dump writers
│   ├── observability/   # Time-travel replay & causal explainer engines
│   ├── projection/      # Parquet and PostgreSQL data projection
│   ├── runtime/         # Simulation kernel, state store & IR executor
│   └── semantics/       # Candidate review and approval workflow
├── examples/            # Pre-packaged domain simulation scripts & DBs
├── tests/               # Pytest suite for determinism & introspection
├── web_dashboard/       # HTTP API server & vanilla JS/CSS web app
└── pyproject.toml       # Package metadata & CLI entry points
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
