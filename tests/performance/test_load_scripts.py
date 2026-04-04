"""Validation tests for load test scripts.

As a developer I want to confirm that the load test scripts are present and properly structured,
so that the team can run load tests before releases without surprises.
Technical: Static validation — no backend or external tools required.
"""

from pathlib import Path

SCRIPTS_LOAD_DIR = Path(__file__).parent.parent.parent / "scripts" / "load"


class TestLoadScriptsExist:
    """Validate that all required load test files are present."""

    def test_k6_ask_script_exists(self):
        """As a developer I want the k6 load test script to exist, so I can run it before releases.
        Technical: scripts/load/ask-load.js must be present and non-empty.
        """
        script = SCRIPTS_LOAD_DIR / "ask-load.js"
        assert script.exists(), f"k6 script not found: {script}"
        assert script.stat().st_size > 0, "ask-load.js must not be empty"

    def test_locust_script_exists(self):
        """As a developer I want a locust load test file to exist as an alternative to k6.
        Technical: scripts/load/locustfile.py must be present and non-empty.
        """
        script = SCRIPTS_LOAD_DIR / "locustfile.py"
        assert script.exists(), f"locust script not found: {script}"
        assert script.stat().st_size > 0, "locustfile.py must not be empty"

    def test_readme_exists(self):
        """As a developer I want a README so I can learn how to run load tests.
        Technical: scripts/load/README.md must be present.
        """
        readme = SCRIPTS_LOAD_DIR / "README.md"
        assert readme.exists(), f"README not found: {readme}"
        assert readme.stat().st_size > 0, "README.md must not be empty"


class TestK6ScriptContent:
    """Validate that the k6 script covers required endpoints and defines thresholds."""

    def _read(self) -> str:
        return (SCRIPTS_LOAD_DIR / "ask-load.js").read_text()

    def test_covers_qa_endpoint(self):
        """As a tester I want POST /api/v1/qa covered, so the most expensive RAG path is exercised.
        Technical: ask-load.js must reference /api/v1/qa.
        """
        assert "/api/v1/qa" in self._read()

    def test_covers_retrieval_chunks_endpoint(self):
        """As a tester I want POST /api/v1/retrieval/chunks covered, so retrieval-only path is exercised.
        Technical: ask-load.js must reference /api/v1/retrieval/chunks.
        """
        assert "/api/v1/retrieval/chunks" in self._read()

    def test_covers_health_endpoint(self):
        """As a tester I want GET /api/v1/health covered, so liveness is exercised under load.
        Technical: ask-load.js must reference /api/v1/health.
        """
        assert "/api/v1/health" in self._read()

    def test_defines_thresholds(self):
        """As a tester I want performance thresholds defined, so failures are detected automatically.
        Technical: ask-load.js must define a 'thresholds' block.
        """
        assert "thresholds" in self._read()

    def test_defines_http_req_duration_threshold(self):
        """As a tester I want latency thresholds enforced, so p95 regressions are caught.
        Technical: thresholds must include http_req_duration.
        """
        assert "http_req_duration" in self._read()

    def test_parameterises_base_url(self):
        """As a tester I want the target URL to be overridable, so tests run against different environments.
        Technical: BACKEND_URL environment variable must be used.
        """
        assert "BACKEND_URL" in self._read()


class TestLocustScriptContent:
    """Validate that the locust script covers required endpoints."""

    def _read(self) -> str:
        return (SCRIPTS_LOAD_DIR / "locustfile.py").read_text()

    def test_covers_qa_endpoint(self):
        """As a tester I want POST /api/v1/qa covered in the locust file.
        Technical: locustfile.py must reference /api/v1/qa.
        """
        assert "/api/v1/qa" in self._read()

    def test_covers_retrieval_chunks_endpoint(self):
        """As a tester I want POST /api/v1/retrieval/chunks covered in the locust file.
        Technical: locustfile.py must reference /api/v1/retrieval/chunks.
        """
        assert "/api/v1/retrieval/chunks" in self._read()

    def test_covers_health_endpoint(self):
        """As a tester I want GET /api/v1/health covered in the locust file.
        Technical: locustfile.py must reference /api/v1/health.
        """
        assert "/api/v1/health" in self._read()

    def test_has_locust_user_class(self):
        """As a tester I want a proper Locust User class so the test is runnable.
        Technical: locustfile.py must subclass HttpUser.
        """
        assert "HttpUser" in self._read()

    def test_has_task_decorator(self):
        """As a tester I want task methods decorated with @task so Locust picks them up.
        Technical: locustfile.py must use the @task decorator.
        """
        assert "@task" in self._read()


class TestReadmeContent:
    """Validate that the README documents SLOs and how to run the tests."""

    def _read(self) -> str:
        return (SCRIPTS_LOAD_DIR / "README.md").read_text()

    def test_documents_slos(self):
        """As a developer I want SLOs documented so I know what success looks like.
        Technical: README.md must mention 'SLO' or 'p95' latency targets.
        """
        content = self._read()
        assert "SLO" in content or "p95" in content, "README must document SLOs (SLO or p95)"

    def test_documents_k6_run_command(self):
        """As a developer I want to see how to run k6, so I can execute load tests.
        Technical: README.md must include 'k6 run'.
        """
        assert "k6 run" in self._read()

    def test_documents_locust_run_command(self):
        """As a developer I want to see how to run locust, so I have an alternative tool.
        Technical: README.md must include 'locust'.
        """
        assert "locust" in self._read().lower()

    def test_documents_backend_url(self):
        """As a developer I want to know the target host, so I can point tests at the right environment.
        Technical: README.md must mention 'localhost:9180' or 'BACKEND_URL'.
        """
        content = self._read()
        assert "9180" in content or "BACKEND_URL" in content
