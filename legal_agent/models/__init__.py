"""
Core Pydantic models for the legal contract agent system.

These are the canonical data structures that flow through the supervisor graph.
Every agent reads from and writes to these models. No agent mutates in-place;
each produces a new version for auditability.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field


# ─────────────────────────────────────────────────────
# Enums & constants
# ─────────────────────────────────────────────────────

class ContractType(str, Enum):
    """Recognized contract types."""
    NDA = "NDA"
    NDA_MUTUAL = "NDA_MUTUAL"
    MSA = "MSA"
    SOW = "SOW"
    DPA = "DPA"
    SAAS = "SAAS"
    EMPLOYMENT = "EMPLOYMENT"
    INDEPENDENT_CONTRACTOR = "INDEPENDENT_CONTRACTOR"
    PARTNERSHIP = "PARTNERSHIP"
    LICENSING = "LICENSING"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    LEASE = "LEASE"
    OTHER = "OTHER"


class Severity(str, Enum):
    """Deviation severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKER = "blocker"


class RiskCategory(str, Enum):
    """Risk sub-score categories."""
    FINANCIAL = "financial"
    IP = "ip"
    DATA = "data"
    OPERATIONAL = "operational"
    EXIT = "exit"


class HITLStatus(str, Enum):
    """Human-in-the-loop queue status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    TIMED_OUT = "timed_out"


class ContractStatus(str, Enum):
    """Lifecycle status of a contract."""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    NEGOTIATING = "negotiating"
    EXECUTED = "executed"
    TERMINATED = "terminated"
    EXPIRED = "expired"


# ─────────────────────────────────────────────────────
# Grounding / source location
# ─────────────────────────────────────────────────────

class SourceLocation(BaseModel):
    """Exact location of a clause/term in the source document.

    Every claim emitted by any agent MUST carry a SourceLocation.
    Phantom citations are blocked at the output layer by verifying
    that the page and section_ref exist in the parsed Contract.
    """

    page: int = Field(ge=1, description="1-based page number in source document")
    section_ref: str | None = Field(
        default=None,
        description="Section heading or identifier, e.g. 'Section 4.2'",
    )
    bounding_box: tuple[float, float, float, float] | None = Field(
        default=None,
        description="(x0, y0, x1, y1) in points from top-left of page",
    )
    text_snippet: str | None = Field(
        default=None,
        max_length=500,
        description="Up to 500 chars of the source text at this location",
    )

    @computed_field  # type: ignore[misc]
    @property
    def citation(self) -> str:
        """Human-readable citation string."""
        parts: list[str] = [f"p.{self.page}"]
        if self.section_ref:
            parts.append(self.section_ref)
        return " · ".join(parts)


# ─────────────────────────────────────────────────────
# Clause
# ─────────────────────────────────────────────────────

class Clause(BaseModel):
    """A single clause / section within a contract."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    heading: str = Field(description="Section heading, e.g. '4.2 Confidentiality'")
    text: str = Field(description="Full text of the clause")
    level: int = Field(default=1, ge=1, le=5, description="Heading depth (1 = top-level)")
    source_location: SourceLocation | None = Field(default=None)
    clause_type: str | None = Field(
        default=None,
        description="Normalized type, e.g. 'confidentiality', 'indemnification'",
    )
    defined_terms: list[str] = Field(
        default_factory=list,
        description="Defined terms found in this clause (e.g. 'Confidential Information')",
    )
    cross_references: list[str] = Field(
        default_factory=list,
        description="Section refs found in this clause (e.g. 'Section 7.1')",
    )

    # Redline tracking
    is_modified: bool = Field(default=False, description="True if this clause has tracked changes")
    original_text: str | None = Field(
        default=None,
        description="Pre-redline text for diff comparison",
    )


# ─────────────────────────────────────────────────────
# Party
# ─────────────────────────────────────────────────────

class Party(BaseModel):
    """A contracting party."""

    name: str = Field(description="Legal entity name")
    role: str = Field(
        default="party",
        description="Role: 'disclosing', 'receiving', 'buyer', 'seller', 'employer', etc.",
    )
    address: str | None = None
    signatory_name: str | None = Field(default=None, description="Person signing")
    signatory_title: str | None = None
    source_location: SourceLocation | None = None

    @computed_field  # type: ignore[misc]
    @property
    def short_name(self) -> str:
        """Abbreviated name for internal use."""
        return self.name.split(",")[0].split("LLC")[0].split("Inc")[0].split("Corp")[0].strip()


# ─────────────────────────────────────────────────────
# Contract (the root object)
# ─────────────────────────────────────────────────────

