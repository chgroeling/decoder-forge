from decoder_forge.bit_pattern import BitPattern
from dataclasses import dataclass
from typing import Any


@dataclass(eq=True, frozen=True)
class OpsDef:
    name: str
    dest: str
    op: str
    args: list[Any]


class AssociatedOpsRepo:

    def __init__(
        self,
        ops: list[OpsDef],
        pat_to_ops: dict[BitPattern, list[OpsDef]],
    ):

        self.ops = ops
        self.pat_to_ops = pat_to_ops

    def __repr__(self) -> str:
        return (
            "AssociatedOpsRepo("
            + f"ops={repr(self.ops)} "
            + f"pat_to_ops={repr(self.pat_to_ops)}"
            + ")"
        )

    @staticmethod
    def build(
        ops_def: dict[str, dict[str, Any]],
        pat_repo: dict[BitPattern, dict[str, str]],
    ):

        # Read all ops
        name_to_op = {
            name: OpsDef(name=name, dest=i["dest"], op=i["op"], args=i["args"])
            for name, i in ops_def.items()
        }

        def get_ops_or_empty(pat_data: dict[str, str]):
            if "ops" not in pat_data:
                return []
            return pat_data["ops"]

        pat_to_ops = {
            pat: [name_to_op[j] for j in get_ops_or_empty(pat_data)]
            for pat, pat_data in pat_repo.items()
        }

        return AssociatedOpsRepo(ops=list(name_to_op.values()), pat_to_ops=pat_to_ops)
