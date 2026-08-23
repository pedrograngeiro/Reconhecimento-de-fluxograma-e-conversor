import subprocess
import sys


def test_importing_main_module_has_no_side_effects():
    result = subprocess.run(
        [sys.executable, "-c", "import flowchart_converter.__main__"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
