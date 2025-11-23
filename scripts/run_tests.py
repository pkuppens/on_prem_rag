#!/usr/bin/env python3
"""
Test Agent: Detect and Execute Tests with Service Management

This script detects and executes all tests in the project, including integration
tests that require services to be started. It automatically manages service
lifecycle (Docker services, MCP servers) and uses parallelism where possible.

Author: AI Assistant
Created: 2025-01-19
Updated: 2025-01-19
"""

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


class ServiceManager:
    """Manages Docker services and MCP servers for integration tests."""

    def __init__(self, keep_services: bool = False, verbose: bool = False):
        """Initialize service manager.

        Args:
            keep_services: If True, keep services running after tests
            verbose: If True, show verbose output
        """
        self.keep_services = keep_services
        self.verbose = verbose
        self.started_services: Set[str] = set()
        self.mcp_server_process: Optional[subprocess.Popen] = None

    def check_port(self, host: str, port: int, timeout: float = 2.0) -> bool:
        """Check if a port is open and accepting connections.

        Args:
            host: Hostname or IP address
            port: Port number
            timeout: Connection timeout in seconds

        Returns:
            True if port is open, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def check_docker_service(self, service_name: str, port: int) -> bool:
        """Check if a Docker service is running.

        Args:
            service_name: Docker service name
            port: Service port

        Returns:
            True if service is running, False otherwise
        """
        # Check if service is running in Docker
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", service_name, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Check if port is accessible
                return self.check_port("localhost", port)
        except Exception:
            pass
        return False

    def start_docker_service(self, service_name: str, wait_time: int = 30) -> bool:
        """Start a Docker service.

        Args:
            service_name: Docker service name
            wait_time: Time to wait for service to be ready (seconds)

        Returns:
            True if service started successfully, False otherwise
        """
        if self.verbose:
            print(f"   [INFO] Starting Docker service: {service_name}")

        try:
            # Start service
            result = subprocess.run(
                ["docker", "compose", "up", "-d", service_name],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                if self.verbose:
                    print(f"   ❌ Failed to start {service_name}: {result.stderr}")
                return False

            # Wait for service to be ready
            if self.verbose:
                print(f"   [INFO] Waiting for {service_name} to be ready...")
            time.sleep(wait_time)

            # Check if service is running
            result = subprocess.run(
                ["docker", "compose", "ps", service_name, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout.strip():
                self.started_services.add(service_name)
                if self.verbose:
                    print(f"   [OK] {service_name} is running")
                return True
            else:
                if self.verbose:
                    print(f"   [FAIL] {service_name} failed to start")
                return False

        except subprocess.TimeoutExpired:
            if self.verbose:
                print(f"   [FAIL] Timeout starting {service_name}")
            return False
        except Exception as e:
            if self.verbose:
                print(f"   [FAIL] Error starting {service_name}: {e}")
            return False

    def start_mcp_calendar_server(self) -> bool:
        """Start MCP Calendar Server if needed.

        Returns:
            True if server started or already running, False otherwise
        """
        # Check if server is already running (cross-platform)
        try:
            if sys.platform == "win32":
                # Windows: use tasklist
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq python.exe"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                # Check if mcp-calendar-server might be running
                # This is a heuristic - we can't easily check the command line on Windows
                # So we'll just try to start it and see if it fails
                already_running = False
            else:
                # Unix: use pgrep
                result = subprocess.run(
                    ["pgrep", "-f", "mcp-calendar-server"],
                    capture_output=True,
                    timeout=5,
                )
                already_running = result.returncode == 0

            if already_running:
                if self.verbose:
                    print("   [OK] MCP Calendar Server already running")
                return True
        except Exception:
            pass

        if self.verbose:
            print("   [INFO] Starting MCP Calendar Server...")

        try:
            # Start server in background using uv run
            # Note: On Windows, we need to use the full path or ensure uv is in PATH
            cmd = ["uv", "run", "mcp-calendar-server"]
            if sys.platform == "win32":
                # On Windows, use shell=True for better command resolution
                self.mcp_server_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE if not self.verbose else None,
                    stderr=subprocess.PIPE if not self.verbose else None,
                    cwd=PROJECT_ROOT,
                    shell=True,
                )
            else:
                self.mcp_server_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE if not self.verbose else None,
                    stderr=subprocess.PIPE if not self.verbose else None,
                    cwd=PROJECT_ROOT,
                )

            # Wait a bit for server to start
            time.sleep(3)

            # Check if process is still running
            if self.mcp_server_process.poll() is None:
                if self.verbose:
                    print("   [OK] MCP Calendar Server started")
                return True
            else:
                if self.verbose:
                    print("   [FAIL] MCP Calendar Server failed to start")
                return False

        except Exception as e:
            if self.verbose:
                print(f"   [FAIL] Error starting MCP Calendar Server: {e}")
            return False

    def ensure_services(self, required_services: Dict[str, int]) -> Dict[str, bool]:
        """Ensure required services are running.

        Args:
            required_services: Dictionary mapping service names to ports

        Returns:
            Dictionary mapping service names to their status (True if running)
        """
        status: Dict[str, bool] = {}

        for service_name, port in required_services.items():
            if service_name == "mcp-calendar-server":
                status[service_name] = self.start_mcp_calendar_server()
            else:
                # Check if already running
                if self.check_docker_service(service_name, port):
                    status[service_name] = True
                    if self.verbose:
                        print(f"   [OK] {service_name} already running")
                else:
                    # Start service
                    status[service_name] = self.start_docker_service(service_name)

        return status

    def cleanup(self) -> None:
        """Clean up started services."""
        if self.keep_services:
            if self.verbose:
                print("   [INFO] Keeping services running (--keep-services)")
            return

        # Stop MCP server
        if self.mcp_server_process:
            try:
                self.mcp_server_process.terminate()
                self.mcp_server_process.wait(timeout=5)
                if self.verbose:
                    print("   [INFO] Stopped MCP Calendar Server")
            except Exception:
                try:
                    self.mcp_server_process.kill()
                except Exception:
                    pass

        # Stop Docker services we started
        if self.started_services:
            if self.verbose:
                print(f"   [INFO] Stopping Docker services: {', '.join(self.started_services)}")

            for service in self.started_services:
                try:
                    subprocess.run(
                        ["docker", "compose", "stop", service],
                        capture_output=True,
                        timeout=30,
                    )
                except Exception:
                    pass


class TestDetector:
    """Detects tests and identifies integration test requirements."""

    def __init__(self, test_dir: Path = None):
        """Initialize test detector.

        Args:
            test_dir: Directory containing tests (default: tests/)
        """
        self.test_dir = test_dir or (PROJECT_ROOT / "tests")
        self.integration_test_patterns = [
            r"integration",
            r"mcp.*calendar",
            r"websocket",
            r"auth.*service",
            r"vector.*store",
            r"embedding.*pipeline",
        ]

    def detect_tests(self) -> List[Path]:
        """Detect all test files.

        Returns:
            List of test file paths
        """
        test_files = []
        for pattern in ["test_*.py", "*_test.py"]:
            test_files.extend(self.test_dir.glob(pattern))
            test_files.extend(self.test_dir.rglob(pattern))

        # Remove duplicates and sort
        return sorted(set(test_files))

    def is_integration_test(self, test_file: Path) -> bool:
        """Check if a test file is an integration test.

        Args:
            test_file: Path to test file

        Returns:
            True if integration test, False otherwise
        """
        # Check filename patterns
        filename = test_file.name.lower()
        for pattern in self.integration_test_patterns:
            if re.search(pattern, filename):
                return True

        # Check file content for integration markers
        try:
            content = test_file.read_text(encoding="utf-8")
            if re.search(r"@pytest\.mark\.integration", content, re.IGNORECASE):
                return True
            if re.search(r"integration.*test", content, re.IGNORECASE):
                return True
            # Check for service dependencies
            if any(service in content.lower() for service in ["docker", "chromadb", "ollama", "mcp", "calendar", "websocket"]):
                return True
        except Exception:
            pass

        return False

    def get_required_services(self, test_files: List[Path]) -> Dict[str, int]:
        """Determine required services for test files.

        Args:
            test_files: List of test file paths

        Returns:
            Dictionary mapping service names to ports
        """
        required_services: Dict[str, int] = {}

        for test_file in test_files:
            if not self.is_integration_test(test_file):
                continue

            try:
                content = test_file.read_text(encoding="utf-8").lower()

                # Check for Docker services
                if "chromadb" in content or "chroma" in content:
                    required_services["chroma"] = 9100
                if "ollama" in content:
                    required_services["ollama"] = 11434
                if "backend" in content or "rag.*pipeline" in content:
                    required_services["backend"] = 9000
                if "auth" in content or "authentication" in content:
                    required_services["auth"] = 9100

                # Check for MCP Calendar Server
                if "mcp.*calendar" in content or "calendar.*server" in content:
                    required_services["mcp-calendar-server"] = 0  # Port varies

            except Exception:
                pass

        return required_services


class TestRunner:
    """Runs tests with parallel execution and failure handling."""

    def __init__(
        self,
        service_manager: ServiceManager,
        verbose: bool = False,
        auto_fix: bool = False,
    ):
        """Initialize test runner.

        Args:
            service_manager: Service manager instance
            verbose: If True, show verbose output
            auto_fix: If True, attempt to fix test failures automatically
        """
        self.service_manager = service_manager
        self.verbose = verbose
        self.auto_fix = auto_fix

    def run_tests(
        self,
        test_files: Optional[List[Path]] = None,
        pattern: Optional[str] = None,
        markers: Optional[str] = None,
        parallel: bool = True,
        workers: Optional[int] = None,
    ) -> Tuple[int, Dict[str, any]]:
        """Run tests.

        Args:
            test_files: Specific test files to run (None for all)
            pattern: Test name pattern to match
            markers: Pytest markers to filter by
            parallel: If True, run tests in parallel
            workers: Number of parallel workers (None for auto)

        Returns:
            Tuple of (exit_code, results_dict)
        """
        # Build pytest arguments
        pytest_args = ["-v", "--tb=short"]

        # Add test files or directory
        if test_files:
            pytest_args.extend([str(f) for f in test_files])
        else:
            pytest_args.append(str(PROJECT_ROOT / "tests"))

        # Add pattern if specified
        if pattern:
            pytest_args.extend(["-k", pattern])

        # Add markers if specified
        if markers:
            pytest_args.extend(["-m", markers])

        # Add parallel execution
        if parallel:
            # Check if pytest-xdist is available
            try:
                import xdist

                if workers:
                    pytest_args.extend(["-n", str(workers)])
                else:
                    pytest_args.extend(["-n", "auto"])
            except ImportError:
                if self.verbose:
                    print("   [WARN] pytest-xdist not available, running sequentially")
                parallel = False

        # Determine how to run pytest
        # Priority: pytest directly > python -m pytest > uv run pytest
        # This avoids pyvenv.cfg errors by preferring direct execution
        use_uv = False
        pytest_cmd = None

        # First, try pytest directly (if installed in PATH or current environment)
        try:
            result = subprocess.run(
                ["pytest", "--version"],
                capture_output=True,
                timeout=5,
                check=True,
            )
            pytest_cmd = ["pytest"]
            if self.verbose:
                print("   [INFO] Using pytest directly")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # Try python -m pytest (works if pytest is installed as a module)
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "--version"],
                    capture_output=True,
                    timeout=5,
                    check=True,
                )
                pytest_cmd = [sys.executable, "-m", "pytest"]
                if self.verbose:
                    print("   [INFO] Using python -m pytest")
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                # Last resort: try uv run pytest
                # Only use if pytest is not available directly
                # We'll catch the pyvenv.cfg error and handle it gracefully
                try:
                    # Check if uv is available (but don't test uv run to avoid errors)
                    subprocess.run(["uv", "--version"], capture_output=True, timeout=5, check=True)
                    use_uv = True
                    pytest_cmd = ["uv", "run", "pytest"]
                    if self.verbose:
                        print("   [INFO] Attempting uv run pytest (will fall back on error)")
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    # uv not available - use python -m pytest anyway (might work)
                    pytest_cmd = [sys.executable, "-m", "pytest"]
                    if self.verbose:
                        print("   [WARN] pytest not found, attempting python -m pytest")

        if pytest_cmd is None:
            pytest_cmd = [sys.executable, "-m", "pytest"]

        # Run pytest using subprocess for better control
        if self.verbose:
            cmd_str = " ".join(pytest_cmd + pytest_args)
            print(f"Running tests: {cmd_str}")

        # Use subprocess to run pytest (better for parallel execution)
        # If using uv run and it fails with pyvenv.cfg error, fall back to python -m pytest
        try:
            result = subprocess.run(
                pytest_cmd + pytest_args,
                cwd=PROJECT_ROOT,
                timeout=3600,  # 1 hour timeout
                capture_output=True,  # Capture to check for errors
                text=True,
            )
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr and "pyvenv.cfg" not in result.stderr.lower():
                # Only print stderr if it's not the pyvenv.cfg error
                print(result.stderr, file=sys.stderr)

            # Check if there was a pyvenv.cfg error in stderr
            if result.stderr and ("pyvenv.cfg" in result.stderr.lower() or "failed to locate" in result.stderr.lower()):
                if use_uv:
                    print("\n   [WARN] uv environment not ready (pyvenv.cfg error)")
                    print("   [INFO] Falling back to python -m pytest")
                    print("   [INFO] To fix: Run 'uv sync --dev' to set up the environment\n")
                    # Retry with python -m pytest
                    pytest_cmd = [sys.executable, "-m", "pytest"]
                    result = subprocess.run(
                        pytest_cmd + pytest_args,
                        cwd=PROJECT_ROOT,
                        timeout=3600,
                    )

            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            print("   [FAIL] Test execution timed out")
            exit_code = 1
        except FileNotFoundError as e:
            print(f"   [FAIL] Command not found: {pytest_cmd[0]}")
            if use_uv:
                print("   [INFO] Try running: uv sync --dev")
            else:
                print("   [INFO] Try installing pytest: pip install pytest")
            exit_code = 1
        except Exception as e:
            error_msg = str(e).lower()
            print(f"   [FAIL] Error running tests: {e}")
            if "pyvenv.cfg" in error_msg or "failed to locate" in error_msg:
                print("   [INFO] uv environment issue detected.")
                print("   [INFO] Solution: Run 'uv sync --dev' to set up the environment")
                print("   [INFO] Or use: python -m pytest directly if dependencies are installed")
            exit_code = 1

        # Parse results (simplified - pytest doesn't provide easy JSON output)
        results = {
            "exit_code": exit_code,
            "passed": exit_code == 0,
        }

        return exit_code, results


def check_dependencies() -> bool:
    """Check if required dependencies are installed.

    Returns:
        True if dependencies are available, False otherwise
    """
    try:
        import pytest

        return True
    except ImportError:
        print("[FAIL] pytest not installed. Run: uv sync --dev")
        return False


def main() -> int:
    """Main entry point for test agent.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Check dependencies first
    if not check_dependencies():
        return 1

    parser = argparse.ArgumentParser(description="Test Agent: Detect and execute tests with service management")
    parser.add_argument(
        "--file",
        type=str,
        help="Run specific test file",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Run tests matching pattern",
    )
    parser.add_argument(
        "--unit-only",
        action="store_true",
        help="Run only unit tests (skip integration)",
    )
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="Run only integration tests",
    )
    parser.add_argument(
        "--markers",
        type=str,
        help="Pytest markers to filter by",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel execution",
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Number of parallel workers (default: auto)",
    )
    parser.add_argument(
        "--keep-services",
        action="store_true",
        help="Keep services running after tests",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Attempt to fix test failures automatically",
    )

    args = parser.parse_args()

    # Print header
    print("Test Agent: Detecting and executing tests...\n")

    # Detect tests
    detector = TestDetector()
    all_tests = detector.detect_tests()

    if not all_tests:
        print("[FAIL] No tests found!")
        return 1

    # Filter tests
    test_files = all_tests
    if args.file:
        test_file = Path(args.file)
        if not test_file.is_absolute():
            test_file = PROJECT_ROOT / test_file
        if test_file.exists():
            test_files = [test_file]
        else:
            print(f"[FAIL] Test file not found: {args.file}")
            return 1

    # Filter by type
    if args.unit_only:
        test_files = [t for t in test_files if not detector.is_integration_test(t)]
    elif args.integration_only:
        test_files = [t for t in test_files if detector.is_integration_test(t)]

    # Print test discovery
    unit_tests = [t for t in test_files if not detector.is_integration_test(t)]
    integration_tests = [t for t in test_files if detector.is_integration_test(t)]

    print(f"Test Discovery:")
    print(f"   - Found {len(test_files)} test file(s)")
    print(f"   - {len(unit_tests)} unit test(s)")
    print(f"   - {len(integration_tests)} integration test(s)")
    print()

    # Determine required services
    required_services = detector.get_required_services(test_files)

    # Manage services
    service_manager = ServiceManager(
        keep_services=args.keep_services,
        verbose=args.verbose,
    )

    if required_services:
        print("Service Management:")
        service_status = service_manager.ensure_services(required_services)

        # Print service status
        for service, status in service_status.items():
            status_icon = "[OK]" if status else "[FAIL]"
            print(f"   {status_icon} {service}: {'Running' if status else 'Failed'}")
        print()

        # Check if all required services are running
        if not all(service_status.values()):
            print("[WARN] Some required services are not running")
            print("   Tests may fail or be skipped\n")

    # Run tests
    print("Test Execution:")
    runner = TestRunner(
        service_manager=service_manager,
        verbose=args.verbose,
        auto_fix=args.auto_fix,
    )

    exit_code, results = runner.run_tests(
        test_files=test_files if args.file else None,
        pattern=args.pattern,
        markers=args.markers,
        parallel=not args.no_parallel,
        workers=args.workers,
    )

    # Cleanup
    if args.verbose:
        print("\nCleanup:")
    service_manager.cleanup()

    # Print summary
    print(f"\nTest Summary:")
    if exit_code == 0:
        print("   [PASS] All tests passed!")
    else:
        print("   [FAIL] Some tests failed")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