class Contract(BaseModel):
    """Canonical representation of a parsed contract.

    This is the central object that flows through the supervisor graph.
    No agent mutates it in-place — each produces a new version.
    """

    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Source metadata
    source_filename: str = Field(description="Original uploaded filename")
    source_hash: str = Field(description="SHA-256 of the source file (for dedup)")
    file_type: str = Field(description="MIME-ish type: 'pdf', 'docx', 'image/png', 'email'")

    # Classification
    contract_type: ContractType | None = Field(
        default=None,
        description="Classified contract type",
    )
    type_confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    # Content
    title: str | None = Field(default=None, description="Contract title from document")
    effective_date: datetime | None = Field(default=None)
    parties: list[Party] = Field(default_factory=list)
    clauses: list[Clause] = Field(default_factory=list)
    defined_terms: dict[str, str] = Field(
        default_factory=dict,
        description="Map: defined term → definition text",
    )

    # Full extracted text (for long-context LLM calls)
    full_text: str = Field(default="", description="Complete extracted text of the contract")

    # Lifecycle
    status: ContractStatus = Field(default=ContractStatus.DRAFT)
    executed_date: datetime | None = None

    # PII hashing for audit logs
    @computed_field  # type: ignore[misc]
    @property
    def fingerprint(self) -> str:
        """Short hash for identifying this contract in logs without leaking PII."""
        data = f"{self.source_hash}{self.source_filename}".encode()
        return hashlib.sha256(data).hexdigest()[:12]

    # Verification helpers
    def has_section(self, section_ref: str) -> bool:
        """Check if a section reference exists in this contract.

        Used by the hallucination guardrail to verify clause references
        before emitting them.
        """
        return any(section_ref.lower() in c.heading.lower() for c in self.clauses)

    def find_clause_by_type(self, clause_type: str) -> Clause | None:
        """Find the first clause matching the given normalized type."""
        for clause in self.clauses:
            if clause.clause_type == clause_type:
                return clause
        return None

    def find_clause_by_ref(self, section_ref: str) -> Clause | None:
        """Find a clause by its section reference."""
        for clause in self.clauses:
            if section_ref.lower() in clause.heading.lower():
                return clause
        return None


# ─────────────────────────────────────────────────────
# TermSheet
# ─────────────────────────────────────────────────────

class MaterialTerm(BaseModel):
    """A single extracted material term."""

    name: str = Field(description="Term name, e.g. 'term_length', 'governing_law'")
    value: Any = Field(description="Extracted value (string, date, amount, boolean, etc.)")
    unit: str | None = Field(default=None, description="Unit for numeric values: 'years', 'USD', etc.")
    source_location: SourceLocation | None = Field(default=None)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: str | None = Field(default=None, description="Extractor notes / caveats")


class RiskScore(BaseModel):
    """Explainable risk sub-score."""

    category: RiskCategory
    score: float = Field(ge=0.0, le=1.0, description="0 = no risk, 1 = maximum risk")
    rationale: str = Field(description="Why this score was assigned")
    contributing_terms: list[str] = Field(
        default_factory=list,
        description="Term names that drove this score",
    )


class TermSheet(BaseModel):
    """Structured extraction of all material terms from a contract."""

    contract_id: str = Field(description="FK to Contract.id")

    # Core terms (populated by AnalysisAgent)
    terms: dict[str, MaterialTerm] = Field(default_factory=dict)

    # Missing-but-expected clauses
    missing_clauses: list[str] = Field(
        default_factory=list,
        description="Clause types expected for this contract_type but absent",
    )

    # Unusual / aggressive terms flagged
    unusual_terms: list[str] = Field(
        default_factory=list,
        description="Terms flagged as unusual or aggressive",
    )

    # Risk scoring
    risk_scores: list[RiskScore] = Field(default_factory=list)

    @computed_field  # type: ignore[misc]
    @property
    def overall_risk(self) -> float:
        """Weighted average of sub-scores."""
        if not self.risk_scores:
            return 0.0
        weights = {
            RiskCategory.FINANCIAL: 0.30,
            RiskCategory.IP: 0.25,
            RiskCategory.DATA: 0.20,
            RiskCategory.OPERATIONAL: 0.15,
            RiskCategory.EXIT: 0.10,
        }
        total = 0.0
        weight_sum = 0.0
        for rs in self.risk_scores:
            w = weights.get(rs.category, 0.1)
            total += rs.score * w
            weight_sum += w
        return total / weight_sum if weight_sum > 0 else 0.0


# ─────────────────────────────────────────────────────
# Deviation
# ─────────────────────────────────────────────────────

