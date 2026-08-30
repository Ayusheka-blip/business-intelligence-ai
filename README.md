# Multi-Source AI Root-Cause & Turnaround Engine

**BusinessIntelligence.ai** is an enterprise-grade KPI intelligence-to-action platform built to detect material business metric anomalies, isolate multi-factor root causes across fragmented data streams, and frame persona-specific turnaround action plans [source: 1]. The engine combines deterministic analytical logic with LLM-driven context synthesis to slash analysis resolution latency (mean-time-to-resolution) from 72 hours down to 0.1 hours [source: 1] while maintaining strict data governance, security boundaries, and uncertainty calibration.

For a full description of the project, visit the [project page](https://github.com/Ayusheka-blip/business-intelligence-ai/).

Submit bug reports and feature suggestions, or track changes in the [issue queue](https://github.com/Ayusheka-blip/business-intelligence-ai/issues).


## Table of contents

- Executive Summary
- Core Platform Capabilities
- Requirements
- Architecture & Engine Design
- Deterministic vs LLM Hybrid Processing
- Edge Case Scenarios
- Persona-Based Action Framing
- Security & Governance
- Runtime Telemetry & Cost
- Installation
- Configuration
- Troubleshooting
- FAQ
- Maintainers


## Executive Summary

BusinessIntelligence.ai addresses the challenge of KPI tracking across fragmented enterprise systems. Rather than relying on LLMs for quantitative metrics, the engine uses deterministic SQL and statistical models for exact variance calculations while leveraging LLM workflows for qualitative narrative synthesis (RAG). By integrating sales, inventory, customer voice, and internal signals, it translates complex operational friction into persona-tailored corrective actions .


## Core Platform Capabilities

- **Multi-Source Data Ingestion:** Reconciles quantitative transactions, operational fulfillment logs, customer voice reviews, internal signals, and macro competitor trends across varying refresh cadences and grains .
- **Deterministic & LLM Hybrid Architecture:** Uses SQL pre-aggregations, Z-score anomaly limits, and percentage-based variance decomposition for exact mathematical accuracy, reserving LLM usage strictly for qualitative context retrieval (RAG) and narrative generation.
- **Uncertainty Calibration & Abstention:** Evaluates signal strength and sample size to refrain from hallucinating false certainty; returns weighted probabilistic hypotheses and prompts human operators when evidence is weak or contradictory.
- **Persona-Tailored Insights:** Customizes depth and language based on target roles—providing strategic revenue summaries for Executive Leaders and granular SKU/system breakdowns for Operations Managers.
- **Structured Action Framing:** Maps diagnostic findings directly into operational execution plans following the schema: `Driver → Controllable Lever → Action → Expected Impact → Owner → Confidence`.
- **Enterprise Security & Telemetry:** Enforces row-, column-, and domain-level access controls via semantic contracts while tracking runtime telemetry (latency, token usage, and cost per insight).


## Requirements

This project requires the following environment dependencies:

- **Python 3.10+**: Core analytical engine runtime.
- **SQL / Analytical Backend**: DuckDB, Snowflake, or Databricks for deterministic KPI aggregations.
- **Python Libraries**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pydantic`, `langchain`.


## Architecture & Engine Design

The platform follows an 8-stage operational pipeline:

1. **Multi-Source Data Ingestion**: Reconciles fragmented sources across varying refresh cadences (e.g., real-time checkout streams vs. daily ERP inventory vs. weekly customer voice) .
2. **Semantic & KPI Contract Layer**: Governs standardized metric definitions, formulas, thresholds, lineage, and access controls.
3. **Period Delta Engine & Anomaly Detection**: Uses statistical models (`Z-score`, `Isolation Forest`, `BSTS`) to detect material KPI variance .
4. **Contribution Analysis & Causal Inference**: Deconstructs movements into driver dimensions (e.g., price, volume, region, API error rates).
5. **Context Synthesis via RAG**: Integrates unstructured qualitative signals (support tickets, release notes, employee warnings).
6. **Persona-Specific Narrative Generation**: Generates contextual insights tailored to Executive, Operations, or Finance roles.
7. **Abstention & Calibration Engine**: Calculates confidence scores and refrains from absolute conclusions when data is weak or contradictory.
8. **Feedback Loop & Continuous Learning**: Captures analyst ratings to refine causal attribution algorithms over time.


## Deterministic vs LLM Hybrid Processing

To ensure mathematical accuracy and operational safety, the engine strictly separates quantitative computation from natural language narrative generation:

- **Deterministic & Statistical Engine (Non-LLM)**:
  - **KPI Calculations & Aggregations**: SQL / DuckDB execution based on semantic contracts.
  - **Materiality & Anomaly Detection**: Statistical testing (`Z-score`, standard deviation bounds).
  - **Contribution Slicing**: Exact percentage-based variance decomposition ($\Delta \text{Revenue} = \Delta \text{Price} + \Delta \text{Volume} + \Delta \text{Mix}$).
  - **Security & Entitlements**: Row-, column-, and domain-level security enforcement before LLM retrieval.
- **LLM Processing (Grounded Generation)**:
  - **Intent Understanding**: Mapping user queries to semantic metric targets.
  - **Qualitative RAG**: Scanning unformatted support logs and incident notes.
  - **Narrative Synthesis**: Converting raw quantitative breakdowns into persona-specific textual stories.
  - **Action Structuring**: Formatting root-cause outputs into the schema: `Driver → Controllable Lever → Action → Expected Impact → Owner → Confidence`.


## Edge Case Scenarios

The engine is engineered to handle real-world data complexities:

- **Low-Confidence / Abstention Scenario**: When data signals are weak or contradictory, the system presents weighted probabilistic hypotheses (e.g., 60% Checkout API Gateway Outage vs. 25% Competitor Price Discounting) and prompts human operators for verification rather than hallucinating false certainty.
- **Sparse-History / New Launch Scenario**: Employs Bayesian prior estimates, surrogate category mapping, and synthetic baseline modeling to evaluate newly launched SKUs or markets lacking historical depth.
- **Role-Based Security Scenario**: Enforces row- and column-level access controls via the semantic layer, ensuring unauthorized users (e.g., regional managers) only view aggregated metrics permitted by their role.


## Persona-Based Action Framing

- **Executive Leader**: Summarizes macro revenue impact (-8%), strategic risks, high-level root causes, and top-line mitigation steps .
- **Operations Manager**: Provides granular SKU, gateway, or logistics breakdowns, specifying targeted technical operational levers and immediate 0–30 day corrective workflows.


## Security & Governance

- **Semantic Contract**: Ensures a single source of truth for all metric formulas, preventing drift across dashboards.
- **Role-Based Access Control (RBAC)**: Fine-grained column/row filtering prior to vector storage or prompt context insertion.
- **Traceable Evidence & Lineage**: Every generated insight includes explicit citations referencing the underlying dataset, table source, freshness timestamp, and analytical method used.


## Runtime Telemetry & Cost

- **Latency Baseline**: Reduces analysis resolution latency (MTTR) from 72 hours (manual slicing) down to ~0.1 hours.
- **LLM Cost Optimization**: Uses deterministic logic for calculations, caching frequent queries, and executing small, structured prompts to minimize token usage and per-insight cost.


## Installation

Install as you would normally deploy an engine prototype:

1. Clone the project repository:
   ```bash
   git clone [https://github.com/Ayusheka-blip/business-intelligence-ai.git](https://github.com/Ayusheka-blip/business-intelligence-ai.git)
   cd business-intelligence-ai
