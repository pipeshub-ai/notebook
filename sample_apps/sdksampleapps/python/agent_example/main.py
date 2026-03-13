"""
Main entrypoint for the PipesHub Agents API sample.

Run one example by name, or all examples in sequence (auth → list-agents → create-agent → chat-with-agent).

Usage:
  python main.py                    # run all examples in order
  python main.py auth               # run only auth (get bearer token)
  python main.py list-agents        # run only list-agents
  python main.py create-agent       # run only create-agent
  python main.py chat-with-agent    # run only chat-with-agent (interactive REPL)

Alternative: full flow in a single script (auth → create agent → chat REPL):
  python src/index.py
"""
import subprocess
import sys
from pathlib import Path

# (example_key, script_path_relative_to_project_root, short_description)
EXAMPLES = [
    ("auth", "examples/auth/index.py", "Get bearer token"),
    ("list-agents", "examples/list-agents/index.py", "List agents"),
    ("create-agent", "examples/create-agent/index.py", "Create SDK Demo Agent"),
    ("chat-with-agent", "examples/chat-with-agent/index.py", "Interactive chat with agent (REPL)"),
]


def main() -> None:
    root = Path(__file__).resolve().parent
    # Single example: python main.py <name>
    if len(sys.argv) > 1:
        name = sys.argv[1].strip().lower()
        for key, script, _ in EXAMPLES:
            if key == name:
                print(f"[main] Running: {key}\n")
                code = subprocess.run(
                    [sys.executable, script],
                    cwd=root,
                ).returncode
                sys.exit(code)
        print(f"Unknown example: {name}", file=sys.stderr)
        print("Usage: python main.py [auth|list-agents|create-agent|chat-with-agent]", file=sys.stderr)
        sys.exit(1)

    # No args: run all examples in order; exit on first failure
    for key, script, desc in EXAMPLES:
        print(f"\n[main] --- {key}: {desc} ---\n")
        code = subprocess.run(
            [sys.executable, script],
            cwd=root,
        ).returncode
        if code != 0:
            print(f"\n[main] {key} exited with code {code}", file=sys.stderr)
            sys.exit(code)
    print("\n[main] All examples completed.\n")


if __name__ == "__main__":
    main()
