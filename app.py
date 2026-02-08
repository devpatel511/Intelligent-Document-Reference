"""Main application entrypoint."""

import argparse
import os
import shutil
import subprocess
import sys
import tomllib
import venv
from pathlib import Path


def check_command_exists(command: str) -> bool:
    """Check if a command exists in the system PATH (cross-platform)."""
    # Use shutil.which for cross-platform command detection
    if shutil.which(command) is not None:
        return True

    # Fallback: try running the command to verify it works
    try:
        subprocess.run(
            [command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=5,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return False


def setup_environment():
    """Set up the development environment."""
    print("=" * 60)
    print("Setting up Local RAG Application Environment")
    print("=" * 60)

    project_root = Path(__file__).parent
    venv_path = project_root / ".venv"

    # Check for Python
    if not check_command_exists("python3") and not check_command_exists("python"):
        print("ERROR: Python 3 is not installed or not in PATH")
        print("Please install Python 3.10 or higher from https://www.python.org/")
        sys.exit(1)

    python_cmd = "python3" if check_command_exists("python3") else "python"

    # Check for Node.js and npm
    if not check_command_exists("node"):
        print("ERROR: Node.js is not installed or not in PATH")
        print("Please install Node.js from https://nodejs.org/")
        print("If Node.js is installed, make sure it's in your system PATH")
        sys.exit(1)

    if not check_command_exists("npm"):
        print("ERROR: npm is not installed or not in PATH")
        print("Please install npm (usually comes with Node.js)")
        print("If npm is installed, make sure it's in your system PATH")
        print("\nTroubleshooting:")
        print("  - Try running 'node --version' and 'npm --version' in your terminal")
        print(
            "  - If they work there, the PATH might not be set correctly for Python subprocess"
        )
        sys.exit(1)

    print(f"\n✓ Python found: {python_cmd}")
    print("✓ Node.js found")
    print("✓ npm found")

    # Create virtual environment if it doesn't exist
    if not venv_path.exists():
        print(f"\nCreating Python virtual environment at {venv_path}...")
        venv.create(venv_path, with_pip=True)
        print("✓ Virtual environment created")
    else:
        print(f"\n✓ Virtual environment already exists at {venv_path}")

    # Determine the correct pip and python paths for the venv (cross-platform)
    # Python's venv module handles this automatically, but we need the paths
    if sys.platform == "win32":
        venv_python = venv_path / "Scripts" / "python.exe"  # noqa
        venv_pip = venv_path / "Scripts" / "pip.exe"
    else:
        venv_python = venv_path / "bin" / "python"  # noqa
        venv_pip = venv_path / "bin" / "pip"

    # Install Python dependencies
    print("\nInstalling Python dependencies...")
    try:
        # Check if uv is available
        if check_command_exists("uv"):
            print("Using uv to install dependencies...")
            subprocess.run(["uv", "sync"], check=True, cwd=project_root)
        else:
            print("uv not found. Installing dependencies with pip...")
            pyproject_file = project_root / "pyproject.toml"
            with open(pyproject_file, "rb") as f:
                pyproject_data = tomllib.load(f)

            dependencies = pyproject_data["project"]["dependencies"]
            subprocess.run(
                [str(venv_pip), "install"] + dependencies, check=True, cwd=project_root
            )
        print("✓ Python dependencies installed")
    except Exception as e:
        print(f"ERROR: Failed to install Python dependencies: {e}")
        sys.exit(1)

    # Install Node.js dependencies
    print("\nInstalling Node.js dependencies...")
    ui_dir = project_root / "ui"
    try:
        # Find npm executable path (works cross-platform)
        npm_path = shutil.which("npm")
        if npm_path:
            subprocess.run([npm_path, "install"], check=True, cwd=ui_dir)
        else:
            # Fallback: use shell execution if path not found
            subprocess.run("npm install", shell=True, check=True, cwd=ui_dir)
        print("✓ Node.js dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install Node.js dependencies: {e}")
        sys.exit(1)

    # Build frontend
    print("\nBuilding frontend...")
    try:
        # Find npm executable path (works cross-platform)
        npm_path = shutil.which("npm")
        if npm_path:
            subprocess.run([npm_path, "run", "build"], check=True, cwd=ui_dir)
        else:
            # Fallback: use shell execution if path not found
            subprocess.run("npm run build", shell=True, check=True, cwd=ui_dir)
        print("✓ Frontend built successfully")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to build frontend: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Setup completed successfully!")
    print("=" * 60)
    print("\nYou can now run the application with:")
    print("  python3 app.py --webui")
    print("\nOr activate the virtual environment first:")
    if sys.platform == "win32":
        print("  .venv\\Scripts\\activate")
    else:
        print("  source .venv/bin/activate")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Local RAG Application")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Set up the environment (install dependencies, build frontend)",
    )
    parser.add_argument(
        "--webui", action="store_true", help="Launch the web UI with backend server"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )

    args = parser.parse_args()

    if args.setup:
        setup_environment()
        # After setup, continue to launch web UI if requested
        if not args.webui:
            return

    if args.webui:
        ui_dir = Path(__file__).parent / "ui"
        ui_build_path = ui_dir / "dist"
        node_modules_path = ui_dir / "node_modules"

        # Check if Node.js dependencies are installed
        if not node_modules_path.exists():
            print("Node.js dependencies not found. Installing...")
            os.chdir(ui_dir)
            try:
                # Find npm executable path (works cross-platform)
                npm_path = shutil.which("npm")
                if npm_path:
                    subprocess.run([npm_path, "install"], check=True)
                else:
                    # Fallback: use shell execution if path not found
                    subprocess.run("npm install", shell=True, check=True)
                print("✓ Node.js dependencies installed")
            except subprocess.CalledProcessError:
                print("Error installing Node.js dependencies.")
                print("Please run 'npm install' in the ui/ directory.")
                sys.exit(1)
            except FileNotFoundError:
                print("npm not found. Please install Node.js and npm.")
                sys.exit(1)
            finally:
                os.chdir(Path(__file__).parent)

        # Check if frontend is built
        if not ui_build_path.exists():
            print("Frontend not built. Building frontend...")
            os.chdir(ui_dir)
            try:
                # Find npm executable path (works cross-platform)
                npm_path = shutil.which("npm")
                if npm_path:
                    subprocess.run([npm_path, "run", "build"], check=True)
                else:
                    # Fallback: use shell execution if path not found
                    subprocess.run("npm run build", shell=True, check=True)
                print("✓ Frontend built successfully!")
            except subprocess.CalledProcessError:
                print("Error building frontend.")
                print("Please run 'npm run build' in the ui/ directory.")
                sys.exit(1)
            except FileNotFoundError:
                print("npm not found. Please install Node.js and npm.")
                sys.exit(1)
            finally:
                os.chdir(Path(__file__).parent)

        print(f"Starting web UI server on http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop the server")

        # Check if we're using the venv's Python, and if not, suggest using it
        venv_path = Path(__file__).parent / ".venv"
        using_venv_python = False

        if venv_path.exists():
            if sys.platform == "win32":
                venv_python = venv_path / "Scripts" / "python.exe"
            else:
                venv_python = venv_path / "bin" / "python"

            # Check if current Python is from venv
            current_python = Path(sys.executable).resolve()
            venv_python_resolved = (
                venv_python.resolve() if venv_python.exists() else None
            )

            if venv_python_resolved and current_python == venv_python_resolved:
                using_venv_python = True

        # Import dependencies only when needed (after setup)
        try:
            import uvicorn

            from backend.main import app
        except ImportError as e:
            print(f"ERROR: Required dependencies not installed: {e}")
            print(
                "\nThe issue is that the Python interpreter you're using doesn't have the dependencies."
            )

            if venv_path.exists() and not using_venv_python:
                print("\nSolution: Use the virtual environment's Python directly:")
                if sys.platform == "win32":
                    venv_python = venv_path / "Scripts" / "python.exe"
                    print(f"  {venv_python} app.py --webui")
                else:
                    venv_python = venv_path / "bin" / "python"
                    print(f"  {venv_python} app.py --webui")
            else:
                print("\nTroubleshooting:")
                print("1. Make sure you've run: python3 app.py --setup")
                print("2. If using a virtual environment, activate it first:")
                if sys.platform == "win32":
                    print("   .venv\\Scripts\\activate")
                    print("   Then use: python app.py --webui")
                else:
                    print("   source .venv/bin/activate")
                    print("   Then use: python app.py --webui")
                print("3. Or use the venv's Python directly:")
                if sys.platform == "win32":
                    print("   .venv\\Scripts\\python.exe app.py --webui")
                else:
                    print("   .venv/bin/python app.py --webui")
            sys.exit(1)

        # Run the FastAPI server with static file serving
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    else:
        print("Use --webui flag to launch the web interface")
        parser.print_help()


if __name__ == "__main__":
    main()