class Deviation(BaseModel):
    """A deviation from the user's playbook position."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    contract_id: str
    term_name: str = Field(description="Which term deviates, e.g. 'indemnification_cap'")

    # What we found vs what the playbook wants
    extracted_value: Any = Field(description="What the contract says")
    playbook_ideal: Any = Field(description="What the playbook wants")
    playbook_acceptable: Any | None = Field(
        default=None,
        description="Playbook's walk-away / acceptable range",
    )

    # Classification
    severity: Severity = Field(description="Severity from playbook matching")
    explanation: str = Field(
        description="Business-language explanation of the deviation",
    )
    fallback_position: str | None = Field(
        default=None,
        description="Suggested fallback language",
    )

    # Grounding
    source_location: SourceLocation | None = None

    # HITL
    requires_approval: bool = Field(
        default=False,
        description="True for blocker deviations",
    )

    # Suggested redline (populated by RedlineAgent)
    suggested_redline: str | None = None


# ─────────────────────────────────────────────────────
# Redline
# ─────────────────────────────────────────────────────

class RedlineClause(BaseModel):
    """A single clause's redline (insertions/deletions)."""

    clause_id: str = Field(description="FK to Clause.id")
    original_text: str = Field(description="Text before redline")
    revised_text: str = Field(description="Text after redline")
    changes: list[dict[str, str]] = Field(
        default_factory=list,
        description='List of {type: "insert"|"delete", text: "..."} for Word XML marks',
    )
    comment: str | None = Field(
        default=None,
        description="Clause-level comment explaining the change",
    )
    source_location: SourceLocation | None = None


class Redline(BaseModel):
    """A generated redline document."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    contract_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    clause_redlines: list[RedlineClause] = Field(default_factory=list)

    # Cover email
    cover_email_text: str | None = Field(default=None)

    # Output file path
    output_path: str | None = Field(default=None, description="Path to generated .docx")

    # HITL
    requires_human_approval: bool = Field(
        default=False,
        description="True if any clause touches indemnification/liability/IP/governing_law",
    )
    approved_by: str | None = None
    approved_at: datetime | None = None


# ─────────────────────────────────────────────────────
# Obligation
# ─────────────────────────────────────────────────────

class Obligation(BaseModel):
    """A post-signing obligation with a date."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    contract_id: str

    obligation_type: str = Field(
        description="Type: 'payment', 'renewal', 'termination_notice', 'audit', 'deliverable', 'reporting'",
    )
    description: str = Field(description="Human-readable description of the obligation")
    due_date: datetime = Field(description="When this obligation is due")
    lead_time_days: int = Field(
        default=30,
        description="Days before due_date to alert the user",
    )
    recurring: bool = Field(default=False, description="True if this repeats (e.g. annual audit)")
    recurring_interval: str | None = Field(
        default=None,
        description="'yearly', 'quarterly', 'monthly', etc.",
    )

    # Grounding
    source_location: SourceLocation | None = None

    # Status
    is_completed: bool = False
    completed_at: datetime | None = None
    dismissed: bool = Field(default=False, description="User dismissed this alert")


# ─────────────────────────────────────────────────────
# HITL Queue Item
# ─────────────────────────────────────────────────────

class HITLItem(BaseModel):
    """An item in the human-in-the-loop approval queue."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    contract_id: str
    agent_name: str = Field(description="Which agent created this item")
    stage: str = Field(description="Which pipeline stage")
    item_type: str = Field(description="'deviation', 'redline', 'classification'")
    item_data: dict[str, Any] = Field(description="Serializable representation of the item")
    reason: str = Field(description="Why human approval is needed")
    status: HITLStatus = Field(default=HITLStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None


# ─────────────────────────────────────────────────────
# Playbook models
# ─────────────────────────────────────────────────────

class PlaybookPosition(BaseModel):
    """A single playbook position for one term."""

    term_name: str = Field(description="Term this position applies to")
    ideal: Any = Field(description="Ideal / first-preference position")
    acceptable: Any | None = Field(default=None, description="Acceptable / walk-away position")
    walk_away: Any | None = Field(default=None, description="Deal-breaker position")
    severity_map: dict[str, Severity] = Field(
        default_factory=dict,
        description="Map: extracted value pattern → severity",
    )
    fallback_language: str | None = Field(default=None, description="Suggested fallback clause text")
    notes: str | None = Field(default=None)
    # Conditional logic for complex positions
    condition: str | None = Field(
        default=None,
        description="CEPL-like expression, e.g. 'counterparty_tier == enterprise and deal_value > 500000'",
    )


class Playbook(BaseModel):
    """A user's negotiated playbook — their standards for contract review."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    name: str = Field(description="Playbook name, e.g. 'Acme Corp Standard Positions'")
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Positions indexed by contract_type, then term_name
    # Top-level key: contract type (or '*' for all)
    # Second-level key: term name
    positions: dict[str, dict[str, PlaybookPosition]] = Field(default_factory=dict)

    # Expected clause types per contract type
    expected_clauses: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Map: contract_type → list of expected clause_type values",
    )

    def get_position(self, contract_type: str, term_name: str) -> PlaybookPosition | None:
        """Look up a playbook position, falling back to '*' (all-types) position."""
        type_positions = self.positions.get(contract_type, {})
        if term_name in type_positions:
            return type_positions[term_name]
        all_positions = self.positions.get("*", {})
        return all_positions.get(term_name)
