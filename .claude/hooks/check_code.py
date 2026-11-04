"""
Claude Code PostToolUse hook: format, lint and type-check after a source file is edited.

- Python: ruff format and ruff check on the file, then mypy on the package.
- C++ (.hpp/.cpp): clang-format in place.

Formatting is applied silently. Lint or type errors are printed to stderr with exit
code 2 so Claude sees and fixes them.
"""

import json
import pathlib
import subprocess
import sys


def run(cmd: list[str], root: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True)


def main() -> int:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    path = tool_input.get("file_path") or payload.get("tool_response", {}).get("filePath")
    if not path:
        return 0

    root = pathlib.Path(__file__).resolve().parents[2]
    file = pathlib.Path(path).resolve()
    if root not in file.parents:
        return 0

    if file.suffix in (".hpp", ".cpp"):
        fmt = run(["clang-format", "-i", str(file)], root)
        if fmt.returncode != 0:
            print(f"clang-format:\n{fmt.stdout}{fmt.stderr}", file=sys.stderr)
            return 2
        return 0

    if file.suffix != ".py":
        return 0

    problems = []
    fmt = run(["ruff", "format", "--quiet", str(file)], root)
    if fmt.returncode != 0:
        problems.append(f"ruff format:\n{fmt.stdout}{fmt.stderr}")

    lint = run(["ruff", "check", "--quiet", str(file)], root)
    if lint.returncode != 0:
        problems.append(f"ruff:\n{lint.stdout}{lint.stderr}")

    types = run([sys.executable, "-m", "mypy"], root)
    if types.returncode != 0:
        problems.append(f"mypy:\n{types.stdout}{types.stderr}")

    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
