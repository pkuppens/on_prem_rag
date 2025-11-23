#!/usr/bin/env python3
"""
Update Date Tags Script

This script checks and updates date tags (Created: and Updated:) in markdown
and code files according to the date-formatting rule.

It ensures all files comply with the date formatting standards:
- Adds Created: tag to files missing it (with current date)
- Adds Updated: tag to files missing it (with current date)
- Updates Updated: tag in files where it's outdated (with current date)
- Preserves existing Created: tags (never modifies them)

Author: AI Assistant
Created: 2025-11-22
Updated: 2025-11-22
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

# File patterns to process
MARKDOWN_PATTERNS = ["*.md", "*.markdown"]
CODE_PATTERNS = [
    "*.py", "*.ts", "*.tsx", "*.js", "*.jsx",
    "*.java", "*.go", "*.rs", "*.cpp", "*.cxx", "*.cc", "*.c", "*.h", "*.cs"
]

# Directories to exclude
EXCLUDED_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache", "dist", "build"}

# Files to exclude
EXCLUDED_FILES = {
    "package-lock.json", "poetry.lock", "yarn.lock", "Pipfile.lock",
    "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", "*.exe"
}


def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


def find_date_tag(line: str) -> Optional[Tuple[str, str]]:
    """Find date tag in a line.
    
    Returns:
        Tuple of (tag_type, date) if found, None otherwise.
        tag_type is 'created' or 'updated'
    """
    # Pattern for Created: or Updated: tags
    patterns = [
        (r"Created:\s*(\d{4}-\d{2}-\d{2})", "created"),
        (r"Updated:\s*(\d{4}-\d{2}-\d{2})", "updated"),
        (r"Date:\s*(\d{4}-\d{2}-\d{2})", "created"),  # Legacy Date: tag
    ]
    
    for pattern, tag_type in patterns:
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            return (tag_type, match.group(1))
    
    return None


def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed."""
    # Check if in excluded directory
    for part in file_path.parts:
        if part in EXCLUDED_DIRS:
            return False
    
    # Check if excluded file pattern
    for pattern in EXCLUDED_FILES:
        if file_path.match(pattern):
            return False
    
    # Check file size (skip large files > 10MB)
    try:
        if file_path.stat().st_size > 10 * 1024 * 1024:
            return False
    except (OSError, ValueError):
        return False
    
    return True


def get_file_patterns(file_path: Path) -> List[str]:
    """Get file patterns that match this file."""
    patterns = []
    
    if file_path.suffix in [".md", ".markdown"]:
        patterns.extend(MARKDOWN_PATTERNS)
    
    if file_path.suffix in [".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs",
                            ".cpp", ".cxx", ".cc", ".c", ".h", ".cs"]:
        patterns.extend(CODE_PATTERNS)
    
    return patterns


def find_files_to_process(root_dir: Path, include_patterns: Optional[List[str]] = None,
                         exclude_patterns: Optional[List[str]] = None) -> List[Path]:
    """Find all files to process."""
    files = []
    
    # Build include patterns
    if include_patterns:
        patterns = include_patterns
    else:
        patterns = MARKDOWN_PATTERNS + CODE_PATTERNS
    
    # Find files
    for pattern in patterns:
        for file_path in root_dir.rglob(pattern):
            if should_process_file(file_path):
                # Check exclude patterns
                if exclude_patterns:
                    excluded = False
                    for exclude in exclude_patterns:
                        if exclude in str(file_path) or file_path.match(exclude):
                            excluded = True
                            break
                    if excluded:
                        continue
                
                files.append(file_path)
    
    # Remove duplicates and sort
    files = sorted(set(files))
    return files


def analyze_file(file_path: Path, current_date: str) -> dict:
    """Analyze a file for date tag compliance.
    
    Returns:
        Dictionary with analysis results:
        - has_created: bool
        - has_updated: bool
        - created_date: str or None
        - updated_date: str or None
        - needs_created: bool
        - needs_updated: bool
        - needs_update: bool (Updated tag needs updating)
    """
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return {"error": str(e)}
    
    lines = content.split('\n')
    has_created = False
    has_updated = False
    created_date = None
    updated_date = None
    created_line_idx = None
    updated_line_idx = None
    
    # Find existing date tags
    for idx, line in enumerate(lines):
        result = find_date_tag(line)
        if result:
            tag_type, date = result
            if tag_type == "created":
                has_created = True
                created_date = date
                created_line_idx = idx
            elif tag_type == "updated":
                has_updated = True
                updated_date = date
                updated_line_idx = idx
    
    # Determine what needs to be done
    needs_created = not has_created
    needs_updated = not has_updated
    needs_update = has_updated and updated_date != current_date
    
    return {
        "has_created": has_created,
        "has_updated": has_updated,
        "created_date": created_date,
        "updated_date": updated_date,
        "created_line_idx": created_line_idx,
        "updated_line_idx": updated_line_idx,
        "needs_created": needs_created,
        "needs_updated": needs_updated,
        "needs_update": needs_update,
        "lines": lines,
    }


