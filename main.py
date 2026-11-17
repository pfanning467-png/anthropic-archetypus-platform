import json
import os
import random
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Anthropic Global Archetypus Thinking & Workforce Platform")
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_PATH = os.getenv("WORKFORCE_DB_PATH", "archetypus_os_v5.db")
MEASUREMENT_WINDOW = "7-Day Rolling Window (Nov 10 – Nov 16, 2026)"

GLOBAL_HUBS = [
    "San Francisco (HQ)", "New York", "Seattle", "Washington D.C.",
    "Dublin (EMEA Hub)", "London", "Paris", "Munich", "Zurich", "Milan",
    "Tokyo", "Seoul"
]

OPERATING_PRINCIPLE = {
    "title": "Anthropic Global Archetypus Thinking & Workforce Platform",
    "subtitle": "Learn what the organisation knows · Identify what it needs next · Coordinate execution · Independently verify outcomes.",
    "measurement_window": MEASUREMENT_WINDOW,
    "global_hubs": GLOBAL_HUBS,
}

# --- RECONCILED 20 DIVISIONS (5,300 STAFF · 661 OPEN ROLES · 39 SUB-PODS) ---
DEPARTMENTS = [
    {
        "id": "sales", "name": "Sales", "roles": 124, "headcount": 780,
        "director": "Dir. Commercial GTM", "base_risk": 0,
        "hubs": "San Francisco, New York, Dublin, London, Paris, Munich, Milan, Tokyo, Seoul",
        "charter": "Zero-token SQL/KV retrieval for pre-approved SOC2/HIPAA/ZDR security packs (KNO-B-044); bespoke contract redlines escalate to Legal.",
        "sub_departments": [
            {"id": "ent-gtm", "name": "Enterprise Account Execution", "procedure": "Pulls verified industry ROI benchmarks from Layer B before drafting executive briefs."},
            {"id": "rfp-desk", "name": "Security & RFP Desk", "procedure": "Retrieves canonical SOC2/HIPAA/ZDR packs deterministically (0 LLM tokens)."},
        ],
    },
    {
        "id": "ai-research", "name": "AI Research & Engineering", "roles": 73, "headcount": 680,
        "director": "Dir. Frontier Research", "base_risk": 2,
        "hubs": "San Francisco, London, Zurich, New York",
        "charter": "Evaluates 7-dimension applicability before compute; auto-triggers REVALIDATE on model generation shifts (4.5 -> 5.5).",
        "sub_departments": [
            {"id": "pretrain", "name": "Pre-Training & Scaling Laws", "procedure": "Reuses validated scaling curves; runs delta sweeps on new hyperparameters only."},
            {"id": "posttrain", "name": "Post-Training & RLHF", "procedure": "Pulls reward-model baselines from Layer A; never regenerates preference datasets."},
            {"id": "interp", "name": "Mechanistic Interpretability", "procedure": "Queries existing SAE feature dictionaries before running new circuit traces."},
            {"id": "evals", "name": "Frontier Evaluations", "procedure": "Executes deterministic benchmark subsets; escalates anomalies to Level-2 review."},
        ],
    },
    {
        "id": "applied-ai", "name": "Applied AI", "roles": 67, "headcount": 420,
        "director": "Dir. Enterprise Solutions", "base_risk": 1,
        "hubs": "San Francisco, New York, Dublin, London, Tokyo",
        "charter": "Clones validated enterprise RAG/agent blueprints; builds client-specific schema deltas only.",
        "sub_departments": [
            {"id": "sol-arch", "name": "Solutions Architecture", "procedure": "Adapts canonical reference architectures with minimal schema delta."},
            {"id": "fde", "name": "Forward-Deployed Engineering", "procedure": "Commits field deployment learnings back to Layer A within 24 hours."},
        ],
    },
    {
        "id": "security", "name": "Security", "roles": 54, "headcount": 320,
        "director": "Dir. Model Weight Security", "base_risk": 3,
        "hubs": "San Francisco, Seattle, Dublin, London",
        "charter": "Enforces least-privilege read/write scopes; deduplicates CVEs/IOCs and requires Level-3 human attestation.",
        "sub_departments": [
            {"id": "weight-sec", "name": "Model Weight & Infra Security", "procedure": "Zero-trust enclave verification with mandatory Level-3 sign-off."},
            {"id": "app-sec", "name": "Product & AppSec", "procedure": "Reuses SAST/DAST baselines on pull-request diffs only."},
        ],
    },
    {
        "id": "eng-product", "name": "Engineering & Design - Product", "roles": 51, "headcount": 540,
        "director": "Dir. Claude Product Eng", "base_risk": 1,
        "hubs": "San Francisco, New York, Seattle, Dublin",
        "charter": "Consumes canonical Data Science metric batons and UI registries; enforces minimal AST diffs.",
        "sub_departments": [
            {"id": "claude-web", "name": "Claude Web & Desktop", "procedure": "Reuses design-system tokens and accessibility specs."},
            {"id": "claude-code", "name": "Claude Code & Agentic CLI", "procedure": "Enforces compact context diffs and repository map caching."},
        ],
    },
    {
        "id": "finance", "name": "Finance", "roles": 48, "headcount": 260,
        "director": "Dir. Compute Economics", "base_risk": 2,
        "hubs": "San Francisco, Dublin, London",
        "charter": "Tracks Inference, Retrieval, Human Review, Experimentation, and Infrastructure costs per validated outcome.",
        "sub_departments": [
            {"id": "finops", "name": "AI FinOps & Token Governance", "procedure": "Audits division Cost per Validated Outcome and reuse efficiency."},
            {"id": "fpa", "name": "Strategic FP&A", "procedure": "Pulls validated Compute capacity batons instead of raw vendor logs."},
        ],
    },
    {
        "id": "swe-infra", "name": "Software Engineering - Infrastructure", "roles": 38, "headcount": 490,
        "director": "Dir. Inference & Distributed Sys", "base_risk": 2,
        "hubs": "San Francisco, Seattle, Dublin, Zurich",
        "charter": "Executes Execution Contract Batons with mandatory 30-second rollback flags before promoting kernel changes.",
        "sub_departments": [
            {"id": "inference", "name": "Distributed Inference Engine", "procedure": "Profiles KV-cache quantization and p99 decode latency on canary slices."},
            {"id": "gateway", "name": "API Gateway & Prompt Cache", "procedure": "Maintains provider prompt-cache hit rates across all 20 divisions."},
            {"id": "sre", "name": "Reliability & SRE", "procedure": "Triages incidents via canonical runbooks before escalating."},
        ],
    },
    {
        "id": "safeguards", "name": "Safeguards (Trust & Safety)", "roles": 35, "headcount": 310,
        "director": "Dir. ASL & Alignment Eval", "base_risk": 3,
        "hubs": "San Francisco, Dublin, London, Washington D.C.",
        "charter": "Blocks repeat dead-end filter architectures (KNO-D-042) unless retest triggers are met; Level-3 sign-off on ASL shifts.",
        "sub_departments": [
            {"id": "asl", "name": "ASL Policy & Frontier Risk", "procedure": "Mandatory Level-3 Human Authority determination on ASL thresholds."},
            {"id": "redteam", "name": "Adversarial Red-Teaming", "procedure": "Deduplicates jailbreak vectors against redteam-bench-v9."},
            {"id": "filters", "name": "Constitutional Classifiers", "procedure": "Uses cached Haiku-5.5 constitutional probes; blocks stateless BERT pre-filters."},
        ],
    },
    {
        "id": "compute", "name": "Compute", "roles": 27, "headcount": 240,
        "director": "Dir. Cluster Capacity", "base_risk": 2,
        "hubs": "San Francisco, Seattle",
        "charter": "Monitors cluster preemption and batch-latency bottlenecks; reuses validated checkpoint schedules.",
        "sub_departments": [
            {"id": "sched", "name": "Trainium2 / GPU Pod Scheduling", "procedure": "Applies validated async checkpoint intervals across 4,096-chip slices."},
            {"id": "cap", "name": "Capacity & Yield Forecasting", "procedure": "Consumes FinOps telemetry batons for quarterly accelerator allocation."},
        ],
    },
    {
        "id": "tpm", "name": "Technical Program Management", "roles": 24, "headcount": 65,
        "director": "Dir. Cross-Org Execution", "base_risk": 1,
        "hubs": "San Francisco, Dublin, London",
        "charter": "Tracks cross-division Execution Contract Batons, dependencies, deadlines, and receiver handshakes.",
        "sub_departments": [
            {"id": "launch-tpm", "name": "Model Launch & Cross-Org TPM", "procedure": "Coordinates release readiness gates across Research, Safeguards, and Infra."},
        ],
    },
    {
        "id": "marketing", "name": "Marketing & Brand", "roles": 21, "headcount": 185,
        "director": "Dir. Brand Strategy", "base_risk": 1,
        "hubs": "San Francisco, New York, London, Paris, Munich",
        "charter": "Anchors external positioning strictly to verified Layer-B CANONICAL IDs; isolates research from copy execution.",
        "sub_departments": [
            {"id": "prod-mkt", "name": "Product Marketing", "procedure": "Builds launch messaging directly from validated Research/Applied AI batons."},
            {"id": "brand-comms", "name": "Brand & Editorial", "procedure": "Applies cached editorial guidelines without regenerating style rules."},
        ],
    },
    {
        "id": "pm-ops", "name": "Product Management, Support, & Operations", "roles": 19, "headcount": 230,
        "director": "Dir. Product Operations", "base_risk": 0,
        "hubs": "San Francisco, Dublin, Tokyo, Seoul",
        "charter": "Routes Tier-1/2 operational issues to validated runbooks in Layer B (0 generative tokens).",
        "sub_departments": [
            {"id": "support", "name": "Enterprise Support Ops", "procedure": "Retrieves verified resolutions; logs novel edge cases to Layer A."},
        ],
    },
    {
        "id": "legal", "name": "Legal", "roles": 18, "headcount": 145,
        "director": "Dir. AI Governance & IP", "base_risk": 3,
        "hubs": "San Francisco, Washington D.C., Dublin, London",
        "charter": "Diffs contract redlines against canonical MSA/DPA templates; Level-3 Counsel ratification on novel IP/regulatory risk.",
        "sub_departments": [
            {"id": "comm-legal", "name": "Commercial & Enterprise Contracts", "procedure": "Evaluates clause deltas against approved fallback positions."},
            {"id": "ip-reg", "name": "IP & Regulatory Compliance", "procedure": "Issues Level-3 legal determinations on statutory obligations."},
        ],
    },
    {
        "id": "people", "name": "People", "roles": 16, "headcount": 160,
        "director": "Dir. Talent & Org Design", "base_risk": 1,
        "hubs": "San Francisco, New York, Dublin, London, Tokyo",
        "charter": "Applies calibrated competency matrices across all 661 open roles globally.",
        "sub_departments": [
            {"id": "recruiting", "name": "Technical & GTM Recruiting", "procedure": "Reuses calibrated interview rubrics across all 20 divisions."},
        ],
    },
    {
        "id": "public-policy", "name": "Public Policy", "roles": 15, "headcount": 95,
        "director": "Dir. Frontier Policy", "base_risk": 3,
        "hubs": "Washington D.C., Dublin, London, Paris, Tokyo",
        "charter": "Maintains one canonical global governance core (EU AI Act / US NIST / UK AISI) and derives jurisdiction deltas only.",
        "sub_departments": [
            {"id": "global-reg", "name": "Global Standards & Regulatory", "procedure": "Maps canonical governance core to regional regulatory deltas."},
        ],
    },
    {
        "id": "data-science", "name": "Data Science & Analytics", "roles": 11, "headcount": 140,
        "director": "Dir. Telemetry & Eval", "base_risk": 0,
        "hubs": "San Francisco, New York, Dublin",
        "charter": "Publishes verified SQL/cohort definitions once to Layer B so teams never write duplicate queries.",
        "sub_departments": [
            {"id": "prod-ds", "name": "Product & Retention Analytics", "procedure": "Serves canonical metric batons to Product, Finance, and GTM."},
        ],
    },
    {
        "id": "communications", "name": "Communications", "roles": 8, "headcount": 75,
        "director": "Dir. Global Comms", "base_risk": 2,
        "hubs": "San Francisco, New York, London",
        "charter": "Requires every external statement to trace to an immutable sha256 evidence hash and CANONICAL record.",
        "sub_departments": [
            {"id": "press", "name": "Press & Executive Comms", "procedure": "Verifies citations against Layer B before Level-2 editorial sign-off."},
        ],
    },
    {
        "id": "public-benefit", "name": "Public Benefit", "roles": 8, "headcount": 55,
        "director": "Dir. Societal Impact", "base_risk": 2,
        "hubs": "San Francisco, Washington D.C., London",
        "charter": "Aggregates anonymised longitudinal cohorts from Layer B for Long-Term Benefit Trust reporting.",
        "sub_departments": [
            {"id": "econ-impact", "name": "Economic & Labor Impact", "procedure": "Synthesises societal impact briefs from privacy-safe cohorts."},
        ],
    },
    {
        "id": "hardware", "name": "Hardware", "roles": 2, "headcount": 65,
        "director": "Dir. Silicon & Accelerators", "base_risk": 2,
        "hubs": "San Francisco, Seattle",
        "charter": "Reuses validated thermal/power envelopes and triggers REVALIDATE only when silicon stepping specs change.",
        "sub_departments": [
            {"id": "silicon", "name": "Custom Silicon & Interconnects", "procedure": "Runs delta thermal simulations on new hardware steppings."},
        ],
    },
    {
        "id": "tech-ed", "name": "Technical Education", "roles": 2, "headcount": 45,
        "director": "Dir. Developer Enablement", "base_risk": 0,
        "hubs": "San Francisco, London, Paris, Tokyo",
        "charter": "Generates developer cookbooks from Layer-B Applied AI blueprints (Level 0); auto-escalates net-new DISCOVER modules to Level 2.",
        "sub_departments": [
            {"id": "curriculum", "name": "Anthropic Academy & Labs", "procedure": "Auto-syncs interactive notebooks with validated reference architectures."},
        ],
    },
]

