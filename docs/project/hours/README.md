# WBSO Hours Registration Utilities

This directory contains utility files and scripts for generating WBSO (Dutch R&D tax deduction) compliant hours registration documentation across multiple repositories.

## Project Overview

This system retrofits WBSO hours registration to achieve a 510+ hour target by capturing:

- **Git commits** across multiple repositories (prioritizing AI agent/privacy/security development)
- **GitHub issues** (creation, management, investigation) - focusing on AI/privacy/security issues
- **Documentation work** and analysis activities (technical documentation for WBSO-AICM-2025-01)
- **Cross-repository coordination** and context switching
- **Dedicated WBSO Google Calendar** with color-coded non-declarable activities
- **Manual processes** are acceptable - not everything needs to be automated
- **WBSO-aligned activities** - prioritizing approved AI agent R&D tasks over general development

For detailed project planning, see [PROJECT_PLAN.md](PROJECT_PLAN.md).

## Files

### Current Files (Single Repository)

- `git_commit_history.txt` - Raw git log output with timestamps
- `commit_analysis.txt` - Detailed daily analysis with WBSO activities
- `weekly_summary.txt` - Weekly hours summary
- `wbso_activities.txt` - WBSO activity categorization summary
- `process_commits.py` - Current single-repo processing script

### Data Files

- `data/system_events_*.csv` - System event logs for workstation activity tracking
- `data/SYSTEM_EVENTS_FORMAT.md` - Documentation for system events data format
- `data/repositories.csv` - Repository configuration for multi-repo extraction

### Planned Structure (Multi-Repository)

```
docs/project/hours/
├── PROJECT_PLAN.md                 # Comprehensive project plan
├── README.md                       # This file (updated)
├── scripts/
│   ├── multi_repo_extractor.py     # Multi-repository data extraction
│   ├── github_issue_analyzer.py    # GitHub issue analysis
│   ├── calendar_integration.py     # Google Calendar integration
│   ├── hour_optimizer.py           # Hour allocation optimization
│   └── report_generator.py         # Final report generation
├── data/
│   ├── repositories.json           # Repository configuration
│   ├── issues/                     # Extracted issue data
│   ├── commits/                    # Extracted commit data
│   └── sessions/                   # Processed work sessions
├── config/
│   ├── wbso_categories.json        # WBSO activity categories
│   ├── hour_allocations.json       # Hour allocation rules
│   └── calendar_config.json        # Calendar configuration
└── reports/
    ├── baseline_analysis.md        # Initial analysis
    ├── final_report.md             # Final WBSO report
    └── compliance_validation.md    # Compliance documentation
```

## Workflow

### Current Workflow (Single Repository)

#### 1. Extract Git History

```bash
# Extract complete commit history with timestamps
git log --pretty=format:"%ad %at %s" --date=short --reverse --all > docs/project/hours/git_commit_history.txt
```

#### 2. Process Commits

```bash
cd docs/project/hours
python process_commits.py
```

#### 3. Review Output

- Check `commit_analysis.txt` for detailed daily entries
- Review `weekly_summary.txt` for weekly totals
- Examine `wbso_activities.txt` for activity categorization

### Planned Workflow (Multi-Repository)

#### Phase 1: Repository Discovery

1. Create repository inventory in `data/repositories.json`
2. Set up GitHub API access tokens
3. Extract commit history from all repositories

#### Phase 2: Supplementary Activity Capture

1. Identify gaps where commit history may miss discarded or uncommitted work.
2. Collect supplementary sources such as workstation login/logout logs to capture complete effort.
3. Reconcile these events with commit timelines to produce a realistic WBSO ground truth.

#### Phase 3: GitHub Issue Analysis

1. Extract issues using GitHub API
2. Categorize issues by type and complexity
3. Assign realistic hour allocations

#### Phase 4: Multi-Repository Integration

1. Combine all repository data
2. Detect cross-repository work sessions
3. Optimize hour allocations to reach 510+ target

#### Phase 5: Dedicated WBSO Google Calendar and Conflict Detection

1. Create dedicated "WBSO Activities" Google Calendar
2. Implement color coding for WBSO vs non-declarable activities
3. Manually review and identify non-declarable activities (appointments, personal time, etc.)
4. Create WBSO calendar events for work sessions (avoiding conflicts)
5. Include proper descriptions and WBSO categorization
6. Set up manual calendar export and review processes

#### Phase 6: Final Reporting

1. Generate comprehensive WBSO reports
2. Validate compliance and time allocations
3. Create final documentation package

## AI Agent Implementation

### Agent Prompts and Tools

- Use existing scripts as ground truth for transformations.
- Example prompt: "Given git_commit_history.txt, run process_commits.py to generate commit_analysis.txt, weekly_summary.txt, and wbso_activities.txt."
- Required tools: `git` for history extraction and `python` for running analysis scripts.

### Design Principles

- Keep agents small and focused on single tasks.
- Ensure outputs can be directly compared to script-generated files for easy verification.

## Features

### Current Features (Single Repository)

#### Time Range Calculation

- Automatically groups commits into work sessions
- Adds realistic buffer time (30 minutes before/after commits)
- Handles time wrapping and edge cases
- Ensures reasonable work hours (8:00-18:00)

#### Break Management

- Automatically adds lunch breaks (30 minutes) when sessions end between 12:00-14:00
- Adds dinner breaks (1.5 hours) when sessions end after 18:00
- Breaks are not counted in total WBSO hours

#### WBSO Activity Categorization

- Analyzes commit messages for R&D keywords
- Categorizes activities into:
  - Research and investigation
  - Development and implementation
  - Innovation and optimization
  - Technical implementation
  - Quality assurance and testing

