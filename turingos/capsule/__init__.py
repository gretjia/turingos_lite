"""P4: Work Capsule compiler + shield + broadcast + variants per charter section 12, 3.3, 3.7, 3.8, 1.5, FC-A05/08.

Exports for integration after WorkOrder -> WorkCapsuleBuilt (visible + private_contract in CAS).
Shield minimizes context/hides predicates for worker-visible.
Broadcast reducer turns failure into rules + next shield variant.
Variants support shield evolution in failure feedback loop.
"""

from .compiler import compile_work_capsule
from .shield import apply_shield, compile_shield
from .broadcast import broadcast_failure
from .variants import get_shield_variant

__all__ = [
    "compile_work_capsule",
    "apply_shield",
    "compile_shield",
    "broadcast_failure",
    "get_shield_variant",
]
