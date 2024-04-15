"""Run script for Study App in development. Sets up server and starts it."""

import subprocess  # nosec B404
import sys

import click


@click.command()
@click.option("--host", default="127.0.0.1", help="Hostname to bind to.")
@click.option("--port", default="5443", help="Port to bind to.")
def main(host: str, port: str):
    """Parse cli-arguments and run Study app."""
    try:
        subprocess.run(  # nosec B603 B607
            [
                "poetry",
                "run",
                "uvicorn",
                "agatha.study_main:study_app",
                "--reload",
                "--port",
                port,
                "--host",
                host,
            ],
            check=True,
        )
    except KeyboardInterrupt:
        # Exit code for Ctrl-C
        sys.exit(130)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
