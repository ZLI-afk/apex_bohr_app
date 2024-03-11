from dp.launching.cli import (
    SubParser,
    default_minimal_exception_handler,
    run_sp_and_exit,
)

from lmp_model import LammpsModel
from lmp_runner import lmp_runner
from vasp_model import VaspModel
from vasp_runner import vasp_runner
from abacus_model import AbacusModel
from abacus_runner import abacus_runner


def to_parser():
    return {
        "LAMMPS": SubParser(LammpsModel, lmp_runner, "Submit MD workflow using LAMMPS"),
        "VASP": SubParser(VaspModel, vasp_runner, "Submit DFT workflow using VASP"),
        "ABACUS": SubParser(AbacusModel, abacus_runner, "Submit DFT workflow using ABACUS"),
    }


def main():
    # excute APEX app main flow
    run_sp_and_exit(
        to_parser(),
        description="APEX workflow submission",
        version="1.2.0",
        exception_handler=default_minimal_exception_handler,
    )


if __name__ == "__main__":
    main()