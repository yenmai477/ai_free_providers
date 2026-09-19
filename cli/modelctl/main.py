"""modelctl entrypoint (Sprint 4 CLI; stub for Phase 1)."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] in {"-h", "--help"}:
        print(
            "modelctl — Phase 1 stub\n"
            "Full CLI lands in Sprint 4.\n"
            "Use the Colab notebook + curl for Phase 1 verification."
        )
        return 0
    print(f"modelctl: unknown command {argv[0]!r} (CLI not implemented yet)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
