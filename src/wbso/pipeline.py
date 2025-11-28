#!/usr/bin/env python3
"""
WBSO Calendar Upload Pipeline

Unified pipeline that validates, converts, uploads, and verifies WBSO calendar entries.
Implements TOC-AUTO-001: No Calendar Entries in WBSO Calendar (CRITICAL)

This script provides:
- Automated, programmatic calendar insertion
- Single command to run entire pipeline
- Real-time progress tracking
- Post-upload verification
- Comprehensive error reporting

Author: AI Assistant
Created: 2025-11-28
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .validation import WBSODataValidator
from .upload import GoogleCalendarUploader
from .calendar_event import WBSODataset, CalendarEvent, WBSOSession
from .logging_config import get_logger

logger = get_logger("pipeline")

# Default paths
SCRIPT_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours"
DATA_DIR = SCRIPT_DIR / "data"
VALIDATION_OUTPUT_DIR = SCRIPT_DIR / "validation_output"
UPLOAD_OUTPUT_DIR = SCRIPT_DIR / "upload_output"
CREDENTIALS_PATH = SCRIPT_DIR / "scripts" / "credentials.json"
TOKEN_PATH = SCRIPT_DIR / "scripts" / "token.json"
CONFIG_PATH = SCRIPT_DIR / "config" / "wbso_calendar_config.json"

# Target date range
TARGET_START_DATE = datetime(2025, 6, 1)
TARGET_END_DATE = datetime.now()


class WBSOCalendarPipeline:
    """Unified pipeline for WBSO calendar upload with verification."""

    def __init__(self, force_validation: bool = False, dry_run: bool = False):
        """Initialize pipeline."""
        self.force_validation = force_validation
        self.dry_run = dry_run
        self.validator = None
        self.uploader = None
        self.dataset = WBSODataset()
        self.validation_results = None
        self.upload_results = None
        self.verification_results = None

    def step_1_validate(self) -> bool:
        """Step 1: Validate data sources."""
        logger.info("=" * 60)
        logger.info("STEP 1: VALIDATION")
        logger.info("=" * 60)

        cleaned_dataset_path = VALIDATION_OUTPUT_DIR / "cleaned_dataset.json"

        # Check if validation is needed
        if not self.force_validation and cleaned_dataset_path.exists():
            logger.info(f"Using existing validated dataset: {cleaned_dataset_path}")
            try:
                self.dataset.load_from_json(cleaned_dataset_path)
                logger.info(f"Loaded {len(self.dataset.sessions)} sessions from validated dataset")
                return True
            except Exception as e:
                logger.warning(f"Failed to load existing validated dataset: {e}")
                logger.info("Running validation...")

        # Run validation
        logger.info("Running comprehensive validation...")
        self.validator = WBSODataValidator(DATA_DIR)
        self.validation_results = self.validator.run_comprehensive_validation()

        # Check validation results
        summary = self.validation_results.get("summary", {})
        if not summary.get("ready_for_upload", False):
            errors = summary.get("total_errors", 0)
            warnings = summary.get("total_warnings", 0)
            logger.error(f"Validation failed: {errors} errors, {warnings} warnings")
            if errors > 0:
                logger.error("Cannot proceed with upload due to validation errors")
                return False
            logger.warning("Validation has warnings but proceeding...")

        # Export validation reports
        self.validator.export_validation_reports(VALIDATION_OUTPUT_DIR)
        self.dataset = self.validator.dataset

        logger.info(f"✅ Validation complete: {len(self.dataset.sessions)} sessions validated")
        return True

    def step_2_convert(self) -> List[CalendarEvent]:
        """Step 2: Convert sessions to calendar events."""
        logger.info("=" * 60)
        logger.info("STEP 2: CONVERSION")
        logger.info("=" * 60)

        # Filter for WBSO sessions in target date range
        wbso_sessions = []
        for session in self.dataset.sessions:
            if not session.is_wbso:
                continue

            # Filter by date range
            if session.start_time:
                if session.start_time.date() < TARGET_START_DATE.date():
                    continue
                if session.start_time.date() > TARGET_END_DATE.date():
                    continue

            wbso_sessions.append(session)

        logger.info(f"Found {len(wbso_sessions)} WBSO sessions in date range {TARGET_START_DATE.date()} to {TARGET_END_DATE.date()}")

        # Convert to calendar events
        calendar_events = []
        conversion_errors = []

        for session in wbso_sessions:
            try:
                event = CalendarEvent.from_wbso_session(session)
                calendar_events.append(event)
            except Exception as e:
                error_msg = f"Failed to convert session {session.session_id}: {e}"
                logger.error(error_msg)
                conversion_errors.append({"session_id": session.session_id, "error": str(e)})

        logger.info(f"✅ Conversion complete: {len(calendar_events)} events created, {len(conversion_errors)} errors")

        if conversion_errors:
            logger.warning(f"Conversion errors: {len(conversion_errors)} sessions failed")
            for error in conversion_errors[:5]:  # Show first 5
                logger.warning(f"  - {error['session_id']}: {error['error']}")

        return calendar_events

    def step_3_upload(self, calendar_events: List[CalendarEvent]) -> bool:
        """Step 3: Upload events to Google Calendar."""
        logger.info("=" * 60)
        logger.info("STEP 3: UPLOAD")
        logger.info("=" * 60)

        if not calendar_events:
            logger.error("No calendar events to upload")
            return False

        # Initialize uploader
        self.uploader = GoogleCalendarUploader(CREDENTIALS_PATH, TOKEN_PATH, CONFIG_PATH)

        # Upload events
        logger.info(f"Uploading {len(calendar_events)} events to WBSO calendar...")
        self.upload_results = self.uploader.upload_events(calendar_events, dry_run=self.dry_run)

        if self.dry_run:
            logger.info("DRY RUN - No events were actually uploaded")
            plan = self.upload_results.get("upload_plan", {})
            logger.info(f"Would upload: {len(plan.get('new_events', []))} new events")
            logger.info(f"Would skip: {len(plan.get('skip_events', []))} duplicate events")
            return True

        # Check upload success
        success = self.upload_results.get("success", False)
        upload_results_list = self.upload_results.get("upload_results", [])

        if success:
            successful_uploads = [r for r in upload_results_list if r.get("status") == "success"]
            failed_uploads = [r for r in upload_results_list if r.get("status") != "success"]
            logger.info(f"✅ Upload complete: {len(successful_uploads)} successful, {len(failed_uploads)} failed")
        else:
            logger.error("❌ Upload failed")
            errors = self.upload_results.get("errors", [])
            for error in errors[:5]:  # Show first 5 errors
                logger.error(f"  - {error.get('event_summary', 'Unknown')}: {error.get('error_message', 'Unknown error')}")

        return success

    def step_4_verify(self) -> Dict[str, Any]:
        """Step 4: Verify events were actually created in calendar."""
        logger.info("=" * 60)
        logger.info("STEP 4: VERIFICATION")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("DRY RUN - Skipping verification")
            return {"verified": False, "dry_run": True}

        if not self.uploader:
            logger.error("Uploader not initialized - cannot verify")
            return {"verified": False, "error": "Uploader not initialized"}

        # Get calendar ID
        calendar_id = self.uploader.get_wbso_calendar_id()
        if not calendar_id:
            logger.error("WBSO calendar not found - cannot verify")
            return {"verified": False, "error": "Calendar not found"}

        # Query calendar for events in date range
        logger.info(f"Querying calendar for events from {TARGET_START_DATE.date()} to {TARGET_END_DATE.date()}...")
        existing_events_data = self.uploader.get_existing_events(TARGET_START_DATE, TARGET_END_DATE + timedelta(days=1))
        events = existing_events_data.get("events", [])

        # Calculate hours from calendar events
        total_hours = 0.0
        verified_events = []

        for event in events:
            start_str = event.get("start", {}).get("dateTime")
            end_str = event.get("end", {}).get("dateTime")

            if not start_str or not end_str:
                continue

            try:
                start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))

                # Filter by date range
                if start_dt.date() < TARGET_START_DATE.date() or start_dt.date() > TARGET_END_DATE.date():
                    continue

                duration = end_dt - start_dt
                hours = duration.total_seconds() / 3600.0
                total_hours += hours

                verified_events.append({
                    "event_id": event.get("id"),
                    "summary": event.get("summary"),
                    "start": start_str,
                    "end": end_str,
                    "hours": hours,
                })
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error parsing event times: {e}")
                continue

        verification_results = {
            "verified": True,
            "calendar_id": calendar_id,
            "total_events": len(verified_events),
            "total_hours": total_hours,
            "date_range": {
                "start": TARGET_START_DATE.isoformat(),
                "end": TARGET_END_DATE.isoformat(),
            },
            "events": verified_events[:10],  # Include first 10 for reference
        }

        logger.info(f"✅ Verification complete: {len(verified_events)} events, {total_hours:.2f} hours in calendar")
        self.verification_results = verification_results

        return verification_results

    def step_5_report(self) -> None:
        """Step 5: Generate summary report."""
        logger.info("=" * 60)
        logger.info("STEP 5: REPORTING")
        logger.info("=" * 60)

        # Calculate totals
        wbso_sessions = [s for s in self.dataset.sessions if s.is_wbso]
        calculated_hours = sum(s.work_hours for s in wbso_sessions if s.start_time and TARGET_START_DATE.date() <= s.start_time.date() <= TARGET_END_DATE.date())
        calendar_hours = self.verification_results.get("total_hours", 0.0) if self.verification_results else 0.0

        # Generate report
        report = {
            "pipeline_timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "date_range": {
                "start": TARGET_START_DATE.isoformat(),
                "end": TARGET_END_DATE.isoformat(),
            },
            "calculated_hours": calculated_hours,
            "calendar_hours": calendar_hours,
            "gap": calculated_hours - calendar_hours,
            "target_hours": 510.0,
            "target_gap": 510.0 - calendar_hours,
            "validation": {
                "total_sessions": len(self.dataset.sessions),
                "wbso_sessions": len(wbso_sessions),
                "validation_passed": self.validation_results.get("summary", {}).get("validation_passed", False) if self.validation_results else False,
            } if self.validation_results else None,
            "upload": {
                "success": self.upload_results.get("success", False) if self.upload_results else False,
                "new_events": len(self.upload_results.get("upload_plan", {}).get("new_events", [])) if self.upload_results else 0,
                "skipped_events": len(self.upload_results.get("upload_plan", {}).get("skip_events", [])) if self.upload_results else 0,
                "errors": len(self.upload_results.get("errors", [])) if self.upload_results else 0,
            } if self.upload_results else None,
            "verification": self.verification_results,
        }

        # Save report
        UPLOAD_OUTPUT_DIR.mkdir(exist_ok=True)
        report_path = UPLOAD_OUTPUT_DIR / "pipeline_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Print summary
        print(f"\n{'=' * 60}")
        print("WBSO CALENDAR PIPELINE SUMMARY")
        print(f"{'=' * 60}")
        print(f"Date Range: {TARGET_START_DATE.date()} to {TARGET_END_DATE.date()}")
        print(f"Calculated Hours: {calculated_hours:.2f} hours")
        print(f"Calendar Hours: {calendar_hours:.2f} hours")
        print(f"Gap: {calculated_hours - calendar_hours:.2f} hours")
        print(f"Target Hours: 510.0 hours")
        print(f"Target Gap: {510.0 - calendar_hours:.2f} hours")
        print(f"Target Achievement: {(calendar_hours / 510.0 * 100):.1f}%")
        print(f"\nValidation: {'✅ Passed' if report['validation'] and report['validation']['validation_passed'] else '❌ Failed'}")
        print(f"Upload: {'✅ Success' if report['upload'] and report['upload']['success'] else '❌ Failed'}")
        print(f"Verification: {'✅ Verified' if report['verification'] and report['verification'].get('verified') else '❌ Not Verified'}")
        print(f"\nReport saved to: {report_path}")
        print(f"{'=' * 60}\n")

        logger.info(f"✅ Report generated: {report_path}")

    def run(self) -> int:
        """Run the complete pipeline."""
        logger.info("=" * 60)
        logger.info("WBSO CALENDAR UPLOAD PIPELINE")
        logger.info("=" * 60)
        logger.info(f"Dry Run: {'Yes' if self.dry_run else 'No'}")
        logger.info(f"Date Range: {TARGET_START_DATE.date()} to {TARGET_END_DATE.date()}")
        logger.info("")

        try:
            # Step 1: Validate
            if not self.step_1_validate():
                logger.error("Pipeline failed at validation step")
                return 1

            # Step 2: Convert
            calendar_events = self.step_2_convert()
            if not calendar_events:
                logger.error("Pipeline failed at conversion step - no events to upload")
                return 1

            # Step 3: Upload
            if not self.step_3_upload(calendar_events):
                logger.error("Pipeline failed at upload step")
                # Continue to verification even if upload had errors

            # Step 4: Verify
            self.step_4_verify()

            # Step 5: Report
            self.step_5_report()

            # Determine success
            if self.dry_run:
                logger.info("✅ Pipeline completed (dry run)")
                return 0

            calendar_hours = self.verification_results.get("total_hours", 0.0) if self.verification_results else 0.0
            if calendar_hours >= 400.0:
                logger.info(f"✅ Pipeline completed successfully: {calendar_hours:.2f} hours in calendar")
                return 0
            else:
                logger.warning(f"⚠️ Pipeline completed but calendar hours ({calendar_hours:.2f}) below target (400+)")
                return 0  # Still return 0 as pipeline completed, just not enough hours

        except Exception as e:
            logger.error(f"Pipeline failed with exception: {e}", exc_info=True)
            return 1


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="WBSO Calendar Upload Pipeline")
    parser.add_argument("--force-validation", action="store_true", help="Force re-validation even if validated data exists")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode - don't actually upload")
    args = parser.parse_args()

    pipeline = WBSOCalendarPipeline(force_validation=args.force_validation, dry_run=args.dry_run)
    exit_code = pipeline.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

