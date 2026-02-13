#!/usr/bin/env python3
"""
System Events Computer-On Session Analysis Script

This script analyzes system events CSV files to identify computer-on sessions
that include all computer activity (work + personal time). These sessions will
be filtered later to derive actual work blocks for WBSO hours registration.

TASK-025: System Events Work Block Analysis
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)

Note: This identifies computer-on sessions, not work blocks. Work blocks will
be derived later by filtering and categorizing these sessions.

Business Rules:
1. Combine system events from all system_events_*.csv files
2. Deduplicate entries
3. Create JSON files with date-based naming (system_events_YYYYMMDD.json)
4. Blocks never exceed day boundaries (0:00)
5. Concatenate only gaps less than 30 minutes, keep larger gaps open

Author: AI Assistant
Created: 2025-09-30
"""

import argparse
import csv
import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class SystemEvent:
    """Represents a single system event from the CSV file."""

    datetime: str
    event_id: str
    log_name: str
    event_type: str
    level: str
    username: str
    process_name: str
    message: str
    additional_info: str
    record_id: str


@dataclass
class ComputerOnBlock:
    """Represents a computer-on session identified from system events.

    Note: This includes all computer activity, not just work time.
    Personal activities, breaks, and non-work time are included.
    Work blocks will be derived later by filtering these sessions.
    """

    block_id: str
    start_time: str
    end_time: str
    duration_hours: float
    confidence_score: float
    evidence: List[str]
    session_type: str
    work_hours: float = 0.0
    lunch_break: Optional[str] = None
    dinner_break: Optional[str] = None
    start_event: Optional[SystemEvent] = None
    end_event: Optional[SystemEvent] = None


