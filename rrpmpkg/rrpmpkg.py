import os
import platform
import re
import shutil
import subprocess

import requests
from rich.console import Console
import typer

cli = typer.Typer()
console = Console()

REPO_REGEX = re.compile(r"^([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)$")
GITHUB_REGEX = re.compile(r"^(https://|http://)?github.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)(.git)?$")


@cli.command()
def install(package: str, install_deps: bool = True, ):
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
    temp_dir = os.path.expandvars(f"%TEMP%\\{url.split('/')[-1]}") if platform.system().lower().startswith("win") else f"/tmp/{url.split('/')[-1]}"
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    out = subprocess.run(["git", "clone", url, temp_dir], capture_output=True)
    if str(out.stdout).startswith("fatal: destintion path"):
        shutil.rmtree(temp_dir)
        subprocess.run(["git", "clone", url, temp_dir])
    else:
        console.print(out.stdout.decode("utf-8"))
    os.chdir(temp_dir)
    if install_deps:
        console.print("[green]Installing dependencies[/]")
        subprocess.run(["pip", "install", "-r", "requirements.txt"])
    console.print("[green]Installing extension[/]")
    for file in os.listdir(temp_dir):
        if os.path.isfile(file) and file.endswith(".py"):
            if platform.system().lower().startswith("win"):
                shutil.copy(temp_dir, os.path.expandvars(f"%LOCALAPPDATA%\\rrpm\\extensions\\{file}"))
            else:
                shutil.copy(temp_dir,
                            os.path.expanduser(f"~/.config/rrpm/extensions/{file}"))
        else:
            if os.path.isdir(file):
                if not file.startswith("."):
                    if platform.system().lower().startswith("win"):
                        shutil.copytree(temp_dir,
                                        os.path.expandvars(f"%LOCALAPPDATA%\\rrpm"
                                                           f"\\extensions\\{file}"))
                    else:
                        shutil.copytree(temp_dir,
                                        os.path.expanduser(f"~/.config/rrpm/extensions/{file}"))


if __name__ == "__main__":
    cli()
