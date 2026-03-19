"""Main application entrypoint."""

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import tomllib
import venv
from pathlib import Path
from typing import Any


def _run_dev_mode(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run backend (uvicorn --reload) and frontend (npm run dev) for development."""
    project_root = Path(__file__).parent
    ui_dir = project_root / "ui"
    venv_path = project_root / ".venv"

    if sys.platform == "win32":
        venv_python = venv_path / "Scripts" / "python.exe"
    else:
        venv_python = venv_path / "bin" / "python"

    if not venv_python.exists():
        print("ERROR: Virtual environment not found. Run: python app.py --setup")
        sys.exit(1)

    if not (ui_dir / "node_modules").exists():
        print("Node dependencies not found. Run: python app.py --setup")
        sys.exit(1)

    # Backend: uvicorn with --reload
    backend_cmd = [
        str(venv_python),
        "-m",
        "uvicorn",
        "backend.main:app",
        "--reload",
        "--host",
        host,
        "--port",
        str(port),
    ]
    # Frontend: npm run dev, with API base URL so Vite proxies to backend
    frontend_env = os.environ.copy()
    frontend_env["VITE_API_BASE_URL"] = f"http://localhost:{port}"

    npm_path = shutil.which("npm")
    if not npm_path:
        print("ERROR: npm not found.")
        sys.exit(1)
    frontend_cmd = [npm_path, "run", "dev"]
    cwd_frontend = str(ui_dir)

    print("Starting development servers...")
    print(f"  Backend:  http://{host}:{port}")
    print(
        f"  Frontend: http://localhost:5173 (uses backend API at {frontend_env['VITE_API_BASE_URL']})"
    )
    print("Press Ctrl+C to stop both.")

    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(project_root),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=cwd_frontend,
        env=frontend_env,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    def kill_both(*_args, **_kwargs):
        backend_proc.terminate()
        frontend_proc.terminate()

    signal.signal(signal.SIGINT, kill_both)
    signal.signal(signal.SIGTERM, kill_both)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, kill_both)

    try:
        while backend_proc.poll() is None and frontend_proc.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    kill_both()
    backend_proc.wait()
    frontend_proc.wait()


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


def _start_mini_mode_helper(host: str, port: int) -> subprocess.Popen[Any] | None:
    """Start the Electron mini-mode sidecar used by the global hotkey widget."""
    project_root = Path(__file__).parent
    mini_mode_dir = project_root / "desktop" / "mini-mode"

    if not mini_mode_dir.exists():
        return None

    npm_path = shutil.which("npm")
    if not npm_path:
        print("Warning: npm not found, skipping Mini Mode helper startup.")
        return None

    mini_node_modules = mini_mode_dir / "node_modules"
    if not mini_node_modules.exists():
        print("Mini Mode dependencies not found. Installing in desktop/mini-mode...")
        try:
            subprocess.run([npm_path, "install"], check=True, cwd=mini_mode_dir)
            print("✓ Mini Mode dependencies installed")
        except subprocess.CalledProcessError as exc:
            print(f"Warning: failed to install Mini Mode dependencies: {exc}")
            return None

    mini_env = os.environ.copy()
    mini_env["MINI_MODE_MAIN_URL"] = f"http://{host}:{port}/chat"
    mini_env["MINI_MODE_WIDGET_URL"] = f"http://{host}:{port}/mini"

    try:
        proc = subprocess.Popen(
            [npm_path, "start"],
            cwd=mini_mode_dir,
            env=mini_env,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    except Exception as exc:  # pragma: no cover - best effort launcher path
        print(f"Warning: failed to start Mini Mode helper: {exc}")
        return None

    print(
        "Mini Mode helper started. Use Ctrl+Shift+Space to toggle the widget "
        "while the web UI is running."
    )
    return proc


def _latest_mtime(root: Path) -> float:
    """Return latest mtime under root (files only), or 0 when path is missing."""
    if not root.exists():
        return 0.0

    latest = 0.0
    for path in root.rglob("*"):
        if path.is_file():
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if mtime > latest:
                latest = mtime
    return latest


def _ui_build_is_stale(ui_dir: Path, ui_build_path: Path) -> bool:
    """Check whether ui/dist is older than key UI source files."""
    if not ui_build_path.exists():
        return True

    dist_index = ui_build_path / "index.html"
    if not dist_index.exists():
        return True

    try:
        dist_mtime = dist_index.stat().st_mtime
    except OSError:
        return True

    source_roots = [
        ui_dir / "src",
        ui_dir / "index.html",
        ui_dir / "package.json",
        ui_dir / "vite.config.ts",
        ui_dir / "vite.config.js",
    ]
    newest_source = 0.0
    for src in source_roots:
        if src.is_dir():
            newest_source = max(newest_source, _latest_mtime(src))
        elif src.exists():
            try:
                newest_source = max(newest_source, src.stat().st_mtime)
            except OSError:
                continue

    return newest_source > dist_mtime


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


def _run_benchmark(args) -> None:
    """Load benchmark config, bootstrap the app, and run the evaluation suite."""
    import asyncio

    import yaml

    from benchmarks.models import BenchmarkConfig
    from benchmarks.runner import BenchmarkRunner
    from core.bootstrap import bootstrap
    from core.runtime_config import build_runtime_client, resolve_runtime_preferences

    def _normalize_path_fragment(value: str) -> str:
        return value.replace("\\", "/").lower()

    def _infer_dataset_name(path_like: str | None) -> str | None:
        if not path_like:
            return None
        normalized = _normalize_path_fragment(path_like).rstrip("/")
        base = normalized.split("/")[-1]
        if re.fullmatch(r"dataset\d+", base):
            return base
        return None

    def _prompt_expected_paths(prompt: Any) -> list[str]:
        paths: list[str] = []
        if getattr(prompt, "expected_file", None):
            paths.append(str(prompt.expected_file))
        if getattr(prompt, "expected_files", None):
            paths.extend(str(p) for p in (prompt.expected_files or []))
        if getattr(prompt, "expected_citation_file", None):
            paths.append(str(prompt.expected_citation_file))
        return paths

    def _prompt_matches_dataset(prompt: Any, dataset_name: str) -> bool:
        marker = f"/{dataset_name.lower()}/"
        for raw in _prompt_expected_paths(prompt):
            normalized = f"/{_normalize_path_fragment(raw).strip('/')}"
            if marker in normalized + "/":
                return True
        return False

    def _known_embedding_dimension(backend: str, model: str | None) -> int | None:
        model_name = str(model or "").strip().lower()
        if not model_name:
            return None

        if backend == "local":
            local_prefix_dims = {
                "embeddinggemma": 768,
                "nomic-embed-text": 768,
                "mxbai-embed-large": 1024,
                "snowflake-arctic-embed": 1024,
                "bge": 1024,
                "e5": 1024,
            }
            for prefix, dim in local_prefix_dims.items():
                if model_name.startswith(prefix):
                    return dim

        if backend == "api":
            openai_dims = {
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072,
            }
            return openai_dims.get(model_name)

        # Gemini and some providers support configurable dimensions and are better
        # determined via probing; return None here so caller can continue fallback chain.
        return None

    def _infer_backend_from_model_id(
        model_id: str | None,
        *,
        kind: str,
    ) -> str | None:
        value = str(model_id or "").strip().lower()
        if not value:
            return None

        # Gemini naming conventions.
        if value.startswith("models/gemini-") or value.startswith("gemini-"):
            return "gemini"

        # OpenAI naming conventions.
        if value.startswith("text-embedding-") or value.startswith("gpt-"):
            return "api"

        # Voyage embedding model family.
        if kind == "embedding" and value.startswith("voyage-"):
            return "voyage"

        # Heuristic for local/Ollama models (tag-style ids like model:tag).
        if ":" in value:
            return "local"

        local_hints = (
            "llama",
            "qwen",
            "deepseek",
            "phi",
            "mistral",
            "gemma",
            "nomic",
            "embedding",
            "embed",
            "bge",
            "e5",
            "mxbai",
        )
        if any(h in value for h in local_hints):
            return "local"

        return None

    config_path = args.benchmark_config or str(
        Path(__file__).parent / "benchmarks" / "default_benchmark.yaml"
    )

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    config = BenchmarkConfig.from_dict(raw)

    # CLI overrides
    if args.benchmark_dataset:
        config.dataset_path = args.benchmark_dataset

    # Scope benchmark to a single dataset (fast iteration mode).
    scoped_dataset_name = None
    if args.benchmark_dataset_id is not None:
        ds = str(args.benchmark_dataset_id).strip()
        scoped_dataset_name = ds if ds.startswith("dataset") else f"dataset{ds}"
        config.dataset_path = str(Path("datasets") / scoped_dataset_name)
    else:
        inferred = _infer_dataset_name(args.benchmark_dataset)
        if inferred:
            scoped_dataset_name = inferred

    if scoped_dataset_name:
        before = len(config.prompts)
        config.prompts = [
            p for p in config.prompts if _prompt_matches_dataset(p, scoped_dataset_name)
        ]
        if config.dataset_suites:
            scoped_path = _normalize_path_fragment(
                str(Path("datasets") / scoped_dataset_name)
            ).rstrip("/")
            config.dataset_suites = [
                s
                for s in config.dataset_suites
                if _normalize_path_fragment(s.path).rstrip("/") == scoped_path
                or _normalize_path_fragment(s.id).rstrip("/")
                == scoped_dataset_name.lower()
            ]
        print(
            f"Scoped benchmark to {scoped_dataset_name}: {len(config.prompts)}/{before} prompts"
        )
        if not config.prompts:
            raise SystemExit(
                f"No prompts matched {scoped_dataset_name}. Check benchmark config paths."
            )
    if args.benchmark_output:
        config.output_dir = args.benchmark_output
    if args.benchmark_runs is not None:
        config.runs_per_query = args.benchmark_runs
    if args.no_graphs:
        config.no_graphs = True
    if args.skip_indexing:
        config.skip_indexing = True

    print(f"Benchmarking with {len(config.prompts)} prompts from {config_path}")
    print(f"  Dataset:   {config.dataset_path}")
    print(f"  Output:    {config.output_dir}")
    print(f"  Runs/query:{config.runs_per_query}")
    print(f"  Skip idx:  {config.skip_indexing}")
    print()

    ctx = bootstrap()

    prefs = resolve_runtime_preferences(ctx)

    benchmark_target = args.benchmark or "default"
    if benchmark_target in {"local", "api", "gemini"}:
        prefs["embedding_backend"] = benchmark_target
        prefs["inference_backend"] = benchmark_target

    if args.embed:
        prefs["embedding_model"] = args.embed
        inferred_embed_backend = _infer_backend_from_model_id(
            args.embed,
            kind="embedding",
        )
        if inferred_embed_backend in {"local", "api", "gemini", "voyage"}:
            prefs["embedding_backend"] = inferred_embed_backend
    if args.model:
        prefs["inference_model"] = args.model
        inferred_infer_backend = _infer_backend_from_model_id(
            args.model,
            kind="inference",
        )
        if inferred_infer_backend in {"local", "api", "gemini"}:
            prefs["inference_backend"] = inferred_infer_backend

    # Probe the embedding model's native/default vector size so benchmark indexing
    # always uses a matching DB dimension for the selected backend/model.
    probe_prefs = dict(prefs)
    probe_prefs["embedding_dimension"] = None
    embedding_backend = str(probe_prefs.get("embedding_backend") or "")
    embedding_model = str(probe_prefs.get("embedding_model") or "")
    probe_exception: Exception | None = None
    probed_dimension: int | None = None

    for _ in range(2):
        try:
            probe_embed_client = build_runtime_client(
                ctx, kind="embedding", prefs=probe_prefs
            )
            probe_vector = probe_embed_client.embed_text(["benchmark dimension probe"])[
                0
            ]
            probed_dimension = len(probe_vector)
            break
        except Exception as exc:
            probe_exception = exc

    if probed_dimension is None:
        known_dim = _known_embedding_dimension(embedding_backend, embedding_model)
        if known_dim is not None:
            print(
                "Warning: failed to probe embedding dimension for benchmark model "
                f"({probe_exception}). Using known dimension {known_dim} for "
                f"{embedding_backend}/{embedding_model}."
            )
            probed_dimension = known_dim
        else:
            fallback_dimension = int(
                prefs.get("embedding_dimension")
                or getattr(ctx.settings, "embedding_dimension", 3072)
            )
            print(
                "Warning: failed to probe embedding dimension for benchmark model "
                f"({probe_exception}). Falling back to {fallback_dimension}."
            )
            probed_dimension = fallback_dimension

    prefs["embedding_dimension"] = int(probed_dimension)
    try:
        ctx.embedding_client = build_runtime_client(ctx, kind="embedding", prefs=prefs)
        ctx.inference_client = build_runtime_client(ctx, kind="inference", prefs=prefs)
    except Exception as exc:
        message = str(exc).lower()
        if "api key is required" in message and benchmark_target == "default":
            # Default benchmark target should remain usable even when cloud API keys
            # are not configured. Fall back to local backends in that case.
            print(
                "Warning: benchmark default backend requires API key(s) but none were "
                "configured. Falling back to local embedding/inference backends."
            )
            prefs["embedding_backend"] = "local"
            prefs["inference_backend"] = "local"

            if not prefs.get("embedding_model"):
                prefs["embedding_model"] = "embeddinggemma:latest"
            if not prefs.get("inference_model"):
                prefs["inference_model"] = "llama3"

            local_known = _known_embedding_dimension(
                "local", str(prefs.get("embedding_model") or "")
            )
            if local_known is not None:
                prefs["embedding_dimension"] = int(local_known)

            ctx.embedding_client = build_runtime_client(
                ctx, kind="embedding", prefs=prefs
            )
            ctx.inference_client = build_runtime_client(
                ctx, kind="inference", prefs=prefs
            )
        else:
            raise
    ctx.runtime_preferences = prefs

    # Optional dedicated vision model for image-to-text during ingestion.
    # This lets benchmarking use a coding/text model for answer generation while
    # using a separate multimodal model for image description.
    indexing_llm_client = ctx.inference_client
    if args.vlm:
        indexing_llm_client = build_runtime_client(
            ctx,
            kind="inference",
            prefs=prefs,
            model_override=args.vlm,
        )

    print("Benchmark model configuration:")
    print(
        f"  Embedding: {prefs.get('embedding_backend')} / "
        f"{prefs.get('embedding_model')} (dim={prefs.get('embedding_dimension')})"
    )
    print(
        f"  Inference: {prefs.get('inference_backend')} / {prefs.get('inference_model')}"
    )
    if args.vlm:
        print(
            f"  Vision:    {prefs.get('inference_backend')} / {args.vlm} (indexing image-to-text)"
        )
    print()

    runner = BenchmarkRunner(config, ctx, indexing_llm_client=indexing_llm_client)
    asyncio.run(runner.run())


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
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Development mode: run backend with hot-reload and frontend dev server (backend on --port, UI on 5173)",
    )
    parser.add_argument(
        "--benchmark",
        nargs="?",
        const="default",
        choices=["default", "local", "api", "gemini"],
        default=None,
        help=(
            "Run benchmark suite. Optional value selects backend preset for both "
            "embedding and inference: default|local|api|gemini."
        ),
    )
    parser.add_argument(
        "--embed",
        type=str,
        default=None,
        help="Override embedding model id for benchmark runs.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override inference model id for benchmark runs.",
    )
    parser.add_argument(
        "--vlm",
        type=str,
        default=None,
        help=(
            "Optional dedicated vision-language model for ingestion image-to-text "
            "during benchmark runs (separate from --model)."
        ),
    )
    parser.add_argument(
        "--benchmark-config",
        type=str,
        default=None,
        help="Path to benchmark YAML config (default: benchmarks/default_benchmark.yaml).",
    )
    parser.add_argument(
        "--benchmark-dataset",
        type=str,
        default=None,
        help="Override the dataset path in the benchmark config.",
    )
    parser.add_argument(
        "--benchmark-dataset-id",
        type=str,
        default=None,
        help=(
            "Run benchmark against a single dataset folder and matching prompts "
            "(e.g. 13 or dataset13)."
        ),
    )
    parser.add_argument(
        "--benchmark-output",
        type=str,
        default=None,
        help="Override the output directory for benchmark results.",
    )
    parser.add_argument(
        "--benchmark-runs",
        type=int,
        default=None,
        help="Override the number of runs per query.",
    )
    parser.add_argument(
        "--no-graphs",
        action="store_true",
        help="Skip graph generation during benchmarking.",
    )
    parser.add_argument(
        "--skip-indexing",
        action="store_true",
        help="Skip dataset indexing and run queries against existing index.",
    )
    parser.add_argument(
        "--no-mini-mode",
        action="store_true",
        help="Do not auto-launch the Mini Mode desktop helper when using --webui.",
    )

    args = parser.parse_args()

    if args.setup:
        setup_environment()
        # After setup, continue to launch web UI if requested
        if not args.webui:
            return

    if args.dev:
        _run_dev_mode(host=args.host, port=args.port)
        return

    if args.benchmark is not None:
        _run_benchmark(args)
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

        # Build frontend when missing or stale so /mini reflects latest styling fixes.
        if _ui_build_is_stale(ui_dir, ui_build_path):
            print("Frontend build is missing or stale. Building frontend...")
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

        mini_mode_proc: subprocess.Popen[Any] | None = None
        if not args.no_mini_mode:
            mini_mode_proc = _start_mini_mode_helper(args.host, args.port)

        try:
            # Run the FastAPI server with static file serving
            uvicorn.run(app, host=args.host, port=args.port, log_level="info")
        finally:
            if mini_mode_proc and mini_mode_proc.poll() is None:
                mini_mode_proc.terminate()
                try:
                    mini_mode_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    mini_mode_proc.kill()
    else:
        print("Use --webui flag to launch the web interface")
        parser.print_help()


if __name__ == "__main__":
    main()
