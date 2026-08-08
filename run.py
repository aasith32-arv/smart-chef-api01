import os
import sys
from pathlib import Path


def use_local_virtualenv():
    """Re-run the development entry point with the local virtual environment."""
    if sys.prefix != sys.base_prefix:
        return

    project_dir = Path(__file__).resolve().parent
    candidates = (
        project_dir / ".venv" / "bin" / "python",
        project_dir / ".venv" / "Scripts" / "python.exe",
    )
    for interpreter in candidates:
        if interpreter.is_file():
            os.execv(
                str(interpreter),
                [str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]],
            )


if __name__ == "__main__":
    use_local_virtualenv()


from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
