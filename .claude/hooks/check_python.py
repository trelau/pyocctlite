"""
Claude Code PostToolUse hook: lint and type-check after a Python file is edited.

Runs ruff on the edited file and mypy on the package (config in pyproject.toml).
On failure, prints the findings to stderr and exits 2 so Claude sees them.
"""
import json
import pathlib
import subprocess
import sys


def main() -> int:
    payload = json.load(sys.stdin)
    tool_input = payload.get('tool_input', {})
    path = tool_input.get('file_path') or payload.get('tool_response', {}).get('filePath')
    if not path or not path.endswith('.py'):
        return 0

    root = pathlib.Path(__file__).resolve().parents[2]
    file = pathlib.Path(path).resolve()
    if root not in file.parents:
        return 0

    problems = []
    ruff = subprocess.run(['ruff', 'check', '--quiet', str(file)], cwd=root,
                          capture_output=True, text=True)
    if ruff.returncode != 0:
        problems.append(f'ruff:\n{ruff.stdout}{ruff.stderr}')

    mypy = subprocess.run([sys.executable, '-m', 'mypy'], cwd=root, capture_output=True, text=True)
    if mypy.returncode != 0:
        problems.append(f'mypy:\n{mypy.stdout}{mypy.stderr}')

    if problems:
        print('\n'.join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