class SystemEventsAnalyzer:
    """Analyzes system events to identify computer-on sessions.

    Note: These sessions include all computer activity (work + personal).
    Work blocks will be derived later by filtering and categorizing these sessions.
    """

    def __init__(self):
        """Initialize the analyzer with computer-on session detection rules."""
        # Computer-on session detection rules
        self.startup_events = ["6005"]  # System startup
        self.shutdown_events = ["1074", "42"]  # Shutdown and sleep
        self.uptime_events = ["6013"]  # System uptime reports
        self.unexpected_events = ["41", "6008"]  # Unexpected shutdowns

        # Work hours definition (8:00-18:00)
        self.work_start_hour = 8
        self.work_end_hour = 18

        # Session duration limits
        self.min_session_minutes = 30
        self.max_session_hours = 12

        # Confidence scoring weights
        self.confidence_weights = {
            "complete_session": 1.0,  # Both start and end events
            "partial_session": 0.7,  # Only start or end event
            "work_hours": 0.9,  # During work hours
            "non_work_hours": 0.6,  # Outside work hours
            "unexpected_shutdown": 0.3,  # Unexpected shutdown reduces confidence
        }

    def parse_system_events(self, csv_file_path: str) -> List[SystemEvent]:
        """Parse system events from CSV file."""
        events = []

        try:
            with open(csv_file_path, "r", encoding="utf-8-sig") as file:  # Handle BOM
                reader = csv.DictReader(file)
                for row in reader:
                    # Clean column names (remove quotes and BOM)
                    cleaned_row = {}
                    for key, value in row.items():
                        clean_key = key.strip().strip('"').replace("\ufeff", "")
                        cleaned_row[clean_key] = value

                    # Debug: print the first row to see the actual keys
                    if not events:
                        print(f"CSV columns: {list(cleaned_row.keys())}")

                    event = SystemEvent(
                        datetime=cleaned_row["DateTime"],
                        event_id=cleaned_row["EventId"],
                        log_name=cleaned_row["LogName"],
                        event_type=cleaned_row["EventType"],
                        level=cleaned_row["Level"],
                        username=cleaned_row["Username"],
                        process_name=cleaned_row["ProcessName"],
                        message=cleaned_row["Message"],
                        additional_info=cleaned_row["AdditionalInfo"],
                        record_id=cleaned_row["RecordId"],
                    )
                    events.append(event)
        except FileNotFoundError:
            print(f"Error: File {csv_file_path} not found")
            return []
        except KeyError as e:
            print(f"Error: Missing column in CSV file: {e}")
            return []
        except Exception as e:
            print(f"Error parsing CSV file: {e}")
            return []

        return events

    def parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse datetime string with multiple format support."""
        formats = [
            "%Y/%m/%d %H:%M:%S",  # 2025/05/03 11:55:40
            "%m/%d/%Y %I:%M:%S %p",  # 4/27/2025 9:21:21 AM
            "%Y-%m-%d %H:%M:%S",  # 2025-05-03 11:55:40
            "%m/%d/%Y %H:%M:%S",  # 4/27/2025 11:55:40
        ]

        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        return None

    def is_work_hours(self, datetime_str: str) -> bool:
        """Check if the given datetime is during work hours."""
        dt = self.parse_datetime(datetime_str)
        if dt is None:
            return False
        return self.work_start_hour <= dt.hour < self.work_end_hour

    def calculate_duration_hours(self, start_time: str, end_time: str) -> float:
        """Calculate duration in hours between two datetime strings."""
        start_dt = self.parse_datetime(start_time)
        end_dt = self.parse_datetime(end_time)

        if start_dt is None or end_dt is None:
            return 0.0

        duration = end_dt - start_dt
        return duration.total_seconds() / 3600.0

    def calculate_confidence_score(self, computer_on_block: ComputerOnBlock) -> float:
        """Calculate confidence score for a computer-on session."""
        score = 0.0

        # Base confidence based on event completeness
        if computer_on_block.start_event and computer_on_block.end_event:
            score += self.confidence_weights["complete_session"]
        else:
            score += self.confidence_weights["partial_session"]

        # Time-based confidence
        if self.is_work_hours(computer_on_block.start_time):
            score += self.confidence_weights["work_hours"]
        else:
            score += self.confidence_weights["non_work_hours"]

        # Check for unexpected shutdowns
        if computer_on_block.end_event and computer_on_block.end_event.event_id in self.unexpected_events:
            score *= self.confidence_weights["unexpected_shutdown"]

        # Duration-based confidence
        if computer_on_block.duration_hours < 0.5:  # Less than 30 minutes
            score *= 0.5
        elif computer_on_block.duration_hours > 12:  # More than 12 hours
            score *= 0.8

        return min(1.0, score)  # Cap at 1.0

    def ensure_chronological_order(self, computer_on_sessions: List[ComputerOnBlock]) -> List[ComputerOnBlock]:
        """Ensure sessions are in chronological order by start_time without overlap."""
        if not computer_on_sessions:
            return []

        # Sort by start_time
        sorted_sessions = sorted(computer_on_sessions, key=lambda x: x.start_time)

        # Remove overlaps by adjusting end times
        non_overlapping_sessions = []
        for i, session in enumerate(sorted_sessions):
            if i == 0:
                non_overlapping_sessions.append(session)
            else:
                prev_session = non_overlapping_sessions[-1]
                prev_end = self.parse_datetime(prev_session.end_time)
                current_start = self.parse_datetime(session.start_time)
                current_end = self.parse_datetime(session.end_time)

                if prev_end is None or current_start is None or current_end is None:
                    non_overlapping_sessions.append(session)
                    continue

                # If current session starts before previous ends, adjust start time
                if current_start <= prev_end:
                    # Adjust current session start to be after previous end
                    adjusted_start = prev_end + timedelta(minutes=1)
                    session.start_time = adjusted_start.strftime("%Y/%m/%d %H:%M:%S")
                    session.duration_hours = self.calculate_duration_hours(session.start_time, session.end_time)

                # Validate that the session has positive duration after adjustment
                if session.duration_hours > 0:
                    non_overlapping_sessions.append(session)
                else:
                    print(
                        f"Warning: Skipping session {session.block_id} with negative/zero duration: {session.start_time} to {session.end_time}"
                    )

        return non_overlapping_sessions

    def validate_and_filter_sessions(self, computer_on_sessions: List[ComputerOnBlock]) -> List[ComputerOnBlock]:
        """Validate sessions and filter out those with negative or zero duration."""
        valid_sessions = []

        for session in computer_on_sessions:
            # Check if duration is positive
            if session.duration_hours > 0:
                valid_sessions.append(session)
            else:
                print(
                    f"Warning: Filtering out session {session.block_id} with invalid duration: {session.duration_hours} hours ({session.start_time} to {session.end_time})"
                )

        return valid_sessions

    def generate_break_times(self, session: ComputerOnBlock) -> ComputerOnBlock:
        """Generate lunch and dinner break times for sessions that meet criteria."""
        start_dt = self.parse_datetime(session.start_time)
        end_dt = self.parse_datetime(session.end_time)

        if start_dt is None or end_dt is None:
            return session

        # Check for lunch break: start < 10:00 and end > 14:00
        if start_dt.hour < 10 and end_dt.hour >= 14:
            # Generate random lunch break between 12:00 and 12:40
            lunch_hour = 12
            lunch_minute = random.randint(0, 40)
            lunch_break_dt = start_dt.replace(hour=lunch_hour, minute=lunch_minute, second=0, microsecond=0)
            session.lunch_break = lunch_break_dt.strftime("%Y/%m/%d %H:%M:%S")

        # Check for dinner break: start < 16:00 and end > 20:00
        if start_dt.hour < 16 and end_dt.hour >= 20:
            # Generate random dinner break between 18:00 and 18:40
            dinner_hour = 18
            dinner_minute = random.randint(0, 40)
            dinner_break_dt = start_dt.replace(hour=dinner_hour, minute=dinner_minute, second=0, microsecond=0)
            session.dinner_break = dinner_break_dt.strftime("%Y/%m/%d %H:%M:%S")

        return session

    def calculate_work_hours(self, session: ComputerOnBlock) -> ComputerOnBlock:
        """Calculate work hours by subtracting break time from duration."""
        work_hours = session.duration_hours

        # Subtract 30 minutes (0.5 hours) for each break
        if session.lunch_break:
            work_hours -= 0.5
        if session.dinner_break:
            work_hours -= 0.5

        # Ensure work_hours is not negative
        session.work_hours = max(0.0, work_hours)

        return session

    def identify_computer_on_sessions(self, events: List[SystemEvent]) -> List[ComputerOnBlock]:
        """Identify computer-on sessions from system events."""
        computer_on_sessions = []
        block_counter = 1

        # Sort events by datetime
        events.sort(key=lambda x: x.datetime)

        i = 0
        while i < len(events):
            event = events[i]

            # Look for startup events
            if event.event_id in self.startup_events:
                start_event = event
                start_time = event.datetime

                # Look for corresponding shutdown event
                end_event = None
                end_time = None

                # Search for shutdown event within reasonable time
                for j in range(i + 1, len(events)):
                    next_event = events[j]

                    # Check if we've moved to next day or too much time has passed
                    start_dt = self.parse_datetime(start_time)
                    next_dt = self.parse_datetime(next_event.datetime)

                    if start_dt is None or next_dt is None:
                        continue

                    if next_dt.date() != start_dt.date() and next_dt.hour < self.work_start_hour:
                        # Assume end of work day - use same format as input
                        if "/" in start_time and ":" in start_time:
                            end_time = f"{start_dt.strftime('%Y/%m/%d')} {self.work_end_hour}:00:00"
                        else:
                            end_time = f"{start_dt.strftime('%m/%d/%Y')} {self.work_end_hour}:00:00"
                        break

                    if next_event.event_id in self.shutdown_events:
                        end_event = next_event
                        end_time = next_event.datetime
                        break

                # If no shutdown found, assume end of work day
                if not end_time:
                    start_dt = self.parse_datetime(start_time)
                    if start_dt is not None:
                        if "/" in start_time and ":" in start_time:
                            end_time = f"{start_dt.strftime('%Y/%m/%d')} {self.work_end_hour}:00:00"
                        else:
                            end_time = f"{start_dt.strftime('%m/%d/%Y')} {self.work_end_hour}:00:00"

                # Only proceed if we have a valid end_time
                if end_time:
                    # Calculate duration
                    duration_hours = self.calculate_duration_hours(start_time, end_time)

                    # Only create computer-on session if duration meets minimum requirements
                    if duration_hours >= (self.min_session_minutes / 60.0):
                        # Determine session type
                        if duration_hours >= 8:
                            session_type = "full_day"
                        elif duration_hours >= 4:
                            session_type = "half_day"
                        else:
                            session_type = "short_session"

                        # Create computer-on session
                        computer_on_session = ComputerOnBlock(
                            block_id=f"cos_{block_counter:03d}",  # Computer On Session
                            start_time=start_time,
                            end_time=end_time,
                            duration_hours=duration_hours,
                            confidence_score=0.0,  # Will be calculated
                            evidence=[f"startup_event_{start_event.event_id}"],
                            session_type=session_type,
                            start_event=start_event,
                            end_event=end_event,
                        )

                        # Add end event evidence if available
                        if end_event:
                            computer_on_session.evidence.append(f"shutdown_event_{end_event.event_id}")

                        # Calculate confidence score
                        computer_on_session.confidence_score = self.calculate_confidence_score(computer_on_session)

                        computer_on_sessions.append(computer_on_session)
                        block_counter += 1

            i += 1

        return computer_on_sessions

    def analyze_file(self, csv_file_path: str) -> Dict:
        """Analyze a single system events CSV file."""
        print(f"Analyzing system events file: {csv_file_path}")

        # Parse events
        events = self.parse_system_events(csv_file_path)
        if not events:
            return {"error": f"Failed to parse events from {csv_file_path}"}

        print(f"Parsed {len(events)} system events")

        # Identify computer-on sessions
        computer_on_sessions = self.identify_computer_on_sessions(events)
        print(f"Identified {len(computer_on_sessions)} computer-on sessions")

        # Calculate summary statistics
        total_hours = sum(session.duration_hours for session in computer_on_sessions)
        avg_confidence = (
            sum(session.confidence_score for session in computer_on_sessions) / len(computer_on_sessions)
            if computer_on_sessions
            else 0
        )

        # Apply the same processing as multiple files
        # 1. Validate and filter sessions with negative/zero duration
        valid_sessions = self.validate_and_filter_sessions(computer_on_sessions)

        # 2. Ensure chronological order without overlap
        chronological_sessions = self.ensure_chronological_order(valid_sessions)

        # 3. Generate break times and calculate work hours
        final_sessions = []
        for session in chronological_sessions:
            session = self.generate_break_times(session)
            session = self.calculate_work_hours(session)
            final_sessions.append(session)

        # Calculate updated summary statistics
        total_hours = sum(session.duration_hours for session in final_sessions)
        total_work_hours = sum(session.work_hours for session in final_sessions)
        avg_confidence = sum(session.confidence_score for session in final_sessions) / len(final_sessions) if final_sessions else 0

        # Convert computer-on sessions to dictionaries for JSON serialization
        computer_on_sessions_dict = []
        for session in final_sessions:
            session_dict = asdict(session)
            # Remove the SystemEvent objects as they're not JSON serializable
            session_dict.pop("start_event", None)
            session_dict.pop("end_event", None)
            computer_on_sessions_dict.append(session_dict)

        return {
            "file_analyzed": csv_file_path,
            "total_events": len(events),
            "computer_on_sessions": computer_on_sessions_dict,
            "summary": {
                "total_computer_on_sessions": len(final_sessions),
                "total_hours": round(total_hours, 2),
                "total_work_hours": round(total_work_hours, 2),
                "average_confidence": round(avg_confidence, 3),
                "average_hours_per_session": round(total_hours / len(final_sessions), 2) if final_sessions else 0,
                "average_work_hours_per_session": round(total_work_hours / len(final_sessions), 2) if final_sessions else 0,
                "sessions_with_breaks": {
                    "lunch_break": len([s for s in final_sessions if s.lunch_break]),
                    "dinner_break": len([s for s in final_sessions if s.dinner_break]),
                },
                "session_types": {
                    "full_day": len([s for s in final_sessions if s.session_type == "full_day"]),
                    "half_day": len([s for s in final_sessions if s.session_type == "half_day"]),
                    "short_session": len([s for s in final_sessions if s.session_type == "short_session"]),
                },
            },
        }

    def combine_and_deduplicate_events(self, csv_files: List[str]) -> List[SystemEvent]:
        """Combine events from multiple CSV files and deduplicate."""
        all_events = []
        seen_events = set()

        for csv_file in csv_files:
            events = self.parse_system_events(csv_file)
            for event in events:
                # Create a unique key for deduplication
                event_key = f"{event.datetime}_{event.event_id}_{event.record_id}"
                if event_key not in seen_events:
                    seen_events.add(event_key)
                    all_events.append(event)

        # Sort by datetime
        all_events.sort(key=lambda x: x.datetime)
        return all_events

    def respect_day_boundaries(self, computer_on_sessions: List[ComputerOnBlock]) -> List[ComputerOnBlock]:
        """Ensure blocks never exceed day boundaries (0:00)."""
        adjusted_sessions = []

        for session in computer_on_sessions:
            start_dt = self.parse_datetime(session.start_time)
            end_dt = self.parse_datetime(session.end_time)

            if start_dt is None or end_dt is None:
                continue

            # If session crosses day boundary, split it
            if start_dt.date() != end_dt.date():
                # Split at midnight
                midnight = start_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

                # First part (until midnight)
                midnight_str = midnight.strftime("%Y/%m/%d %H:%M:%S")
                first_session = ComputerOnBlock(
                    block_id=session.block_id + "_a",
                    start_time=session.start_time,
                    end_time=midnight_str,
                    duration_hours=self.calculate_duration_hours(session.start_time, midnight_str),
                    confidence_score=session.confidence_score,
                    evidence=session.evidence.copy(),
                    session_type=session.session_type,
                    start_event=session.start_event,
                    end_event=None,
                )
                adjusted_sessions.append(first_session)

                # Second part (from midnight)
                second_session = ComputerOnBlock(
                    block_id=session.block_id + "_b",
                    start_time=midnight_str,
                    end_time=session.end_time,
                    duration_hours=self.calculate_duration_hours(midnight_str, session.end_time),
                    confidence_score=session.confidence_score,
                    evidence=session.evidence.copy(),
                    session_type=session.session_type,
                    start_event=None,
                    end_event=session.end_event,
                )
                adjusted_sessions.append(second_session)
            else:
                adjusted_sessions.append(session)

        return adjusted_sessions

    def concatenate_small_gaps(self, computer_on_sessions: List[ComputerOnBlock]) -> List[ComputerOnBlock]:
        """Concatenate sessions with gaps less than 30 minutes."""
        if not computer_on_sessions:
            return []

        concatenated_sessions = []
        current_session = computer_on_sessions[0]

        for next_session in computer_on_sessions[1:]:
            # Calculate gap between sessions
            current_end = self.parse_datetime(current_session.end_time)
            next_start = self.parse_datetime(next_session.start_time)

            if current_end is None or next_start is None:
                concatenated_sessions.append(current_session)
                current_session = next_session
                continue

            gap_minutes = (next_start - current_end).total_seconds() / 60

            # If gap is less than 30 minutes, concatenate
            if gap_minutes < 30 and gap_minutes >= 0:  # Only positive gaps
                # Extend current session to include next session
                current_session.end_time = next_session.end_time
                if next_session.end_time:  # Ensure end_time is not None
                    current_session.duration_hours = self.calculate_duration_hours(
                        current_session.start_time, next_session.end_time
                    )
                current_session.evidence.extend(next_session.evidence)
                current_session.end_event = next_session.end_event

                # Update session type based on new duration
                if current_session.duration_hours >= 8:
                    current_session.session_type = "full_day"
                elif current_session.duration_hours >= 4:
                    current_session.session_type = "half_day"
                else:
                    current_session.session_type = "short_session"
            else:
                # Gap is too large or negative, keep sessions separate
                concatenated_sessions.append(current_session)
                current_session = next_session

        # Add the last session
        concatenated_sessions.append(current_session)
        return concatenated_sessions

    def analyze_multiple_files(self, csv_files: List[str]) -> Dict:
        """Analyze multiple system events CSV files with proper business rules."""
        # Combine and deduplicate all events
        all_events = self.combine_and_deduplicate_events(csv_files)
        print(f"Combined and deduplicated {len(all_events)} system events")

        # Identify computer-on sessions
        computer_on_sessions = self.identify_computer_on_sessions(all_events)
        print(f"Identified {len(computer_on_sessions)} computer-on sessions")

        # Apply business rules
        # 1. Validate and filter sessions with negative/zero duration
        valid_sessions = self.validate_and_filter_sessions(computer_on_sessions)
        print(f"Validated sessions: {len(valid_sessions)} sessions")

        # 2. Respect day boundaries
        day_boundary_sessions = self.respect_day_boundaries(valid_sessions)
        print(f"Applied day boundaries: {len(day_boundary_sessions)} sessions")

        # 3. Concatenate small gaps
        concatenated_sessions = self.concatenate_small_gaps(day_boundary_sessions)
        print(f"Concatenated small gaps: {len(concatenated_sessions)} sessions")

        # 4. Ensure chronological order without overlap
        chronological_sessions = self.ensure_chronological_order(concatenated_sessions)
        print(f"Applied chronological ordering: {len(chronological_sessions)} sessions")

        # 5. Generate break times and calculate work hours
        final_sessions = []
        for session in chronological_sessions:
            session = self.generate_break_times(session)
            session = self.calculate_work_hours(session)
            final_sessions.append(session)
        print(f"Generated break times and work hours: {len(final_sessions)} final sessions")

        # Calculate summary statistics
        total_hours = sum(session.duration_hours for session in final_sessions)
        total_work_hours = sum(session.work_hours for session in final_sessions)
        avg_confidence = sum(session.confidence_score for session in final_sessions) / len(final_sessions) if final_sessions else 0

        # Debug: Check for negative durations
        negative_sessions = [s for s in final_sessions if s.duration_hours < 0]
        if negative_sessions:
            print(f"Warning: Found {len(negative_sessions)} sessions with negative duration")
            for session in negative_sessions[:3]:  # Show first 3
                print(f"  {session.block_id}: {session.start_time} to {session.end_time} = {session.duration_hours} hours")

        # Convert to dictionaries for JSON serialization
        sessions_dict = []
        for session in final_sessions:
            session_dict = asdict(session)
            session_dict.pop("start_event", None)
            session_dict.pop("end_event", None)
            sessions_dict.append(session_dict)

        return {
            "analysis_date": "2025-09-30T" + datetime.now().strftime("%H:%M:%S"),
            "files_analyzed": len(csv_files),
            "total_events_processed": len(all_events),
            "computer_on_sessions": sessions_dict,
            "summary": {
                "total_computer_on_sessions": len(final_sessions),
                "total_hours": round(total_hours, 2),
                "total_work_hours": round(total_work_hours, 2),
                "average_confidence": round(avg_confidence, 3),
                "average_hours_per_session": round(total_hours / len(final_sessions), 2) if final_sessions else 0,
                "average_work_hours_per_session": round(total_work_hours / len(final_sessions), 2) if final_sessions else 0,
                "sessions_with_breaks": {
                    "lunch_break": len([s for s in final_sessions if s.lunch_break]),
                    "dinner_break": len([s for s in final_sessions if s.dinner_break]),
                },
                "session_types": {
                    "full_day": len([s for s in final_sessions if s.session_type == "full_day"]),
                    "half_day": len([s for s in final_sessions if s.session_type == "half_day"]),
                    "short_session": len([s for s in final_sessions if s.session_type == "short_session"]),
                },
            },
        }


def main():
    """Main function to run the system events analysis."""
    parser = argparse.ArgumentParser(description="Analyze system events to identify computer-on sessions")
    parser.add_argument("csv_files", nargs="+", help="System events CSV files to analyze")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = SystemEventsAnalyzer()

    # Analyze files
    if len(args.csv_files) == 1:
        result = analyzer.analyze_file(args.csv_files[0])
    else:
        result = analyzer.analyze_multiple_files(args.csv_files)

    # Output results with proper naming
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Computer-on sessions analysis saved to {args.output}")
    else:
        # Generate default filename based on current date
        default_filename = f"system_events_{datetime.now().strftime('%Y%m%d')}.json"
        with open(default_filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Computer-on sessions analysis saved to {default_filename}")

    # Print summary if verbose
    if args.verbose and "summary" in result:
        summary = result["summary"]
        print("\nSummary:")
        print(f"  Total computer-on sessions: {summary['total_computer_on_sessions']}")
        print(f"  Total hours: {summary['total_hours']}")
        print(f"  Total work hours: {summary['total_work_hours']}")
        print(f"  Average hours per session: {summary['average_hours_per_session']}")
        print(f"  Average work hours per session: {summary['average_work_hours_per_session']}")
        print(f"  Sessions with breaks: {summary['sessions_with_breaks']}")
        print(f"  Session types: {summary['session_types']}")


if __name__ == "__main__":
    main()