#### Weekly Summaries

- Groups sessions by ISO week numbers
- Calculates total hours per week
- Provides session breakdowns

### Planned Features (Multi-Repository)

#### Multi-Repository Support

- Extract and process commits from multiple repositories
- Cross-repository work session detection
- Unified hour tracking across all repositories

#### GitHub Issue Integration

- Extract issues using GitHub API
- Categorize issues by type (bug, feature, investigation, documentation)
- Assign realistic hour allocations based on issue complexity
- Link issues to related commits

#### Hour Optimization

- Analyze current totals vs 510 target
- Implement generous but justifiable time allocations
- Add context switching and coordination time
- Include research and investigation time

#### Dedicated WBSO Google Calendar and Conflict Detection

- Create dedicated "WBSO Activities" Google Calendar
- Implement color coding for WBSO vs non-declarable activities
- Manual calendar export and review processes
- Detect conflicts with existing calendar items (appointments, personal time, etc.)
- Identify and categorize non-declarable activities
- Generate calendar events for work sessions (avoiding conflicts)
- Include proper descriptions and WBSO categorization
- Enable calendar-based WBSO reporting
- Manual conflict resolution and editing processes

#### Enhanced Reporting

- Comprehensive WBSO reports with activity breakdowns
- Compliance validation and documentation
- Audit trail for tax authorities
- Professional documentation package

## WBSO Compliance

### Current Compliance Features

The generated documentation includes:

- Clear R&D activity descriptions
- Technical language demonstrating innovation
- Proper time tracking with breaks
- Weekly summaries for tax reporting
- Link to project objectives and outcomes

### Enhanced Compliance (Planned)

- Multi-repository R&D activity tracking
- GitHub issue-based documentation work
- Comprehensive audit trail across all repositories
- Professional documentation package for tax authorities
- 510+ hour target achievement with proper justification

## Usage Notes

### Current Usage (Single Repository)

- All times are rounded to 5-minute intervals
- Sessions with gaps > 2 hours are split into separate sessions
- Only sessions with 0.5-12 hours duration are included
- Breaks are automatically inserted based on work patterns
- WBSO activities are generated based on commit message analysis

### Planned Usage (Multi-Repository)

- Multi-repository data extraction and processing
- GitHub issue analysis and hour allocation
- Cross-repository work session detection
- Dedicated WBSO Google Calendar with color coding
- Manual calendar export and review processes
- Calendar conflict detection and non-declarable activity identification
- Hour optimization to reach 510+ target

## Hour Allocation Strategy

### WBSO-Approved Activities (Priority - AI Agent Project)

- **AI Framework Development**: 3-6 hours per significant commit (core R&D work)
- **Access Control Systems**: 2-5 hours per authorization mechanism
- **Privacy-Preserving Algorithms**: 2-5 hours per anonymization/pseudonymization implementation
- **Audit Logging Systems**: 2-4 hours per privacy-friendly logging mechanism
- **Data Integrity Protection**: 2-4 hours per corruption prevention system
- **Natural Language Processing**: 2-4 hours per intent recognition feature
- **Jailbreak Detection**: 2-4 hours per security mechanism
- **Cloud Integration Research**: 1-3 hours per cloud safety investigation

### Standard Development Activities

- **Development Work**: 2-4 hours per significant commit
- **Bug Fixes**: 1-3 hours depending on complexity
- **Refactoring**: 2-6 hours for major refactoring
- **Documentation**: 1-2 hours per documentation commit

### Issue-Based Hours

- **AI/Privacy Technical Investigation**: 2-4 hours per technical investigation issue
- **Security Feature Planning**: 1-3 hours per security/privacy feature issue
- **Data Protection Bug Analysis**: 1-2 hours per data integrity bug report
- **Privacy Compliance Research**: 2-4 hours per AVG/privacy compliance issue
- **Issue Creation**: 0.5-1 hour per issue (documentation work)

### Additional Hours

- **Context Switching**: 0.5-1 hour between different repositories
- **Research and Learning**: 1-3 hours per research session
- **Testing and Validation**: 1-2 hours per testing session
- **Code Review**: 0.5-1 hour per review session

### Non-Declarable Activities (Solo Developer Context)

- **Personal Appointments**: Dentist, doctor, personal meetings, family time
- **Break Time**: Lunch breaks, coffee breaks, personal time, exercise
- **Travel Time**: Commuting, personal travel
- **Administrative Tasks**: Non-technical paperwork, general administration
- **Personal Development**: Non-R&D learning, hobbies, personal projects
- **Health and Wellness**: Medical appointments, therapy, wellness activities

## Maintenance

### Current Maintenance

- Update git history files before processing
- Review and adjust WBSO activity keywords as needed
- Validate time ranges against actual work patterns
- Keep utility files organized in this directory

### Planned Maintenance

- Multi-repository data synchronization
- GitHub API rate limit management
- Manual WBSO calendar maintenance and updates
- Regular compliance validation and updates
- Calendar export and review process maintenance

## References

- [PROJECT_PLAN.md](PROJECT_PLAN.md)

## Related Tasks

- [TASK-025: System Events Work Block Analysis](../../project/team/tasks/TASK-025.md) - Analyze system events to define work blocks
- [TASK-026: Integrate System Events Work Blocks with Git Commit Analysis](../../project/team/tasks/TASK-026.md) - Combine system events and Git commits for comprehensive hours tracking

## Code Files

- [docs/project/hours/process_commits.py](docs/project/hours/process_commits.py) - Single-repository commit processing example.
- [docs/project/hours/scripts/](docs/project/hours/scripts/) - Helper scripts for multi-repository extraction.