SEED_LAYER_E = [
    {
        "pred_id": "PRED-E-001",
        "opportunity_type": "REUSE BOTTLENECK",
        "target_division": "Sales · Security & RFP Desk",
        "signal_source": "142 duplicate Sonnet-5.5 calls/wk detected querying identical SOC2/ZDR clauses.",
        "recommended_action": "Route standard security keys directly to deterministic record KNO-B-044 (0 LLM tokens).",
        "expected_value_usd": 1455.34,
        "success_prob": 0.98,
        "estimated_cost_usd": 12.00,
        "risk_penalty_usd": 5.00,
        "ev_score": 1409.23,
        "promotion_guardrail": "Recommendation Only · Requires Controlled Test + Deputy General Counsel Sign-Off",
        "status": "ACTIONABLE",
    },
    {
        "pred_id": "PRED-E-002",
        "opportunity_type": "GENERATION DRIFT",
        "target_division": "AI Research & SWE-Infra",
        "signal_source": "KNO-A-041 has 94% confidence on Sonnet-4.5, but 0% verified applicability on Sonnet-5.5.",
        "recommended_action": "Run bounded 64-batch revalidation sweep on claude-sonnet-5-5 before cluster rollout.",
        "expected_value_usd": 4200.00,
        "success_prob": 0.86,
        "estimated_cost_usd": 185.00,
        "risk_penalty_usd": 120.00,
        "ev_score": 3307.00,
        "promotion_guardrail": "Recommendation Only · Requires SWE-Infra Canary Verification before CANONICAL promotion",
        "status": "ACTIONABLE",
    },
    {
        "pred_id": "PRED-E-003",
        "opportunity_type": "KNOWLEDGE GAP",
        "target_division": "Public Policy & Legal",
        "signal_source": "Canonical Governance Core (KNO-B-045) lacks APAC Sovereign Cloud residency delta module.",
        "recommended_action": "Commission scoped DISCOVER task with Level-3 Legal/Policy sign-off and rollback plan.",
        "expected_value_usd": 2800.00,
        "success_prob": 0.79,
        "estimated_cost_usd": 310.00,
        "risk_penalty_usd": 240.00,
        "ev_score": 1662.00,
        "promotion_guardrail": "Recommendation Only · Requires Level-3 Designated Human Authority Ratification",
        "status": "ACTIONABLE",
    },
]

