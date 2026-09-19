"""modelctl — local CLI for free-model-gateway."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from modelctl.services.registry import DEFAULT_CONFIG_DIR, REPO_ROOT


def _config_dir(args: argparse.Namespace) -> Path | None:
    if getattr(args, "config_dir", None):
        return Path(args.config_dir)
    # Prefer repo config when running from a checkout
    candidate = REPO_ROOT / "config"
    if (candidate / "models.yaml").is_file():
        return candidate
    return DEFAULT_CONFIG_DIR


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="modelctl",
        description="Local control plane for free-model-gateway (Colab/HF via LiteLLM).",
    )
    p.add_argument(
        "--config-dir",
        help="Path to config/ (models.yaml, hosts.yaml). Default: repo config/.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("models", help="List models from config/models.yaml")
    sub.add_parser("hosts", help="List hosts from config/hosts.yaml")

    use = sub.add_parser("use", help="Select host + model in local state")
    use.add_argument("host_id")
    use.add_argument("model_id")
    use.add_argument("--context", type=int, default=None)

    st = sub.add_parser("status", help="Show local state and probe endpoint")
    st.add_argument("--no-probe", action="store_true", help="Skip live HTTP probe")

    stop = sub.add_parser("stop", help="Clear local endpoint (does not stop Colab)")
    stop.add_argument(
        "--all",
        action="store_true",
        help="Also clear host/model selection",
    )

    ep = sub.add_parser("endpoint", help="Get/set public gateway URL")
    ep_sub = ep.add_subparsers(dest="endpoint_cmd", required=True)
    ep_sub.add_parser("get", help="Print current endpoint")
    ep_set = ep_sub.add_parser("set", help="Set endpoint URL from Colab READY banner")
    ep_set.add_argument("url")
    ep_set.add_argument("--no-env", action="store_true", help="Do not print export lines")
    ep_sub.add_parser("env", help="Print ANTHROPIC_* export lines")

    conn = sub.add_parser("connect", help="Set endpoint and print exports (alias)")
    conn.add_argument("url")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_dir = _config_dir(args)

    if args.command == "models":
        from modelctl.commands.list import cmd_models

        return cmd_models(config_dir)

    if args.command == "hosts":
        from modelctl.commands.list import cmd_hosts

        return cmd_hosts(config_dir)

    if args.command == "use":
        from modelctl.commands.use import cmd_use

        return cmd_use(
            args.host_id,
            args.model_id,
            context=args.context,
            config_dir=config_dir,
        )

    if args.command == "status":
        from modelctl.commands.status import cmd_status

        return cmd_status(probe=not args.no_probe)

    if args.command == "stop":
        from modelctl.commands.stop import cmd_stop

        return cmd_stop(clear_selection=args.all)

    if args.command == "endpoint":
        from modelctl.commands.endpoint import (
            cmd_endpoint_env,
            cmd_endpoint_get,
            cmd_endpoint_set,
        )

        if args.endpoint_cmd == "get":
            return cmd_endpoint_get()
        if args.endpoint_cmd == "set":
            return cmd_endpoint_set(args.url, print_env=not args.no_env)
        if args.endpoint_cmd == "env":
            return cmd_endpoint_env()

    if args.command == "connect":
        from modelctl.commands.endpoint import cmd_connect

        return cmd_connect(args.url)

    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