def update_file(file_path: Path, analysis: dict, current_date: str) -> bool:
    """Update a file with date tags.
    
    Returns:
        True if file was modified, False otherwise.
    """
    if analysis.get("error"):
        return False
    
    lines = analysis["lines"]
    modified = False
    
    # Add or update Updated tag
    if analysis["needs_updated"] or analysis["needs_update"]:
        if analysis["updated_line_idx"] is not None:
            # Update existing Updated tag
            line = lines[analysis["updated_line_idx"]]
            new_line = re.sub(
                r"Updated:\s*\d{4}-\d{2}-\d{2}",
                f"Updated: {current_date}",
                line,
                flags=re.IGNORECASE
            )
            if new_line != line:
                lines[analysis["updated_line_idx"]] = new_line
                modified = True
        else:
            # Add new Updated tag
            # Try to add after Created tag if it exists
            if analysis["created_line_idx"] is not None:
                insert_idx = analysis["created_line_idx"] + 1
                lines.insert(insert_idx, f"Updated: {current_date}")
                modified = True
            else:
                # Add at the beginning of file (after shebang if present)
                insert_idx = 1 if lines and lines[0].startswith("#!") else 0
                lines.insert(insert_idx, f"Updated: {current_date}")
                modified = True
    
    # Add Created tag if missing
    if analysis["needs_created"]:
        # Try to add after author or at beginning
        insert_idx = 0
        for idx, line in enumerate(lines[:20]):  # Check first 20 lines
            if "Author:" in line or "author:" in line.lower():
                insert_idx = idx + 1
                break
        
        lines.insert(insert_idx, f"Created: {current_date}")
        modified = True
    
    if modified:
        try:
            file_path.write_text('\n'.join(lines), encoding='utf-8')
            return True
        except Exception as e:
            print(f"ERROR - Failed to write {file_path}: {e}", file=sys.stderr)
            return False
    
    return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check and update date tags in markdown and code files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )
    parser.add_argument(
        "--include",
        type=str,
        help="Comma-separated list of directories/patterns to include"
    )
    parser.add_argument(
        "--exclude",
        type=str,
        help="Comma-separated list of directories/patterns to exclude"
    )
    parser.add_argument(
        "--fix-format",
        action="store_true",
        help="Fix wrong date formats (not yet implemented)"
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root directory to scan (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Get current date
    current_date = get_current_date()
    
    # Parse include/exclude patterns
    include_patterns = None
    if args.include:
        include_patterns = [p.strip() for p in args.include.split(",")]
    
    exclude_patterns = None
    if args.exclude:
        exclude_patterns = [p.strip() for p in args.exclude.split(",")]
    
    # Find root directory
    root_dir = Path(args.root).resolve()
    if not root_dir.exists():
        print(f"ERROR - Root directory not found: {root_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Find files to process
    print("INFO - Scanning files for date tag compliance...")
    print(f"INFO - Current date: {current_date}")
    files = find_files_to_process(root_dir, include_patterns, exclude_patterns)
    print(f"INFO - Found {len(files)} files to check")
    print()
    
    if not files:
        print("INFO - No files found to process")
        sys.exit(0)
    
    # Analyze files
    stats = {
        "total": len(files),
        "needs_created": 0,
        "needs_updated": 0,
        "needs_update": 0,
        "compliant": 0,
        "errors": 0,
        "modified": 0,
    }
    
    files_to_update = []
    
    print("INFO - Processing files...")
    for file_path in files:
        analysis = analyze_file(file_path, current_date)
        
        if "error" in analysis:
            stats["errors"] += 1
            continue
        
        if analysis["needs_created"]:
            stats["needs_created"] += 1
            files_to_update.append((file_path, analysis))
        elif analysis["needs_updated"]:
            stats["needs_updated"] += 1
            files_to_update.append((file_path, analysis))
        elif analysis["needs_update"]:
            stats["needs_update"] += 1
            files_to_update.append((file_path, analysis))
        else:
            stats["compliant"] += 1
    
    # Update files
    if not args.dry_run:
        for file_path, analysis in files_to_update:
            if update_file(file_path, analysis, current_date):
                stats["modified"] += 1
                action = []
                if analysis["needs_created"]:
                    action.append("Added Created tag")
                if analysis["needs_updated"]:
                    action.append("Added Updated tag")
                if analysis["needs_update"]:
                    action.append("Updated Updated tag")
                print(f"INFO - {'; '.join(action)} in: {file_path}")
    else:
        # Dry run - just report
        for file_path, analysis in files_to_update:
            action = []
            if analysis["needs_created"]:
                action.append("Would add Created tag")
            if analysis["needs_updated"]:
                action.append("Would add Updated tag")
            if analysis["needs_update"]:
                action.append("Would update Updated tag")
            print(f"INFO - {'; '.join(action)} in: {file_path}")
    
    # Print summary
    print()
    print("INFO - " + "=" * 50)
    print("INFO - UPDATE SUMMARY")
    print("INFO - " + "=" * 50)
    print(f"INFO - Total files scanned: {stats['total']}")
    print(f"INFO - Files with Created tag added: {stats['needs_created']}")
    print(f"INFO - Files with Updated tag added: {stats['needs_updated']}")
    print(f"INFO - Files with Updated tag updated: {stats['needs_update']}")
    print(f"INFO - Files already compliant: {stats['compliant']}")
    if stats["errors"] > 0:
        print(f"INFO - Files with errors: {stats['errors']}")
    if args.dry_run:
        print("INFO - ")
        print("INFO - DRY RUN MODE - No files were modified")
        print("INFO - Run without --dry-run to apply changes")
    else:
        print(f"INFO - Total files modified: {stats['modified']}")


if __name__ == "__main__":
    main()