SEED_KNOWLEDGE = [
    {
        "entry_id": "KNO-A-041",
        "layer": "A · Research & Experiment Memory",
        "lifecycle_state": "REQUIRING_REVALIDATION",
        "expiry_status": "ACTIVELY_INVALIDATED",
        "owner": "Dr. M. Chen",
        "dept": "AI Research & Engineering",
        "sub_dept": "Mechanistic Interpretability",
        "title": "Long-Context KV-Cache Quantization at 200k Tokens",
        "evidence_refs": ["artifact://exp-041/kv-quant.parquet", "commit://9f82c1a"],
        "model_version": "claude-sonnet-4-5",
        "dataset_version": "eval-suite-v4.2",
        "environment_tag": "trainium2-kernel-2.14",
        "historical_confidence": 0.94,
        "reproducibility_score": 0.96,
        "evidence_quality_score": 0.95,
        "freshness_score": 0.42,
        "independent_reviewer": "SWE-Infra Canary Lead",
        "limitations": "High historical confidence (94%) on Sonnet-4.5, but actively invalidated for Sonnet-5.5 generation.",
        "last_verified": "2026-10-28",
        "expiry_condition": "Invalidated by 5.5 model generation rollout; requires 5.5 canary sweep.",
        "permissions": "ALL_DIVISIONS_READ",
        "failure_conditions": None,
        "retest_triggers": None,
        "deterministic_eligible": False,
        "summary": "4-bit KV quantization cut HBM footprint by 61% on 4.5 series; queued for 5.5 generation revalidation.",
    },
    {
        "entry_id": "KNO-D-042",
        "layer": "D · Negative-Finding Memory",
        "lifecycle_state": "ACTIVELY_MONITORED",
        "expiry_status": "CURRENT",
        "owner": "S. Patel",
        "dept": "Safeguards (Trust & Safety)",
        "sub_dept": "Constitutional Classifiers",
        "title": "Standalone Small-BERT Pre-Filter for Multi-Turn Biosecurity Screening",
        "evidence_refs": ["artifact://exp-042/redteam-neg.json", "eval://redteam-bench-v9"],
        "model_version": "bert-tiny-guard-v2",
        "dataset_version": "redteam-bench-v9",
        "environment_tag": "safety-pipe-2.1",
        "historical_confidence": 0.91,
        "reproducibility_score": 0.94,
        "evidence_quality_score": 0.92,
        "freshness_score": 0.95,
        "independent_reviewer": "ASL Eval Committee",
        "limitations": "Failed under stateless single-turn encoder architecture; reconsider only if stateful distillation is added.",
        "last_verified": "2026-11-13",
        "expiry_condition": "Reconsider if stateful multi-turn distillation or redteam-bench-v10 lands.",
        "permissions": "SAFEGUARDS_AND_RESEARCH",
        "failure_conditions": "Fails when deployed as standalone stateless pre-filter on multi-turn benign dual-use prompts (11.4% false refusal).",
        "retest_triggers": "Retest only if stateful context-window distillation is added OR safety baseline changes.",
        "deterministic_eligible": False,
        "summary": "Conditional failure under stateless single-turn pre-filtering; use cached Haiku-5.5 constitutional probe instead.",
    },
    {
        "entry_id": "KNO-B-044",
        "layer": "B · Validated Organisational Knowledge",
        "lifecycle_state": "CANONICAL",
        "expiry_status": "CURRENT",
        "owner": "R. O'Connor",
        "dept": "Sales",
        "sub_dept": "Security & RFP Desk",
        "title": "Canonical Enterprise Financial Services SOC2 / HIPAA / ZDR Security Pack",
        "evidence_refs": ["artifact://kb-044/finserv-rfp-pack.json", "legal://signoff-2026-q4"],
        "model_version": "claude-sonnet-5-5",
        "dataset_version": "soc2-iso-2026-q4",
        "environment_tag": "rfp-registry-3.1",
        "historical_confidence": 0.99,
        "reproducibility_score": 1.00,
        "evidence_quality_score": 0.99,
        "freshness_score": 0.98,
        "independent_reviewer": "Deputy General Counsel",
        "limitations": "Covers standard US/EU Zero-Data-Retention terms; bespoke indemnity requires Level-3 Legal review.",
        "last_verified": "2026-11-15",
        "expiry_condition": "Due for quarterly review 2027-02-15.",
        "permissions": "ALL_DIVISIONS_READ",
        "failure_conditions": None,
        "retest_triggers": None,
        "deterministic_eligible": True,
        "summary": "Pre-approved SOC2 Type II, HIPAA BAA, and Zero-Data-Retention responses retrievable via deterministic lookup (0 LLM tokens).",
    },
    {
        "entry_id": "KNO-B-045",
        "layer": "B · Validated Organisational Knowledge",
        "lifecycle_state": "ACTIVELY_MONITORED",
        "expiry_status": "DUE_FOR_REVIEW",
        "owner": "E. Lindqvist",
        "dept": "Public Policy",
        "sub_dept": "Global Standards & Regulatory",
        "title": "Canonical Frontier Governance Core (EU AI Act GPAI / US NIST / UK AISI)",
        "evidence_refs": ["artifact://kb-045/global-reg-core.md", "policy://board-ratified-v3"],
        "model_version": "claude-opus-5-5",
        "dataset_version": "reg-corpus-2026-q4",
        "environment_tag": "policy-mapper-1.4",
        "historical_confidence": 0.96,
        "reproducibility_score": 0.95,
        "evidence_quality_score": 0.97,
        "freshness_score": 0.84,
        "independent_reviewer": "Head of Global Policy",
        "limitations": "Due for scheduled 30-day regulatory check; still valid for current filings without full recompute.",
        "last_verified": "2026-10-18",
        "expiry_condition": "Due for scheduled review (non-invalidated); full revalidation only if EU AI Office updates GPAI code.",
        "permissions": "POLICY_LEGAL_COMMS",
        "failure_conditions": None,
        "retest_triggers": None,
        "deterministic_eligible": False,
        "summary": "Unified 5.5-series compliance core mapped to regional deltas; eliminates 3x parallel drafting.",
    },
    {
        "entry_id": "KNO-C-046",
        "layer": "C · Operational Memory",
        "lifecycle_state": "UNDER_VALIDATION",
        "expiry_status": "CURRENT",
        "owner": "Launch TPM Pod",
        "dept": "Technical Program Management",
        "sub_dept": "Model Launch & Cross-Org TPM",
        "title": "Q4 Inference Kernel Rollout Dependency & Ownership Graph",
        "evidence_refs": ["baton://BTN-8812", "jira://REL-409"],
        "model_version": "claude-sonnet-5-5",
        "dataset_version": "prod-rollout-nov26",
        "environment_tag": "orchestrator-2.0",
        "historical_confidence": 0.93,
        "reproducibility_score": 0.91,
        "evidence_quality_score": 0.92,
        "freshness_score": 0.96,
        "independent_reviewer": "VP Infrastructure",
        "limitations": "5.5-series KV-cache revalidation pending canary promotion.",
        "last_verified": "2026-11-16",
        "expiry_condition": "Transitions to CANONICAL upon production canary sign-off.",
        "permissions": "ALL_DIVISIONS_READ",
        "failure_conditions": None,
        "retest_triggers": None,
        "deterministic_eligible": False,
        "summary": "Tracks cross-division execution contract from AI Research to SWE-Infra.",
    },
]

