import os
import platform
import re
import shutil
import subprocess

import requests
from rich.console import Console
import typer

from . import __version__

cli = typer.Typer()
console = Console()

REPO_REGEX = re.compile(r"^([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)$")
GITHUB_REGEX = re.compile(r"^(https://|http://)?github.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)(.git)?$")


@cli.command()
def version():
    """Show RRPM's currently installed version"""
    console.print(f"[green]RRPM Version {__version__}[/]")


@cli.command()
def install(package: str, install_deps: bool = True):
    """Install an extension"""
    if shutil.which("git") is None:
        console.print("Git is not installed")
        return

    if REPO_REGEX.match(package) is not None:
        url = f"https://github.com/{package}"
    elif GITHUB_REGEX.match(package) is not None:
        if not package.startswith("http://") and not package.startswith("https://"):
            url = f"https://{package}"
        else:
            url = package.removesuffix(".git").replace("http://", "https://")
    else:
        console.print(f"[red]'{package}' package not found[/]")
        return

    if requests.get(url).status_code != 200:
        console.print(f"[red]'{package}' extension not found[/]")
        return

    console.print(f"[green]Installing '{package}' extension[/]")
    ext_dir = os.path.expanduser(
        os.path.expandvars("%LOCALAPPDATA%\\rrpm\\extensions")) if platform.system().lower().startswith(
        "win") else os.path.expanduser(os.path.expandvars("~/.config/rrpm/extensions"))
    try:
        out = subprocess.run([shutil.which("git"), "clone", url, os.path.join(ext_dir, url.split("/")[-1])], capture_output=True)
        if out.stdout.decode("utf-8").startswith("fatal: destination path"):
            console.print("[red]Extension already exists[/]")
        else:
            console.print(out.stdout.decode("utf-8"))
    except FileNotFoundError:
        out = subprocess.run([shutil.which("git"), "clone", url, os.path.join(ext_dir, url.split("/")[-1])], capture_output=True, shell=True)
        if out.stdout.decode("utf-8").startswith("fatal: destination path"):
            console.print("[red]Extension already exists[/]")
        else:
            console.print(out.stdout.decode("utf-8"))

    if os.path.exists(
            os.path.join(
                ext_dir,
                url.split("/")[-1]
            )
    ) and install_deps:
        if os.path.exists(
                os.path.join(
                    ext_dir,
                    url.split("/")[-1],
                    "requirements.txt"
                )
        ):
            try:
                subprocess.run(
                    [
                        shutil.which("pip"),
                        "install",
                        "-r",
                        os.path.join(
                            ext_dir,
                            url.split("/")[-1],
                            "requirements.txt"
                        )
                    ]
                )
            except FileNotFoundError:
                subprocess.run(
                    [
                        shutil.which("pip"),
                        "install",
                        "-r",
                        os.path.join(
                            ext_dir,
                            url.split("/")[-1],
                            "requirements.txt"
                        )
                    ],
                    shell=True
                )
        else:
            console.print("WARNING: Failed to install dependencies! No requirements.txt file present!")


@cli.command()
def uninstall(package: str):
    """Uninstall an extension"""
    console.print(f"[green]Uninstalling '{package}' extension[/]")
    ext_dir = os.path.expanduser(
        os.path.expandvars("%LOCALAPPDATA%\\rrpm\\extensions")) if platform.system().lower().startswith(
        "win") else os.path.expanduser(os.path.expandvars("~/.config/rrpm/extensions"))
    try:
        shutil.rmtree(os.path.join(ext_dir, package.split("/")[-1]))
    except FileNotFoundError:
        console.print("[red]Extension is not installed![/]")
    except PermissionError as e:
        console.print(f"[red]Failed to uninstall extension! Permission denied to file: {':'.join(str(e).split(':')[1:]).lstrip().rstrip()}[/]")
    except Exception as e:
        console.print("[red]Failed to uninstall extension! Exception occured: {e}")


@cli.command()
def update(package: str = None, reinstall_deps: bool = False):
    """Update an Extension"""
    if shutil.which("git") is None:
        console.print("Git is not installed")
        return

    ext_dir = os.path.expanduser(
        os.path.expandvars("%LOCALAPPDATA%\\rrpm\\extensions")) if platform.system().lower().startswith(
        "win") else os.path.expanduser(os.path.expandvars("~/.config/rrpm/extensions"))

    if package is None:
        if not os.listdir(ext_dir):
            console.print("[yellow]No extensions are installed![/]")
            return
        for fold in os.listdir(ext_dir):
            os.chdir(os.path.join(ext_dir, fold))
            try:
                subprocess.run([shutil.which("git"), "pull"])
            except FileNotFoundError:
                subprocess.run([shutil.which("git"), "pull"], shell=True)

            if reinstall_deps:
                if os.path.exists(
                        os.path.join(
                            ext_dir,
                            fold,
                            "requirements.txt"
                        )
                ):
                    try:
                        subprocess.run(
                            [
                                shutil.which("pip"),
                                "install",
                                "-r",
                                os.path.join(
                                    ext_dir,
                                    fold,
                                    "requirements.txt"
                                )
                            ]
                        )
                    except FileNotFoundError:
                        subprocess.run(
                            [
                                shutil.which("pip"),
                                "install",
                                "-r",
                                os.path.join(
                                    ext_dir,
                                    fold,
                                    "requirements.txt"
                                )
                            ],
                            shell=True
                        )
                else:
                    console.print(
                        f"WARNING: Failed to install dependencies for '{fold}'! No requirements.txt file present!")
    else:
        try:
            os.chdir(os.path.join(ext_dir, package))
        except FileNotFoundError:
            console.print("[red]Extension is not installed[/]")
            return
        try:
            subprocess.run([shutil.which("git"), "pull"])
        except FileNotFoundError:
            subprocess.run([shutil.which("git"), "pull"], shell=True)
        if reinstall_deps:
            if os.path.exists(
                    os.path.join(
                        ext_dir,
                        package,
                        "requirements.txt"
                    )
            ):
                try:
                    subprocess.run(
                        [
                            shutil.which("pip"),
                            "install",
                            "-r",
                            os.path.join(
                                ext_dir,
                                package,
                                "requirements.txt"
                            )
                        ]
                    )
                except FileNotFoundError:
                    subprocess.run(
                        [
                            shutil.which("pip"),
                            "install",
                            "-r",
                            os.path.join(
                                ext_dir,
                                package,
                                "requirements.txt"
                            )
                        ],
                        shell=True
                    )
            else:
                console.print(
                    f"WARNING: Failed to install dependencies for '{package}'! No requirements.txt file present!")


if __name__ == "__main__":
    cli()
