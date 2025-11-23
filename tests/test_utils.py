#!/usr/bin/env python3
"""
Test Utilities for MCP Calendar Server Tests

This module provides shared utilities and data structures for test reporting
and test execution.

Author: AI Assistant
Created: 2025-11-16
Updated: 2025-11-22
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class TestReportItem:
    """Test report item with Requirements/Verification/Arrange-Act-Assert structure.
    
    This dataclass represents a single test case result with all the information
    needed to generate a detailed test report following the Requirements/Verification/
    Arrange-Act-Assert format.
    """
    test_name: str
    requirements: List[str] = field(default_factory=list)
    verification: List[str] = field(default_factory=list)
    arrange: List[str] = field(default_factory=list)
    act: List[str] = field(default_factory=list)
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    test_result: str = "PENDING"  # "PASS" | "FAIL" | "SKIP" | "PENDING"
    error: Optional[str] = None
    
    def add_assertion(self, description: str, expected: Any, actual: Any, passed: bool) -> None:
        """Add an assertion result to the test report item.
        
        Args:
            description: Description of what is being asserted
            expected: Expected value
            actual: Actual value
            passed: Whether the assertion passed
        """
        self.assertions.append({
            "description": description,
            "expected": expected,
            "actual": actual,
            "passed": passed
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert test report item to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the test report item
        """
        return {
            "test_name": self.test_name,
            "requirements": self.requirements,
            "verification": self.verification,
            "arrange": self.arrange,
            "act": self.act,
            "assertions": self.assertions,
            "test_result": self.test_result,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestReportItem":
        """Create TestReportItem from dictionary.
        
        Args:
            data: Dictionary with test report item data
            
        Returns:
            TestReportItem instance
        """
        return cls(
            test_name=data.get("test_name", ""),
            requirements=data.get("requirements", []),
            verification=data.get("verification", []),
            arrange=data.get("arrange", []),
            act=data.get("act", []),
            assertions=data.get("assertions", []),
            test_result=data.get("test_result", "PENDING"),
            error=data.get("error")
        )


def create_test_report_item(
    test_name: str,
    requirements: Optional[List[str]] = None,
    verification: Optional[List[str]] = None
) -> TestReportItem:
    """Helper function to create a TestReportItem with common fields.
    
    Args:
        test_name: Name of the test
        requirements: List of requirement statements (optional)
        verification: List of verification steps (optional)
        
    Returns:
        TestReportItem instance
    """
    return TestReportItem(
        test_name=test_name,
        requirements=requirements or [],
        verification=verification or []
    )

