from __future__ import annotations
from pathlib import Path
import yaml
from pydantic import BaseModel, Field

DEFAULT_ECW: dict[str, float] = {
    "EXP": 1.0, "IDA": 1.0, "IPI": 1.0, "IMP": 1.0, "IGI": 1.0, "IEP": 1.0,
    "ISS": 0.8, "ISA": 0.8, "ISM": 0.8, "ISO": 0.8, "IBA": 0.8,
    "TAS": 1.0, "NAS": 0.7, "IC": 0.8, "IEA": 0.7, "ND": 0.0,
}


class AnnotationParams(BaseModel):
    evalue_hit_filter: float = 1.0e-6
    annotation_cutoff: float = 55
    go_weight: float = 5
    hsp_coverage: float = 0.0
    num_hits: int = 20
    ecw: dict[str, float] = Field(default_factory=lambda: dict(DEFAULT_ECW))


class Config(BaseModel):
    query_fasta: str
    diamond_tsv: str
    cache_dir: str
    out_dir: str
    interpro_tsv: str | None = None
    annotation: AnnotationParams = Field(default_factory=AnnotationParams)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        data = yaml.safe_load(Path(path).read_text())
        return cls.model_validate(data)
