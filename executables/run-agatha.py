"""Run script for Agatha in development. Sets up server and starts it."""

import os
import subprocess  # nosec B404
import sys

import click


@click.command()
@click.option("--dev", is_flag=True, default=False, help="Run in development mode.")
@click.option("--host", default="127.0.0.1", help="Hostname to bind to.")
@click.option("--port", default="5442", help="Port to bind to.")
@click.option("--no-poetry", is_flag=True, default=False, help="Don't run poetry.")
def main(dev: bool, host: str, port: str, no_poetry: bool) -> None:
    """Parse cli-arguments and run Agatha."""
    args = ["uvicorn", "agatha.main:agatha", "--port", port, "--host", host]
    if not no_poetry:
        args = ["poetry", "run"] + args

    env_vars = os.environ.copy()
    if dev:
        env_vars["AGATHA_DEVELOPMENT_MODE"] = str(dev)

    if env_vars.get("AGATHA_DEVELOPMENT_MODE", False):
        args.append("--reload")
    try:
        subprocess.run(  # nosec B603 B607
            args,
            check=True,
            env=env_vars,
        )
    except KeyboardInterrupt:
        # Exit code for Ctrl-C
        sys.exit(130)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