SEED_BATONS = [
    {
        "contract_id": "BTN-8812",
        "from_pod": "AI Research · Mechanistic Interpretability",
        "receiving_owner": "Lead Inference Architect (SWE-Infra)",
        "objective": "Revalidate 4-bit KV-cache quantization on claude-sonnet-5-5 at 64-batch concurrency",
        "status": "IN_EXECUTION",
        "source_knowledge_ids": ["KNO-A-041", "KNO-C-046"],
        "acceptance_criteria": [
            "p99 decode latency <= 18ms at 64 concurrent 200k-context streams",
            "Needle-in-haystack recall degradation < 0.30% vs FP16 baseline",
            "Independent canary sign-off recorded in Layer B before cluster cutover",
        ],
        "dependencies": ["Trainium2 slice reservation #TRN-44", "eval-suite-v4.3 harness"],
        "rollback_plan": "Revert inference router flag kv_quant_4bit=false to fall back to FP8 KV cache within 30s.",
        "deadline": "2026-11-18T18:00:00Z",
        "evidence_manifest": ["artifact://exp-041/kv-quant.parquet", "sha256:9f82c1a4"],
        "budget_remaining_usd": 142.50,
        "governance_level": "level_2_dept_leader",
        "escalation_reason": "Elevated from Level 1 to Level 2: Production inference kernel cutover affects multi-division SLA.",
        "approval_status": "APPROVED (VP Infrastructure · 2026-11-16T09:10Z)",
        "receiver_ack": "ACKNOWLEDGED",
    }
]

