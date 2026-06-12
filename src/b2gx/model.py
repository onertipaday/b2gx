from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class Hit:
    sseqid: str
    ppos: float
    evalue: float
    bitscore: float
    hsp_cov: float


@dataclass(frozen=True)
class CandidateGO:
    go_id: str
    evidence: str
    sseqid: str
    similarity: float


@dataclass(frozen=True)
class GOAssignment:
    go_id: str
    source: Literal["blast", "interpro"]
    evidence: str
    score: float | None


@dataclass
class SequenceAnnotation:
    seq_id: str
    hits: list[Hit] = field(default_factory=list)
    candidate_gos: list[CandidateGO] = field(default_factory=list)
    assigned_gos: list[GOAssignment] = field(default_factory=list)
    interpro: list[str] = field(default_factory=list)
    ec: list[str] = field(default_factory=list)
    kegg_ko: list[str] = field(default_factory=list)
    kegg_pathways: list[str] = field(default_factory=list)
    top_hit_desc: str | None = None
