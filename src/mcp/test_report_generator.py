#!/usr/bin/env python3
"""
Test Report Generator for MCP Calendar Server

This module generates markdown test reports comparing test results
vs expected outcomes for MCP calendar server integration tests.

Author: AI Assistant
Created: 2025-11-15
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class TestReportGenerator:
    """Generate markdown test reports from test results."""

    def __init__(self, results_file: Optional[Path] = None, output_file: Optional[Path] = None):
        """Initialize report generator.

        Args:
            results_file: Path to JSON test results file (defaults to tests/test_results_mcp_calendar.json)
            output_file: Optional output file path (defaults to tests/test_report_mcp_calendar.md)
        """
        if results_file is None:
            # Default to tests directory
            results_file = Path(__file__).parent.parent.parent / "tests" / "test_results_mcp_calendar.json"
        self.results_file = Path(results_file)
        
        if output_file is None:
            # Default output file
            output_file = Path(__file__).parent.parent.parent / "tests" / "test_report_mcp_calendar.md"
        self.output_file = Path(output_file)
        self.results: Dict[str, Any] = {}

    def load_results(self) -> bool:
        """Load test results from JSON file.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(self.results_file, "r") as f:
                self.results = json.load(f)
            return True
        except FileNotFoundError:
            print(f"Test results file not found: {self.results_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return False

    def generate_report(self) -> str:
        """Generate markdown test report.

        Returns:
            Markdown report as string
        """
        if not self.results:
            return "# Test Report\n\nNo test results available.\n"

        report_lines = []
        report_lines.append("# MCP Calendar Server Integration Test Report\n")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Test Summary
        report_lines.append("## Test Summary\n")
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r.get("status") == "PASS")
        failed_tests = sum(1 for r in self.results.values() if r.get("status") == "FAIL")
        skipped_tests = sum(1 for r in self.results.values() if r.get("status") == "SKIP")

        report_lines.append(f"- **Total Tests**: {total_tests}")
        report_lines.append(f"- **Passed**: {passed_tests} ✅")
        report_lines.append(f"- **Failed**: {failed_tests} ❌")
        report_lines.append(f"- **Skipped**: {skipped_tests} ⚠️")
        report_lines.append(f"- **Success Rate**: {(passed_tests / total_tests * 100):.1f}%\n")

        # Per-Tool Test Results
        report_lines.append("## Per-Tool Test Results\n")

        test_order = [
            "list_calendars",
            "create_events",
            "read_events",
            "summarize_events",
            "detect_duplicates",
            "edit_event",
            "delete_events",
            "full_workflow",
        ]

        for test_name in test_order:
            if test_name not in self.results:
                continue

            result = self.results[test_name]
            status = result.get("status", "UNKNOWN")

            # Status symbol
            if status == "PASS":
                status_symbol = "✅"
            elif status == "FAIL":
                status_symbol = "❌"
            elif status == "SKIP":
                status_symbol = "⚠️"
            else:
                status_symbol = "❓"

            report_lines.append(f"### {test_name.replace('_', ' ').title()} {status_symbol}\n")
            report_lines.append(f"**Status**: {status}\n")

            # Test-specific details
            if test_name == "list_calendars":
                calendar_count = result.get("calendar_count", 0)
                report_lines.append(f"- **Calendars Found**: {calendar_count}")
                if calendar_count > 0:
                    report_lines.append(f"- **Expected**: At least 1 calendar")
                    report_lines.append(f"- **Result**: {'✅ PASS' if calendar_count >= 1 else '❌ FAIL'}")

            elif test_name == "create_events":
                created_count = result.get("created_count", 0)
                expected_count = 3
                report_lines.append(f"- **Events Created**: {created_count}")
                report_lines.append(f"- **Expected**: {expected_count}")
                report_lines.append(f"- **Result**: {'✅ PASS' if created_count == expected_count else '❌ FAIL'}")
                if "events" in result:
                    report_lines.append("\n**Created Events:**")
                    for event in result["events"]:
                        report_lines.append(f"  - {event.get('summary', 'Unknown')} (ID: {event.get('id', 'Unknown')})")

            elif test_name == "read_events":
                total_events = result.get("total_events", 0)
                test_events = result.get("test_events", 0)
                expected = result.get("expected_test_events", 3)
                report_lines.append(f"- **Total Events Found**: {total_events}")
                report_lines.append(f"- **Test Events Found**: {test_events}")
                report_lines.append(f"- **Expected Test Events**: {expected}")
                report_lines.append(f"- **Result**: {'✅ PASS' if test_events == expected else '❌ FAIL'}")

            elif test_name == "summarize_events":
                total_items = result.get("total_items", 0)
                total_days = result.get("total_days", 0)
                total_hours = result.get("total_hours", 0.0)
                expected_items = result.get("expected_items", 3)
                expected_days = result.get("expected_days", 3)
                expected_hours = result.get("expected_hours", 6.0)

                report_lines.append(f"- **Total Items**: {total_items} (Expected: {expected_items})")
                report_lines.append(f"- **Total Days**: {total_days} (Expected: {expected_days})")
                report_lines.append(f"- **Total Hours**: {total_hours} (Expected: {expected_hours})")

                items_ok = total_items == expected_items
                days_ok = total_days == expected_days
                hours_ok = abs(total_hours - expected_hours) < 0.1

                report_lines.append(f"- **Result**: {'✅ PASS' if items_ok and days_ok and hours_ok else '❌ FAIL'}")

            elif test_name == "detect_duplicates":
                duplicates_found = result.get("duplicates_found", 0)
                expected = result.get("expected_duplicates", 0)
                report_lines.append(f"- **Duplicates Found**: {duplicates_found}")
                report_lines.append(f"- **Expected**: {expected}")
                report_lines.append(f"- **Result**: {'✅ PASS' if duplicates_found == expected else '❌ FAIL'}")

            elif test_name == "edit_event":
                if "event_id" in result:
                    report_lines.append(f"- **Event ID**: {result['event_id']}")
                    report_lines.append(f"- **Updated Summary**: {result.get('updated_summary', 'N/A')}")
                    report_lines.append("- **Result**: ✅ PASS")
                elif "reason" in result:
                    report_lines.append(f"- **Reason**: {result['reason']}")
                    report_lines.append("- **Result**: ⚠️ SKIP")

            elif test_name == "delete_events":
                deleted_count = result.get("deleted_count", 0)
                expected_count = result.get("expected_count", 0)
                report_lines.append(f"- **Events Deleted**: {deleted_count}")
                report_lines.append(f"- **Expected**: {expected_count}")
                report_lines.append(f"- **Result**: {'✅ PASS' if deleted_count == expected_count else '❌ FAIL'}")

            elif test_name == "full_workflow":
                passed_steps = result.get("passed_steps", 0)
                failed_steps = result.get("failed_steps", 0)
                total_steps = result.get("total_steps", 0)
                report_lines.append(f"- **Passed Steps**: {passed_steps}/{total_steps}")
                report_lines.append(f"- **Failed Steps**: {failed_steps}")
                report_lines.append(f"- **Result**: {'✅ PASS' if failed_steps == 0 else '❌ FAIL'}")

            # Error details
            if "error" in result:
                report_lines.append(f"\n**Error**: {result['error']}")

            report_lines.append("")  # Empty line between tests

        # Expected vs Actual Outcomes
        report_lines.append("## Expected vs Actual Outcomes\n")
        report_lines.append("| Test | Expected | Actual | Status |")
        report_lines.append("|------|----------|--------|--------|")

        for test_name in test_order:
            if test_name not in self.results:
                continue

            result = self.results[test_name]
            status = result.get("status", "UNKNOWN")

            if test_name == "list_calendars":
                expected = "At least 1 calendar"
                actual = f"{result.get('calendar_count', 0)} calendars"
            elif test_name == "create_events":
                expected = "3 events created"
                actual = f"{result.get('created_count', 0)} events created"
            elif test_name == "read_events":
                expected = "3 test events found"
                actual = f"{result.get('test_events', 0)} test events found"
            elif test_name == "summarize_events":
                expected = "3 items, 3 days, 6.0 hours"
                actual = f"{result.get('total_items', 0)} items, {result.get('total_days', 0)} days, {result.get('total_hours', 0.0)} hours"
            elif test_name == "detect_duplicates":
                expected = "0 duplicates"
                actual = f"{result.get('duplicates_found', 0)} duplicates"
            elif test_name == "edit_event":
                expected = "Event updated successfully"
                actual = "Updated" if "event_id" in result else "Skipped"
            elif test_name == "delete_events":
                expected = "All test events deleted"
                actual = f"{result.get('deleted_count', 0)} events deleted"
            elif test_name == "full_workflow":
                expected = "All steps pass"
                actual = f"{result.get('passed_steps', 0)}/{result.get('total_steps', 0)} steps passed"
            else:
                expected = "N/A"
                actual = "N/A"

            status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            report_lines.append(f"| {test_name.replace('_', ' ').title()} | {expected} | {actual} | {status_symbol} {status} |")

        report_lines.append("")

        # Error Details
        error_tests = {k: v for k, v in self.results.items() if "error" in v}
        if error_tests:
            report_lines.append("## Error Details\n")
            for test_name, result in error_tests.items():
                report_lines.append(f"### {test_name.replace('_', ' ').title()}\n")
                report_lines.append(f"**Error**: {result['error']}\n")

        # Recommendations
        report_lines.append("## Recommendations\n")

        if failed_tests > 0:
            report_lines.append("### Failed Tests\n")
            report_lines.append("The following tests failed and should be investigated:\n")
            for test_name, result in self.results.items():
                if result.get("status") == "FAIL":
                    report_lines.append(f"- **{test_name.replace('_', ' ').title()}**: {result.get('error', 'Unknown error')}")
            report_lines.append("")

        if skipped_tests > 0:
            report_lines.append("### Skipped Tests\n")
            report_lines.append("The following tests were skipped:\n")
            for test_name, result in self.results.items():
                if result.get("status") == "SKIP":
                    report_lines.append(f"- **{test_name.replace('_', ' ').title()}**: {result.get('reason', 'No reason provided')}")
            report_lines.append("")

        if failed_tests == 0 and skipped_tests == 0:
            report_lines.append("✅ All tests passed successfully! The MCP calendar server is functioning correctly.\n")

        return "\n".join(report_lines)

    def save_report(self) -> bool:
        """Save report to file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            report_content = self.generate_report()
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"Test report saved to: {self.output_file}")
            return True
        except Exception as e:
            print(f"Error saving report: {e}")
            return False


def main():
    """Main entry point for report generator."""
    import sys

    results_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    generator = TestReportGenerator(results_file, output_file)

    if not generator.load_results():
        if results_file is None:
            print(f"No test results file found at default location: {generator.results_file}")
            print("Run tests first: uv run pytest tests/test_mcp_calendar_server.py -v -m internet")
        sys.exit(1)

    if not generator.save_report():
        sys.exit(1)

    print(f"Report generation complete! Report saved to: {generator.output_file}")


if __name__ == "__main__":
    main()

