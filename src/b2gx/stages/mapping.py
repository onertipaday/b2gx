from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import polars as pl
from b2gx.config import AnnotationParams
from b2gx.model import CandidateGO
from b2gx.refdata.lookups import query_go


@dataclass(frozen=True)
class Coverage:
    n_subjects: int
    n_resolved: int

    @property
    def resolved_fraction(self) -> float:
        return self.n_resolved / self.n_subjects if self.n_subjects else 0.0


def map_candidates(
    hits: pl.DataFrame, index_parquet: str | Path, params: AnnotationParams
) -> tuple[dict[str, list[CandidateGO]], Coverage]:
    filtered = (
        hits.filter(pl.col("evalue") <= params.evalue_hit_filter)
        .filter(pl.col("qcovhsp") >= params.hsp_coverage * 100.0)
        .sort("evalue")
        .group_by("qseqid", maintain_order=True)
        .head(params.num_hits)
    )

    subjects = filtered["sseqid"].unique().to_list()
    if not subjects:
        return {}, Coverage(n_subjects=0, n_resolved=0)
    go_map = query_go(index_parquet, subjects)  # (refseq, go_id)
    resolved_subjects = set(go_map["refseq"].unique().to_list())

    joined = filtered.join(
        go_map.rename({"refseq": "sseqid"}), on="sseqid", how="inner"
    )

    cand_by_seq: dict[str, list[CandidateGO]] = {}
    for row in joined.iter_rows(named=True):
        cand_by_seq.setdefault(row["qseqid"], []).append(
            CandidateGO(go_id=row["go_id"], evidence="IEA",
                        sseqid=row["sseqid"], similarity=row["ppos"])
        )

    coverage = Coverage(n_subjects=len(subjects), n_resolved=len(resolved_subjects))
    return cand_by_seq, coverage
