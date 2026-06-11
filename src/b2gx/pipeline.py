from __future__ import annotations
from pathlib import Path
import polars as pl
from b2gx.config import AnnotationParams
from b2gx.model import SequenceAnnotation, Hit
from b2gx.refdata.godag import GODag
from b2gx.stages.mapping import map_candidates, Coverage
from b2gx.stages.annotation import annotate_sequence
from b2gx.stages.interpro import merge_interpro
from b2gx.stages.eckegg import assign_ec, assign_kegg


def run_pipeline(
    hits: pl.DataFrame,
    index_parquet: str | Path,
    dag: GODag,
    params: AnnotationParams,
    ec2go: dict[str, set[str]] | None = None,
    acc2ko: dict[str, str] | None = None,
    ko2path: dict[str, list[str]] | None = None,
    interpro_by_seq: dict[str, set[str]] | None = None,
) -> tuple[list[SequenceAnnotation], Coverage]:
    ec2go = ec2go or {}
    acc2ko = acc2ko or {}
    ko2path = ko2path or {}
    interpro_by_seq = interpro_by_seq or {}

    cand_by_seq, coverage = map_candidates(hits, index_parquet, params)

    subj_by_seq: dict[str, list[str]] = {}
    for row in hits.iter_rows(named=True):
        subj_by_seq.setdefault(row["qseqid"], []).append(row["sseqid"])

    anns: list[SequenceAnnotation] = []
    for seq_id, cands in cand_by_seq.items():
        assigned = annotate_sequence(cands, dag, params)
        if seq_id in interpro_by_seq:
            assigned = merge_interpro(assigned, interpro_by_seq[seq_id])
        go_ids = [a.go_id for a in assigned]
        ec = assign_ec(go_ids, ec2go)
        ko, paths = assign_kegg(subj_by_seq.get(seq_id, []), acc2ko, ko2path)
        anns.append(SequenceAnnotation(
            seq_id=seq_id,
            assigned_gos=assigned,
            ec=ec, kegg_ko=ko, kegg_pathways=paths,
            interpro=sorted(interpro_by_seq.get(seq_id, set())),
        ))
    return anns, coverage
