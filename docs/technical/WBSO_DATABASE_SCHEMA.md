# WBSO Database Schema Documentation

## Overview

This document describes the normalized database schema for WBSO (Wet Bevordering Speur- en Ontwikkelingswerk) data storage and management. The schema replaces the previous JSON-based approach with a proper relational database structure using SQLite and SQLAlchemy.

## Table of Contents

1. [Schema Design Principles](#schema-design-principles)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Table Definitions](#table-definitions)
4. [Data Migration Process](#data-migration-process)
5. [Query Examples](#query-examples)
6. [Performance Considerations](#performance-considerations)
7. [Code Files](#code-files)

## Schema Design Principles

### Normalization Benefits

- **Data Integrity**: Foreign key constraints ensure referential integrity
- **Query Performance**: Indexed relationships enable fast joins and aggregations
- **Data Consistency**: Normalized schema prevents data duplication
- **Audit Trail**: Complete transaction history with timestamps
- **Scalability**: Relational structure supports growth and complex queries

### Design Decisions

1. **Repository Separation**: Repositories are stored as separate entities to enable proper categorization and commit tracking
2. **Category Normalization**: WBSO categories are normalized with descriptions and justification templates
3. **Session-Commit Relationship**: Many-to-many relationship between sessions and commits for flexibility
4. **Validation Tracking**: Separate table for validation results with timestamps
5. **Calendar Integration**: Dedicated table for Google Calendar event mapping

## Entity Relationship Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Repository    │    │  WBSOCategory   │    │  WorkSession    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ name (UNIQUE)   │◄───┤ code (UNIQUE)   │◄───┤ session_id (UK) │
│ url             │    │ name            │    │ start_time      │
│ description     │    │ description     │    │ end_time        │
│ created_at      │    │ justification_  │    │ work_hours      │
└─────────────────┘    │ template        │    │ duration_hours  │
         │              │ created_at      │    │ date            │
         │              └─────────────────┘    │ session_type    │
         │                       │              │ is_wbso        │
         │                       │              │ wbso_category_ │
         │                       │              │ id (FK)        │
         │                       │              │ is_synthetic   │
         │                       │              │ repository_id  │
         │                       │              │ (FK)           │
         │                       │              │ wbso_justif... │
         │                       │              │ confidence_... │
         │                       │              │ source_type    │
         │                       │              │ created_at     │
         │                       │              │ updated_at     │
         │                       │              └─────────────────┘
         │                       │                       │
         │                       │                       │
         │                       │              ┌─────────────────┐
         │                       │              │ ValidationResult│
         │                       │              ├─────────────────┤
         │                       │              │ id (PK)         │
         │                       │              │ session_id (FK) │
         │                       │              │ validation_type │
         │                       │              │ is_valid        │
         │                       │              │ error_message   │
         │                       │              │ warning_message │
         │                       │              │ validated_at    │
         │                       │              └─────────────────┘
         │                       │
         │                       │
         │              ┌─────────────────┐
         │              │ CalendarEvent   │
         │              ├─────────────────┤
         │              │ id (PK)         │
         │              │ session_id (FK) │
         │              │ google_event_id │
         │              │ summary         │
         │              │ description     │
         │              │ start_datetime  │
         │              │ end_datetime    │
         │              │ color_id        │
         │              │ location        │
         │              │ transparency    │
         │              │ uploaded_at     │
         │              │ created_at      │
         │              └─────────────────┘
         │
         │
┌─────────────────┐
│     Commit      │
├─────────────────┤
│ id (PK)         │
│ repository_id   │
│ (FK)            │
│ commit_hash     │
│ author          │
│ message         │
│ datetime        │
│ session_id (FK) │
│ created_at      │
└─────────────────┘
```

## Table Definitions

### Repositories Table

Stores repository information for WBSO sessions.

```sql
CREATE TABLE repositories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    url VARCHAR(500),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Centralized repository information to avoid duplication and enable proper categorization.

### WBSO Categories Table

Stores WBSO categories with descriptions and justification templates.

```sql
CREATE TABLE wbso_categories (
    id INTEGER PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    justification_template TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Normalized WBSO categories with standardized descriptions and justification templates.

### Work Sessions Table

Core table storing work session information with WBSO classification.

```sql
CREATE TABLE work_sessions (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    work_hours DECIMAL(5,2) NOT NULL,
    duration_hours DECIMAL(5,2) NOT NULL,
    date DATE NOT NULL,
    session_type VARCHAR(50) NOT NULL,
    is_wbso BOOLEAN NOT NULL DEFAULT FALSE,
    wbso_category_id INTEGER REFERENCES wbso_categories(id),
    is_synthetic BOOLEAN NOT NULL DEFAULT FALSE,
    repository_id INTEGER REFERENCES repositories(id),
    wbso_justification TEXT,
    confidence_score DECIMAL(3,2) DEFAULT 1.0,
    source_type VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Central table linking all WBSO session data with proper foreign key relationships.

### Commits Table

Stores Git commit information associated with work sessions.

```sql
CREATE TABLE commits (
    id INTEGER PRIMARY KEY,
    repository_id INTEGER REFERENCES repositories(id),
    commit_hash VARCHAR(40) NOT NULL,
    author VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    datetime DATETIME NOT NULL,
    session_id VARCHAR(255) REFERENCES work_sessions(session_id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Track Git commits and their association with work sessions for audit trails.

### Calendar Events Table

Stores Google Calendar event information for WBSO sessions.

```sql
CREATE TABLE calendar_events (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES work_sessions(session_id),
    google_event_id VARCHAR(255) UNIQUE,
    summary VARCHAR(500) NOT NULL,
    description TEXT,
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    color_id VARCHAR(10) DEFAULT '1',
    location VARCHAR(255) DEFAULT 'Home Office',
    transparency VARCHAR(20) DEFAULT 'opaque',
    uploaded_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Track Google Calendar integration and event synchronization.

### Validation Results Table

Stores validation results for work sessions.

```sql
CREATE TABLE validation_results (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES work_sessions(session_id),
    validation_type VARCHAR(50) NOT NULL,
    is_valid BOOLEAN NOT NULL,
    error_message TEXT,
    warning_message TEXT,
    validated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Track validation results and data quality metrics.

## Data Migration Process

### Migration Script

The migration process is handled by `src/wbso/migration.py`:

1. **Initialize Reference Data**: Create WBSO categories and repositories
2. **Migrate Work Sessions**: Import from `work_log_complete.json` and `synthetic_sessions.json`
3. **Migrate Commits**: Import from CSV files in `commits/` directory
4. **Migrate Calendar Events**: Import from `wbso_calendar_events.json`
5. **Validate Relationships**: Ensure all foreign key relationships are valid

### Usage

```bash
# Run migration from default data directory
uv run wbso-migrate

# Run migration from custom data directory
uv run wbso-migrate /path/to/data/directory
```

## Query Examples

### Basic WBSO Hours Calculation

```python
from sqlalchemy import func
from src.wbso.database import WorkSession, get_wbso_session

with get_wbso_session() as session:
    # Total WBSO hours
    total_hours = session.query(func.sum(WorkSession.work_hours)).filter(
        WorkSession.is_wbso == True
    ).scalar()

    # Hours by category
    category_hours = session.query(
        WBSOCategory.code,
        func.sum(WorkSession.work_hours)
    ).join(WorkSession).filter(
        WorkSession.is_wbso == True
    ).group_by(WBSOCategory.code).all()
```

### Repository Analysis

```python
# Sessions by repository
repo_sessions = session.query(
    Repository.name,
    func.count(WorkSession.id),
    func.sum(WorkSession.work_hours)
).join(WorkSession).group_by(Repository.id).all()
```

### Validation Summary

```python
# Validation results summary
validation_summary = session.query(
    ValidationResult.validation_type,
    func.count(ValidationResult.id),
    func.sum(func.case([(ValidationResult.is_valid == True, 1)], else_=0))
).group_by(ValidationResult.validation_type).all()
```

## Performance Considerations

### Indexing Strategy

```sql
-- Primary indexes (automatically created)
CREATE INDEX idx_work_sessions_session_id ON work_sessions(session_id);
CREATE INDEX idx_work_sessions_date ON work_sessions(date);
CREATE INDEX idx_work_sessions_is_wbso ON work_sessions(is_wbso);

-- Composite indexes for common queries
CREATE INDEX idx_work_sessions_wbso_date ON work_sessions(is_wbso, date);
CREATE INDEX idx_work_sessions_category_date ON work_sessions(wbso_category_id, date);
CREATE INDEX idx_commits_repo_datetime ON commits(repository_id, datetime);
```

### Query Optimization

1. **Use Joins**: Leverage foreign key relationships for efficient data retrieval
2. **Filter Early**: Apply WHERE clauses before JOINs when possible
3. **Aggregate Functions**: Use SQL aggregation instead of Python loops
4. **Batch Operations**: Use bulk operations for large data imports

## Code Files

- [src/wbso/database.py](src/wbso/database.py) - SQLAlchemy models and database connection management
- [src/wbso/migration.py](src/wbso/migration.py) - Data migration from JSON files to database
- [src/wbso/database_reporting.py](src/wbso/database_reporting.py) - Database-based reporting system
- [tests/test_wbso_database.py](tests/test_wbso_database.py) - Database schema and migration tests

## Related Documentation

- [TASK-039.md](../project/team/tasks/TASK-039.md) - Original WBSO implementation requirements
- [docs/technical/VECTOR_STORE.md](VECTOR_STORE.md) - Project's database architecture patterns
- [src/backend/rag_pipeline/core/metadata_store.py](../../src/backend/rag_pipeline/core/metadata_store.py) - Existing SQLAlchemy patterns