LIVE_FEED_EVENTS = [
    {"time": "19:08:12 UTC", "hub": "Dublin (EMEA Hub)", "division": "Sales · RFP Desk", "route": "REUSE", "detail": "Served KNO-B-044 SOC2/ZDR pack deterministically (0 LLM tokens · saved 9,400t)"},
    {"time": "19:09:44 UTC", "hub": "San Francisco (HQ)", "division": "AI Research", "route": "REVALIDATE", "detail": "Layer E flagged KNO-A-041 Sonnet-4.5 -> 5.5 drift; queued canary sweep"},
    {"time": "19:10:31 UTC", "hub": "London", "division": "Public Policy", "route": "REUSE", "detail": "Reused KNO-B-045 Governance Core for UK AISI alignment brief"},
]


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force_reset: bool = False):
    conn = get_db()
    cur = conn.cursor()
    if force_reset:
        for tbl in ["layer_e", "knowledge", "batons", "economics", "audit_log", "live_feed"]:
            cur.execute(f"DROP TABLE IF EXISTS {tbl}")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS layer_e (
            pred_id TEXT PRIMARY KEY, opportunity_type TEXT, target_division TEXT,
            signal_source TEXT, recommended_action TEXT, expected_value_usd REAL,
            success_prob REAL, estimated_cost_usd REAL, risk_penalty_usd REAL,
            ev_score REAL, promotion_guardrail TEXT, status TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge (
            entry_id TEXT PRIMARY KEY, layer TEXT, lifecycle_state TEXT, expiry_status TEXT,
            owner TEXT, dept TEXT, sub_dept TEXT, title TEXT, evidence_refs TEXT,
            model_version TEXT, dataset_version TEXT, environment_tag TEXT,
            historical_confidence REAL, reproducibility_score REAL, evidence_quality_score REAL,
            freshness_score REAL, independent_reviewer TEXT, limitations TEXT, last_verified TEXT,
            expiry_condition TEXT, permissions TEXT, failure_conditions TEXT, retest_triggers TEXT,
            deterministic_eligible INTEGER, summary TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS batons (
            contract_id TEXT PRIMARY KEY, from_pod TEXT, receiving_owner TEXT, objective TEXT,
            status TEXT, source_knowledge_ids TEXT, acceptance_criteria TEXT, dependencies TEXT,
            rollback_plan TEXT, deadline TEXT, evidence_manifest TEXT, budget_remaining_usd REAL,
            governance_level TEXT, escalation_reason TEXT, approval_status TEXT, receiver_ack TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id TEXT PRIMARY KEY, timestamp TEXT, actor TEXT, governance_level TEXT,
            target_id TEXT, evidence_hash TEXT, decision TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS live_feed (
            id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, hub TEXT, division TEXT, route TEXT, detail TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS economics (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            cost_inference_usd REAL, cost_retrieval_storage_usd REAL, cost_human_review_usd REAL,
            cost_experimentation_usd REAL, cost_infrastructure_usd REAL,
            tokens_counterfactual_saved INTEGER, tokens_cached_read INTEGER,
            tokens_retrieved_memory INTEGER, tokens_billed_input INTEGER, tokens_billed_output INTEGER,
            validated_outcomes INTEGER, tasks_total INTEGER, duplicate_prevented INTEGER,
            control_group_tasks INTEGER, control_group_reused INTEGER
        )
        """
    )

    if cur.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0] == 0:
        for p in SEED_LAYER_E:
            cur.execute(
                "INSERT INTO layer_e VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    p["pred_id"], p["opportunity_type"], p["target_division"], p["signal_source"],
                    p["recommended_action"], p["expected_value_usd"], p["success_prob"],
                    p["estimated_cost_usd"], p["risk_penalty_usd"], p["ev_score"],
                    p["promotion_guardrail"], p["status"],
                ),
            )
        for k in SEED_KNOWLEDGE:
            cur.execute(
                "INSERT INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    k["entry_id"], k["layer"], k["lifecycle_state"], k["expiry_status"],
                    k["owner"], k["dept"], k["sub_dept"], k["title"], json.dumps(k["evidence_refs"]),
                    k["model_version"], k["dataset_version"], k["environment_tag"],
                    k["historical_confidence"], k["reproducibility_score"],
                    k["evidence_quality_score"], k["freshness_score"], k["independent_reviewer"],
                    k["limitations"], k["last_verified"], k["expiry_condition"], k["permissions"],
                    k["failure_conditions"], k["retest_triggers"],
                    1 if k["deterministic_eligible"] else 0, k["summary"],
                ),
            )
        for b in SEED_BATONS:
            cur.execute(
                "INSERT INTO batons VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    b["contract_id"], b["from_pod"], b["receiving_owner"], b["objective"], b["status"],
                    json.dumps(b["source_knowledge_ids"]), json.dumps(b["acceptance_criteria"]),
                    json.dumps(b["dependencies"]), b["rollback_plan"], b["deadline"],
                    json.dumps(b["evidence_manifest"]), b["budget_remaining_usd"],
                    b["governance_level"], b["escalation_reason"], b["approval_status"], b["receiver_ack"],
                ),
            )
        for ev in LIVE_FEED_EVENTS:
            cur.execute(
                "INSERT INTO live_feed (time, hub, division, route, detail) VALUES (?,?,?,?,?)",
                (ev["time"], ev["hub"], ev["division"], ev["route"], ev["detail"]),
            )
        cur.execute(
            "INSERT INTO audit_log VALUES (?,?,?,?,?,?,?)",
            ("AUD-9001", "2026-11-16T09:10:00Z", "VP Infrastructure", "Level 2 · Department Leader", "BTN-8812", "sha256:9f82c1a4", "APPROVED_EXECUTION_CONTRACT"),
        )
        cur.execute(
            "INSERT INTO economics VALUES (1, 14.82, 3.40, 185.00, 62.50, 28.10, 262600, 94200, 86000, 33975, 11325, 23, 25, 19, 29, 7)"
        )

    conn.commit()
    conn.close()


init_db(force_reset=False)


def fetch_state():
    conn = get_db()
    cur = conn.cursor()

    layer_e = [dict(r) for r in cur.execute("SELECT * FROM layer_e ORDER BY ev_score DESC").fetchall()]
    knowledge = []
    for r in cur.execute("SELECT * FROM knowledge ORDER BY rowid DESC").fetchall():
        d = dict(r)
        d["evidence_refs"] = json.loads(d["evidence_refs"])
        d["deterministic_eligible"] = bool(d["deterministic_eligible"])
        knowledge.append(d)

    batons = []
    for r in cur.execute("SELECT * FROM batons ORDER BY rowid DESC").fetchall():
        d = dict(r)
        d["source_knowledge_ids"] = json.loads(d["source_knowledge_ids"])
        d["acceptance_criteria"] = json.loads(d["acceptance_criteria"])
        d["dependencies"] = json.loads(d["dependencies"])
        d["evidence_manifest"] = json.loads(d["evidence_manifest"])
        batons.append(d)

    audits = [dict(r) for r in cur.execute("SELECT * FROM audit_log ORDER BY rowid DESC LIMIT 12").fetchall()]
    feed = [dict(r) for r in cur.execute("SELECT * FROM live_feed ORDER BY id DESC LIMIT 8").fetchall()]
    eco = dict(cur.execute("SELECT * FROM economics WHERE id = 1").fetchone())
    conn.close()

    total_full_cost_usd = round(
        eco["cost_inference_usd"] + eco["cost_retrieval_storage_usd"] + eco["cost_human_review_usd"] + eco["cost_experimentation_usd"] + eco["cost_infrastructure_usd"],
        2,
    )
    cost_per_validated_outcome = round(total_full_cost_usd / max(1, eco["validated_outcomes"]), 2)
    tokens_billed_total = eco["tokens_billed_input"] + eco["tokens_billed_output"]
    reuse_rate = round((eco["duplicate_prevented"] / max(1, eco["tasks_total"])) * 100, 1)
    control_rate = round((eco["control_group_reused"] / max(1, eco["control_group_tasks"])) * 100, 1)
    canonical_count = sum(1 for k in knowledge if k["lifecycle_state"] in ("CANONICAL", "ACTIVELY_MONITORED"))
    freshness_pct = round((canonical_count / max(1, len(knowledge))) * 100, 1)

    return {
        "operating_principle": OPERATING_PRINCIPLE,
        "reconciled_totals": {
            "headcount": sum(d["headcount"] for d in DEPARTMENTS),
            "open_roles": sum(d["roles"] for d in DEPARTMENTS),
            "divisions": len(DEPARTMENTS),
            "sub_pods": sum(len(d["sub_departments"]) for d in DEPARTMENTS),
            "global_hubs": len(GLOBAL_HUBS),
        },
        "departments": DEPARTMENTS,
        "layer_e": layer_e,
        "knowledge": knowledge,
        "batons": batons,
        "live_feed": feed,
        "audit_log": audits,
        "economics": {
            **eco,
            "total_full_cost_usd": total_full_cost_usd,
            "cost_per_validated_outcome_usd": cost_per_validated_outcome,
            "tokens_billed_total": tokens_billed_total,
            "reuse_rate_pct": reuse_rate,
            "control_rate_pct": control_rate,
            "net_lift_pp": round(reuse_rate - control_rate, 1),
            "freshness_pct": freshness_pct,
        },
    }


def evaluate_compatibility_and_ev(
    dept: dict,
    matched: Optional[dict],
    target_model: str,
    target_dataset: str,
    has_permission: bool,
    task_value_usd: float,
    risk_level: int,
) -> dict:
    if not matched:
        compat = {
            "model_version": 0.0, "dataset": 0.0, "environment": 0.0,
            "evidence_quality": 0.0, "freshness": 0.0, "reproducibility": 0.0,
            "permissions": 1.0 if has_permission else 0.0,
        }
        p_success, est_cost, risk_pen = 0.72, 48.00, risk_level * 25.00
        ev = round((p_success * task_value_usd) - est_cost - risk_pen, 2)
        route = "ESCALATE" if (risk_level >= 3 or ev < 0) else "DISCOVER"
        return {
            "route": route,
            "compatibility": compat,
            "historical_confidence": 0.0,
            "present_applicability": 0.0,
            "ev_formula": {"P_S": p_success, "V": task_value_usd, "C": est_cost, "R": risk_pen, "EV": ev},
            "rationale": (
                "No prior record exists in Layers A–D; EV supports bounded DISCOVER with independent verification."
                if route == "DISCOVER"
                else "High risk or negative net EV without prior evidence; escalated for Level-3 human authorisation."
            ),
        }

    c_perm = 1.0 if (has_permission and (matched["permissions"] == "ALL_DIVISIONS_READ" or dept["id"] in ("safeguards", "ai-research", "public-policy", "legal"))) else 0.0
    c_model = 1.0 if matched["model_version"] == target_model else (0.35 if "4-5" in matched["model_version"] else 0.75)
    c_data = 1.0 if matched["dataset_version"] == target_dataset else 0.55
    c_env = 1.0
    c_evid = matched["evidence_quality_score"]
    c_repro = matched["reproducibility_score"]
    c_fresh = 0.20 if matched["expiry_status"] == "ACTIVELY_INVALIDATED" else (0.78 if matched["expiry_status"] == "DUE_FOR_REVIEW" else matched["freshness_score"])

    compat = {
        "model_version": round(c_model, 2),
        "dataset": round(c_data, 2),
        "environment": c_env,
        "evidence_quality": round(c_evid, 2),
        "freshness": round(c_fresh, 2),
        "reproducibility": round(c_repro, 2),
        "permissions": round(c_perm, 2),
    }
    present_app = round(min(c_perm, c_model, c_data, c_env, c_fresh) * ((c_evid + c_repro) / 2), 2)

    if c_perm == 0.0:
        ev = round(-5.0 - 500.0, 2)
        return {
            "route": "BLOCK",
            "compatibility": compat,
            "historical_confidence": matched["historical_confidence"],
            "present_applicability": present_app,
            "ev_formula": {"P_S": 0.0, "V": task_value_usd, "C": 5.0, "R": 500.0, "EV": ev},
            "rationale": f"Least-privilege access violation: {dept['name']} lacks permission ({matched['permissions']}) for {matched['entry_id']}.",
        }

    if matched.get("failure_conditions") and c_model == 1.0:
        ev = round((0.08 * task_value_usd) - 18.0 - 350.0, 2)
        return {
            "route": "BLOCK",
            "compatibility": compat,
            "historical_confidence": matched["historical_confidence"],
            "present_applicability": present_app,
            "ev_formula": {"P_S": 0.08, "V": task_value_usd, "C": 18.0, "R": 350.0, "EV": ev},
            "rationale": f"Blocked by Layer-D Negative Finding ({matched['entry_id']}): {matched['failure_conditions']}",
        }

    if matched["expiry_status"] == "ACTIVELY_INVALIDATED" or c_model < 0.70 or c_data < 0.70:
        p_success, est_cost, risk_pen = round(max(0.65, present_app + 0.45), 2), 32.00, risk_level * 18.00
        ev = round((p_success * task_value_usd) - est_cost - risk_pen, 2)
        route = "ESCALATE" if (risk_level >= 3 and ev < 150) else "REVALIDATE"
        return {
            "route": route,
            "compatibility": compat,
            "historical_confidence": matched["historical_confidence"],
            "present_applicability": present_app,
            "ev_formula": {"P_S": p_success, "V": task_value_usd, "C": est_cost, "R": risk_pen, "EV": ev},
            "rationale": f"Historical confidence is {int(matched['historical_confidence']*100)}%, but present applicability dropped to {int(present_app*100)}% due to drift/invalidation ({matched['expiry_status']}); minimal REVALIDATE authorised.",
        }

    p_success = round(min(0.99, present_app), 2)
    est_cost = 0.40 if matched["deterministic_eligible"] else 4.20
    risk_pen = risk_level * 4.00
    ev = round((p_success * task_value_usd) - est_cost - risk_pen, 2)
    review_note = " (Flagged DUE_FOR_REVIEW in background without blocking reuse)" if matched["expiry_status"] == "DUE_FOR_REVIEW" else ""
    return {
        "route": "REUSE",
        "compatibility": compat,
        "historical_confidence": matched["historical_confidence"],
        "present_applicability": present_app,
        "ev_formula": {"P_S": p_success, "V": task_value_usd, "C": est_cost, "R": risk_pen, "EV": ev},
        "rationale": f"High present applicability ({int(present_app*100)}%) and positive net EV (${ev:,.2f}); reusing {matched['entry_id']}{review_note}.",
    }


class GateDispatchRequest(BaseModel):
    dept_id: str
    sub_dept_id: str
    objective: str
    target_model: str = "claude-sonnet-5-5"
    target_dataset: str = "soc2-iso-2026-q4"
    task_value_usd: float = 850.0
    risk_level: int = 0
    has_permission: bool = True


@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")


@app.get("/api/state")
def api_state():
    return fetch_state()


@app.post("/api/reset")
def api_reset():
    init_db(force_reset=True)
    return fetch_state()


@app.post("/api/pulse")
def api_live_pulse():
    scenarios = [
        ("Dublin (EMEA Hub)", "Sales · RFP Desk", "REUSE", "Deterministic lookup KNO-B-044 for EU FinServ RFP (0 LLM tokens · saved 9,400t)", 9400, 0, 820, 0, 0, 0.0, 0.12, 1, 1),
        ("San Francisco (HQ)", "SWE-Infra · Gateway", "REUSE", "Provider prompt-cache hit on Tier-1 Constitution prefix (saved 4,350t)", 4350, 480, 0, 110, 65, 0.0013, 0.08, 1, 1),
        ("London", "Applied AI · Sol Arch", "REUSE", "Cloned canonical RAG blueprint from Layer B (saved 11,200t)", 11200, 520, 1400, 190, 110, 0.0022, 0.15, 1, 1),
        ("Tokyo", "PM & Support Ops", "REUSE", "Resolved Tier-2 enterprise API quota query via Layer-B runbook (saved 6,100t)", 6100, 0, 640, 0, 0, 0.0, 0.05, 1, 1),
        ("New York", "Data Science", "REUSE", "Served canonical retention cohort SQL definition (saved 7,800t)", 7800, 0, 710, 0, 0, 0.0, 0.06, 1, 1),
    ]
    hub, div, route, detail, cf_tok, cache_tok, ret_tok, b_in, b_out, inf_usd, ret_usd, val_inc, dup_inc = random.choice(scenarios)
    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO live_feed (time, hub, division, route, detail) VALUES (?,?,?,?,?)", (now_str, hub, div, route, detail))
    cur.execute(
        """
        UPDATE economics SET
            cost_inference_usd = cost_inference_usd + ?,
            cost_retrieval_storage_usd = cost_retrieval_storage_usd + ?,
            tokens_counterfactual_saved = tokens_counterfactual_saved + ?,
            tokens_cached_read = tokens_cached_read + ?,
            tokens_retrieved_memory = tokens_retrieved_memory + ?,
            tokens_billed_input = tokens_billed_input + ?,
            tokens_billed_output = tokens_billed_output + ?,
            validated_outcomes = validated_outcomes + ?,
            tasks_total = tasks_total + 1,
            duplicate_prevented = duplicate_prevented + ?
        WHERE id = 1
        """,
        (inf_usd, ret_usd, cf_tok, cache_tok, ret_tok, b_in, b_out, val_inc, dup_inc),
    )
    conn.commit()
    conn.close()
    return fetch_state()


@app.post("/api/layer-e/{pred_id}/convert")
def api_convert_prediction(pred_id: str):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM layer_e WHERE pred_id = ?", (pred_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Prediction not found")

    p = dict(row)
    contract_id = f"BTN-{uuid.uuid4().hex[:4].upper()}"
    cur.execute(
        "INSERT INTO batons VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            contract_id, "Layer E · Predictive Opportunity Engine", p["target_division"], p["recommended_action"],
            "PENDING_VERIFICATION", json.dumps([pred_id]),
            json.dumps([
                "Controlled A/B test demonstrates >= 0% quality regression",
                "Independent reviewer verifies token/cost delta",
                "Human Division Leader approves promotion to Layer B CANONICAL",
            ]),
            json.dumps(["Shadow traffic replay", "Independent eval harness"]),
            "Disable proposed workflow rule and revert to prior baseline routing immediately.",
            "2026-11-20T17:00:00Z", json.dumps([f"layer_e://{pred_id}/proposal.json"]),
            round(p["estimated_cost_usd"], 2), "level_2_dept_leader",
            f"Layer E recommendation ({pred_id}) cannot self-promote; routed as governed execution contract.",
            "AWAITING_APPROVAL", "PENDING_ACK",
        ),
    )
    cur.execute("UPDATE layer_e SET status = 'CONVERTED_TO_CONTRACT' WHERE pred_id = ?", (pred_id,))
    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    cur.execute(
        "INSERT INTO live_feed (time, hub, division, route, detail) VALUES (?,?,?,?,?)",
        (now_str, "Global Control Plane", p["target_division"], "DISCOVER", f"Converted {pred_id} into Execution Contract {contract_id}"),
    )
    conn.commit()
    conn.close()
    return fetch_state()


@app.post("/api/dispatch")
def api_dispatch(req: GateDispatchRequest):
    state = fetch_state()
    dept = next((d for d in DEPARTMENTS if d["id"] == req.dept_id), DEPARTMENTS[0])
    sub = next((s for s in dept["sub_departments"] if s["id"] == req.sub_dept_id), dept["sub_departments"][0])
    obj_lower = req.objective.lower()

    matched = None
    for k in state["knowledge"]:
        if (
            (any(w in obj_lower for w in ["kv", "cache", "quant", "200k"]) and "KV-Cache" in k["title"])
            or (any(w in obj_lower for w in ["bert", "jailbreak", "biosecurity", "filter"]) and "BERT" in k["title"])
            or (any(w in obj_lower for w in ["rfp", "soc2", "hipaa", "zdr", "security pack"]) and "RFP" in k["title"])
            or (any(w in obj_lower for w in ["eu ai act", "nist", "regulatory", "policy"]) and "Governance Core" in k["title"])
            or k["dept"] == dept["name"]
        ):
            matched = k
            break

    gate_eval = evaluate_compatibility_and_ev(
        dept, matched, req.target_model, req.target_dataset, req.has_permission, req.task_value_usd, req.risk_level
    )
    route = gate_eval["route"]

    inf_usd, ret_usd, hum_usd, exp_usd, infra_usd = 0.0, 0.15, 0.0, 0.0, 0.45
    cf_saved_tok, cached_tok, retrieved_tok, bill_in, bill_out = 0, 0, 0, 0, 0
    val_inc, dup_inc = 0, 0

    conn = get_db()
    cur = conn.cursor()

    if route == "REUSE" and matched:
        retrieved_tok = estimate_tokens(matched["summary"])
        cf_saved_tok = 9400
        dup_inc = 1
        val_inc = 1
        if not matched["deterministic_eligible"]:
            cached_tok, bill_in, bill_out, inf_usd = 420, 140, 90, 0.0018
        source_ids = [matched["entry_id"]]
        ev_manifest = matched["evidence_refs"]
    elif route in ("REVALIDATE", "DISCOVER"):
        cached_tok, bill_in, bill_out = 520, 480, 260
        inf_usd = 0.0055 if req.target_model == "claude-sonnet-5-5" else 0.0270
        exp_usd, hum_usd, val_inc = 14.50, 22.00, 1
        new_id = f"KNO-{'A' if route == 'DISCOVER' else 'B'}-{len(state['knowledge']) + 41:03d}"
        finding_text = f"[{route}] {sub['name']} executed bounded experiment on {req.target_model}; awaiting independent verification before CANONICAL promotion."
        source_ids = [matched["entry_id"], new_id] if matched else [new_id]
        ev_manifest = [f"artifact://{new_id.lower()}/verified_run.json"]

        cur.execute(
            "INSERT INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                new_id, "A · Research & Experiment Memory", "UNDER_VALIDATION", "CURRENT",
                f"{sub['name']} Pod", dept["name"], sub["name"], req.objective[:76],
                json.dumps(ev_manifest), req.target_model, req.target_dataset, "trainium2-kernel-2.14",
                0.92, 0.94, 0.93, 1.00, f"{dept['director']} (Independent Verifier)",
                f"Scoped to {req.target_model}.", datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "Revalidate upon next model generation or dataset bump.", "ALL_DIVISIONS_READ",
                None, None, 0, finding_text,
            ),
        )
    else:
        hum_usd = 15.00 if route == "ESCALATE" else 0.0
        source_ids = [matched["entry_id"]] if matched else ["NONE"]
        ev_manifest = matched["evidence_refs"] if matched else ["policy://ev-gate-block"]

    contract_id = f"BTN-{uuid.uuid4().hex[:4].upper()}"
    eff_risk = max(dept["base_risk"], req.risk_level, 2 if route in ("DISCOVER", "REVALIDATE", "ESCALATE") else 0)
    gov_label = (
        "level_0_autonomous" if eff_risk == 0
        else ("level_1_ai_director" if eff_risk == 1
              else ("level_2_dept_leader" if eff_risk == 2 else "level_3_human_authority"))
    )
    esc_reason = (
        f"Base Level {dept['base_risk']} -> Effective Level {eff_risk} for route {route}"
        if eff_risk > dept["base_risk"]
        else f"Aligned with {dept['name']} Level {dept['base_risk']} charter"
    )

    cur.execute(
        "INSERT INTO batons VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            contract_id, f"{dept['name']} · {sub['name']}", f"Independent Verifier ({dept['director']})",
            req.objective[:84], "BLOCKED" if route == "BLOCK" else ("AWAITING_VERIFICATION" if route != "REUSE" else "READY_FOR_HANDOFF"),
            json.dumps(source_ids),
            json.dumps([f"Compatibility >= 0.85 on {req.target_model}", "Evidence hash verified against immutable artifact store"]),
            json.dumps([req.target_dataset]), f"Revert {sub['name']} workflow to prior validated baseline ({source_ids[0]}).",
            "2026-11-19T17:00:00Z", json.dumps(ev_manifest), round(max(0.0, gate_eval["ev_formula"]["C"]), 2),
            gov_label, esc_reason, "AUTO_APPROVED" if eff_risk == 0 else "AWAITING_APPROVAL", "PENDING_ACK",
        ),
    )

    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    primary_hub = dept["hubs"].split(",")[0].strip()
    cur.execute(
        "INSERT INTO live_feed (time, hub, division, route, detail) VALUES (?,?,?,?,?)",
        (now_str, primary_hub, f"{dept['name']} · {sub['name']}", route, f"{req.objective[:68]} (EV: ${gate_eval['ev_formula']['EV']})"),
    )

    cur.execute(
        """
        UPDATE economics SET
            cost_inference_usd = cost_inference_usd + ?, cost_retrieval_storage_usd = cost_retrieval_storage_usd + ?,
            cost_human_review_usd = cost_human_review_usd + ?, cost_experimentation_usd = cost_experimentation_usd + ?,
            cost_infrastructure_usd = cost_infrastructure_usd + ?, tokens_counterfactual_saved = tokens_counterfactual_saved + ?,
            tokens_cached_read = tokens_cached_read + ?, tokens_retrieved_memory = tokens_retrieved_memory + ?,
            tokens_billed_input = tokens_billed_input + ?, tokens_billed_output = tokens_billed_output + ?,
            validated_outcomes = validated_outcomes + ?, tasks_total = tasks_total + 1, duplicate_prevented = duplicate_prevented + ?
        WHERE id = 1
        """,
        (inf_usd, ret_usd, hum_usd, exp_usd, infra_usd, cf_saved_tok, cached_tok, retrieved_tok, bill_in, bill_out, val_inc, dup_inc),
    )
    conn.commit()
    conn.close()
    return {"gate_eval": gate_eval, "contract_id": contract_id, "state": fetch_state()}


@app.post("/api/baton/{contract_id}/ack")
def api_ack_baton(contract_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE batons SET receiver_ack = 'ACKNOWLEDGED' WHERE contract_id = ?", (contract_id,))
    conn.commit()
    conn.close()
    return fetch_state()


@app.post("/api/baton/{contract_id}/approve")
def api_approve_baton(contract_id: str):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT governance_level, source_knowledge_ids FROM batons WHERE contract_id = ?", (contract_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Execution contract not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "UPDATE batons SET approval_status = ?, status = 'VERIFIED_&_COMPLETE' WHERE contract_id = ?",
        (f"APPROVED ({row['governance_level']} · {now_iso[:16]}Z)", contract_id),
    )
    for kid in json.loads(row["source_knowledge_ids"]):
        cur.execute(
            "UPDATE knowledge SET lifecycle_state = 'CANONICAL', expiry_status = 'CURRENT', last_verified = ? WHERE entry_id = ? AND lifecycle_state = 'UNDER_VALIDATION'",
            (now_iso[:10], kid),
        )
    cur.execute(
        "INSERT INTO audit_log VALUES (?,?,?,?,?,?,?)",
        (
            f"AUD-{uuid.uuid4().hex[:4].upper()}", now_iso, "Independent Verifier & Governance Lead",
            row["governance_level"], contract_id, f"sha256:{uuid.uuid4().hex[:8]}", "APPROVED_&_PROMOTED_CANONICAL",
        ),
    )
    cur.execute(
        "INSERT INTO live_feed (time, hub, division, route, detail) VALUES (?,?,?,?,?)",
        (datetime.now(timezone.utc).strftime("%H:%M:%S UTC"), "Global Control Plane", "Governance Audit", "REUSE", f"Contract {contract_id} verified & promoted to CANONICAL"),
    )
    conn.commit()
    conn.close()
    return fetch_state()