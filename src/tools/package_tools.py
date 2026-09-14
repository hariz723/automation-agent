"""Package management tools for automatic package installation and upgrades."""

import re
import subprocess
import sys

from langchain_core.tools import tool

from src.config import Config

# Common Python import name to PyPI package name mapping
MODULE_TO_PYPI = {
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "yaml": "pyyaml",
    "PIL": "pillow",
    "dotenv": "python-dotenv",
    "dateutil": "python-dateutil",
}


def install_pypi_package(package_name: str, upgrade: bool = False) -> tuple[bool, str]:
    """Install or upgrade a Python package using uv (with pip fallback)."""
    clean_pkg = package_name.strip()
    # Security check: only allow valid package names / versions
    if not re.match(r"^[A-Za-z0-9_\-\.>=<~,! ]+$", clean_pkg):
        return False, f"Invalid package specification: '{clean_pkg}'"

    # Try uv add first
    cmd = ["uv", "add"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.extend(clean_pkg.split())

    try:
        res = subprocess.run(
            cmd,
            cwd=str(Config.WORKSPACE_DIR),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if res.returncode == 0:
            return True, f"Successfully installed '{clean_pkg}' via uv."
    except FileNotFoundError:
        pass
    except Exception as err:
        return False, f"Error running uv: {err!s}"

    # Fallback to pip install
    try:
        pip_cmd = [sys.executable, "-m", "pip", "install"]
        if upgrade:
            pip_cmd.append("--upgrade")
        pip_cmd.extend(clean_pkg.split())

        res = subprocess.run(
            pip_cmd,
            cwd=str(Config.WORKSPACE_DIR),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if res.returncode == 0:
            return True, f"Successfully installed '{clean_pkg}' via pip."
        return False, f"Installation failed:\n{res.stderr or res.stdout}"
    except Exception as err:
        return False, f"Error running pip: {err!s}"


def auto_install_module(missing_module_name: str) -> tuple[bool, str]:
    """Map missing module name to PyPI package and install it."""
    base_module = missing_module_name.split(".")[0]
    pypi_package = MODULE_TO_PYPI.get(base_module, base_module)
    return install_pypi_package(pypi_package)


@tool
def install_package(package_name: str, upgrade: bool = False) -> str:
    """Automatically install or upgrade any required Python package (e.g. 'pandas', 'beautifulsoup4', 'scipy', 'matplotlib').

    Args:
        package_name: Name of the package to install or upgrade from PyPI (e.g., 'pandas', 'openpyxl', 'seaborn').
        upgrade: Whether to upgrade the package to its latest version (default: False).
    """
    success, message = install_pypi_package(package_name=package_name, upgrade=upgrade)
    if success:
        return f"✅ {message}"
    return f"❌ Failed to install '{package_name}': {message}"
