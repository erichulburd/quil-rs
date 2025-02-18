import pickle
import pytest
from typing import Optional

from syrupy.assertion import SnapshotAssertion

from quil.program import Program
from quil.instructions import Instruction, QubitPlaceholder, TargetPlaceholder, Gate, Qubit, Jump, Target


def test_pickle():
    program = Program.parse(
        """
DECLARE ro BIT[2]
H 0
CNOT 0 1
MEASURE 0 ro[0]
MEASURE 1 ro[1]
"""
    )
    pickled = pickle.dumps(program)
    unpickled = pickle.loads(pickled)
    assert program == unpickled


def test_custom_resolver():
    qubit_placeholder = QubitPlaceholder()

    def qubit_resolver(qubit: QubitPlaceholder) -> Optional[int]:
        return {qubit_placeholder: 9}.get(qubit)

    target_placeholder = TargetPlaceholder("base-target")

    def target_resolver(target: TargetPlaceholder) -> Optional[str]:
        print("resolving target", target)
        return {target_placeholder: "test"}.get(target)

    program = Program()
    program.add_instructions(
        [
            Instruction.from_gate(Gate("H", [], [Qubit.from_placeholder(qubit_placeholder)], [])),
            Instruction.from_jump(Jump(Target.from_placeholder(target_placeholder))),
        ]
    )

    with pytest.raises(ValueError):
        program.to_quil()

    program.resolve_placeholders_with_custom_resolvers(target_resolver=target_resolver, qubit_resolver=qubit_resolver)

    print(program.to_quil_or_debug())

    assert program.to_quil() == "H 9\nJUMP @test\n"


def test_filter_instructions(snapshot: SnapshotAssertion):
    input = """DECLARE foo REAL[1]
DEFFRAME 1 "rx":
\tHARDWARE-OBJECT: "hardware"
DEFCAL I 1:
\tDELAY 0 1
DEFGATE BAR AS MATRIX:
\t0, 1
\t1, 0

H 1
CNOT 2 3
"""
    program = Program.parse(input)
    program_without_quil_t = program.filter_instructions(lambda instruction: not instruction.is_quil_t())
    assert program_without_quil_t.to_quil() == snapshot
