import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Literal

BASE_DIR = Path(__file__).parent  # where register.py is located
EXPERIMENTS_DIR = BASE_DIR / "experiments"

@dataclass
class TemplateMeta:
    templateID: str
    backend: Literal["chaos-mesh", "chaosd", "custom"]
    template_path: str # Path relative to the experiments/ directory

def load_registry() -> Dict[str, TemplateMeta]:
    index_path = EXPERIMENTS_DIR / "index.yaml"
    data = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    registry: Dict[str, TemplateMeta] = {}

    for item in data.get("templates", []):
        meta = TemplateMeta(
            templateID=item["templateID"],
            backend=item["backend"],
            template_path=item["path"],
        )
        registry[meta.templateID] = meta

    return registry

TEMPLATE_REGISTRY = load_registry()