# WBSO Hours Registration Retrofit Project Plan

## Project Overview

**Goal**:

- Retrofit WBSO hours registration across multiple repositories to reach or exceed the 510-hour target by capturing GitHub commits and issue creation/management activities.
- Use the hours-registration project as a worked example and use case for agentic development, aiming for a 100% accurate AI agent with curated inputs and outputs.
- Document that initial hours registration started but paused after a few weeks pending project approval; those early records serve as ground truth for agent development.
- Develop agent skills for new use cases such as interpreting local computer event logs for sign-on/sign-off events from natural language, without granting external or cloud agents direct access to the computer.

**Scope**: Multi-repository analysis including development work, documentation, investigation, and work analysis tasks.

## Requirements Analysis

### Primary Requirements

1. **Target Hours**: Achieve 510+ hours for WBSO compliance
2. **Multi-Repository**: Capture work across all development repositories
3. **Comprehensive Coverage**: Include both commits and GitHub issues
4. **WBSO-Aligned Activities**: Prioritize hours registration on approved WBSO tasks and technical development work
5. **Dedicated WBSO Google Calendar**: Create a specific Google Calendar for WBSO activities with color-coded non-declarable items
6. **Conflict Detection**: Detect existing calendar items to avoid double-counting and identify non-declarable activities
7. **Flexible Implementation**: Manual processes and calendar exports are acceptable; not everything needs to be automated
8. **Reporting Tools**: Tools for hour calculation and reporting (can include manual processes)
9. **Generous Allocation**: Justify higher hour allocations for thorough work documentation, and reading of documentation as part of investigating solutions to technical problems.

### Secondary Requirements

1. **WBSO Compliance**: Ensure all activities qualify for R&D tax deduction
2. **Audit Trail**: Maintain clear documentation for tax authorities
3. **Activity Categorization**: Proper classification of R&D activities
4. **Time Validation**: Realistic time allocations with proper breaks
5. **Approved Task Alignment**: Focus on technical development tasks that align with WBSO project goals
6. **Technical Innovation Documentation**: Document technical challenges and innovative solutions
7. **Verifiable Micro-Agents**: Implement small, focused AI agents with clear prompts and minimal tools so their transformations mirror example scripts.

## Current State Analysis

### Existing Infrastructure

- ✅ Basic commit processing script (`process_commits.py`)
- ✅ WBSO activity categorization
- ✅ Weekly summary generation
- ✅ Time range calculation with breaks
- ✅ Single repository analysis

### Gaps Identified

- ❌ Multi-repository aggregation
- ❌ GitHub issue analysis
- ❌ Google Calendar integration
- ❌ Calendar conflict detection and non-declarable activity identification
- ❌ 510+ hour target planning
- ❌ Cross-repository work session detection
- ❌ Issue creation as documentation work

## Detailed Action Plan

### Phase 1: Work Retrieval and Data Collection

#### 1.1 Repository Discovery and Inventory

**Pre-condition**: None - starting point

- [x] **Step 1.1.1: Identify All WBSO-Related Repositories**

- **Goal**: Create a complete list of repositories where WBSO work was performed
- **Execution**:
  - List all GitHub repositories under your account

```
    gh repo list pkuppens > data/repositories_all.csv
```

- Review each repository for AI agent, privacy, security, or RAG-related work
- Document repository name, URL, and primary WBSO relevance
- **Validation**:

  - [x] CSV file `data/repositories.csv` with columns: repo_name, repo_description, wbso_relevance
  - [x] All repositories reviewed and categorized by WBSO relevance
  - [x] Repository descriptions accurately reflect WBSO project alignment

- [ ] **Step 1.1.2: Verify Repository Access**

- **Pre-condition**: Step 1.1.1 completed
- **Goal**: Ensure all repositories are accessible for data extraction
- **Execution**:

  - **Step 1.1.2.1: Navigate to Repository Parent Directory**

    - Change to the project parent directory: `C:\Users\piete\Repos\pkuppens`
    - Verify current working directory is correct for repository management

  - **Step 1.1.2.2: Parse Repository List**

    - Read `data/repositories.csv` file (CSV with header and quoted fields)
    - Extract repository names from the `repo_name` column
    - Convert repository names to GitHub URLs (format: `https://github.com/{repo_name}`)
    - Handle any special characters or formatting in repository names

  - **Step 1.1.2.3: Create Repository Management Script**

    - Create a batch file/shell script that:
      - Reads the repository list from CSV
      - For each repository:
        - Check if directory already exists
        - If exists: run `git pull` to update
        - If not exists: run `git clone {github_url}`
        - Handle errors gracefully (network issues, access denied, etc.)
        - Log success/failure for each repository
    - Script should be executable and handle all repositories in the list

  - **Step 1.1.2.4: Execute Repository Management**

    - Run the created script to clone/update all repositories
    - Verify each repository is accessible and contains expected content
    - Document any repositories that fail to clone or update
    - Test GitHub API access with personal access token for each repository

  - **Step 1.1.2.5: Document Access Status**
    - Create a status report of all repositories
    - List any access issues or failed operations
    - Verify all repositories are ready for data extraction

- **Validation**:
  - [x] All repositories successfully cloned or updated in `C:\Users\piete\Repos\pkuppens`
  - [x] Repository management script created and functional
  - [x] GitHub API access confirmed for all repositories
  - [x] No critical access issues preventing data extraction
  - [x] All repository directories contain expected content
        NOTE: Script did not work for pulling when the directory existed, but that could be fixed with git_pull_all.sh script.

#### 1.2 Git Commit Data Extraction

- [ ] **Step 1.2.1: Extract Git Logs for Each Repository** _(READY FOR EXECUTION)_

- **Pre-condition**: Step 1.1.2 completed
- **Goal**: Retrieve all commit data with timestamps and metadata
- **Execution**:
  - For each repository, go to the repo and run: `git log --pretty=format:"%ad|%at|%s|%an|%H" --date=iso --reverse --all`
  - Save output to this repo, relative to this file in: `data/commits/{repo_name}.csv`
    - including column names: datetime, timestamp, message, author, hash
  - **Scripts created**: `extract_git_commits.bat` and `extract_git_commits.ps1`
- **Validation**:

  - [ ] CSV files created for each repository with columns: datetime, timestamp, message, author, hash
  - [ ] All repositories processed successfully
  - [ ] No errors during git log extraction

- [x] **Step 1.2.2: Standardize Timestamp Format**

_Obsolete, git log format is adequate_

- **Pre-condition**: Step 1.2.1 completed
- **Goal**: Convert all timestamps to YYYY-MM-DD HH:MM:SS format
- **Execution**:
  - Parse Unix timestamps in timestamp column
  - Convert to YYYY-MM-DD HH:MM:SS format
  - Update CSV files with standardized datetime column
- **Validation**:

  - [x] All timestamps in consistent YYYY-MM-DD HH:MM:SS format
  - [x] No timestamp parsing errors
  - [x] All commit files updated with standardized format

- [ ] **Step 1.2.3: Add Repository Context to Commits**

- **Pre-condition**: Step 1.2.2 completed
- **Goal**: Include repository information in commit data
- **Execution**:
  - Add repo_name column to each commit record
  - Merge all commit files into single `data/all_commits.csv`
- **Validation**:
  - [ ] Single CSV file with all commits including repository context
  - [ ] All repository commits successfully merged
  - [ ] Repository context correctly added to all commits

#### 1.3 GitHub Issue Data Extraction

- [ ] **Step 1.3.1: Set Up GitHub API Access**

- **Pre-condition**: Step 1.1.2 completed
- **Goal**: Configure GitHub API access for issue extraction
- **Execution**:
  - Create GitHub personal access token with repo scope
  - Test API access with simple repository query
  - Document API rate limits and usage
- **Validation**:

  - [ ] Successfully retrieve repository information via API
  - [ ] GitHub personal access token configured correctly
  - [ ] API rate limits documented

- [ ] **Step 1.3.2: Extract Issues for Each Repository**

- **Pre-condition**: Step 1.3.1 completed
- **Goal**: Retrieve all issues with creation dates and descriptions
- **Execution**:
  - Use GitHub API to fetch all issues for each repository
  - Extract: issue_number, title, body, created_at, updated_at, state, labels
  - Save to `data/issues/{repo_name}_issues.csv`
- **Validation**:

  - [ ] CSV files created for each repository with issue data
  - [ ] All repositories processed for issues
  - [ ] Issue data includes all required fields

- [ ] **Step 1.3.3: Standardize Issue Timestamps**

- **Pre-condition**: Step 1.3.2 completed
- **Goal**: Convert issue timestamps to consistent format
- **Execution**:
  - Parse GitHub API timestamps (ISO 8601 format)
  - Convert to YYYY-MM-DD HH:MM:SS format
  - Update CSV files with standardized datetime columns
- **Validation**: All issue timestamps in YYYY-MM-DD HH:MM:SS format

### Phase 2: Data Processing and Work Item Creation

#### 2.1 Data Consolidation

- [ ] **Step 2.1.1: Create Unified Data Store**

- **Pre-condition**: Steps 1.2.3 and 1.3.3 completed
- **Goal**: Consolidate all data into single SQLite database
- **Execution**:
  - Create SQLite database `data/wbso_hours.db`
  - Import commits from `data/all_commits.csv`
  - Import issues from all `data/issues/*.csv` files
  - Create indexes on timestamp and repository columns
- **Validation**: SQLite database with commits and issues tables, proper indexes

- [ ] **Step 2.1.2: Group Items by Day**

- **Pre-condition**: Step 2.1.1 completed
- **Goal**: Organize all work items by calendar date
- **Execution**:
  - Extract date portion from timestamps (YYYY-MM-DD)
  - Group commits and issues by date
  - Create daily summary view in database
- **Validation**: Database view showing all work items grouped by date

#### 2.2 Work Session Detection

- [ ] **Step 2.2.1: Define Work Session Rules**

- **Pre-condition**: Step 2.1.2 completed
- **Goal**: Establish rules for grouping work into sessions
- **Execution**:
  - Define maximum gap between items (e.g., 2 hours)
  - Define minimum session duration (e.g., 30 minutes)
  - Define maximum session duration (e.g., 12 hours)
  - Document rules in `config/session_rules.json`
- **Validation**: Configuration file with clear session grouping rules

- [ ] **Step 2.2.2: Group Work Items into Sessions**

- **Pre-condition**: Step 2.2.1 completed
- **Goal**: Create work sessions from individual commits and issues
- **Execution**:
  - Apply session rules to group items by day
  - Create session_id for each work session
  - Calculate session start/end times
  - Store sessions in database
- **Validation**: Database table with work sessions, each containing multiple commits/issues

- [ ] **Step 2.2.3: Adjust Sessions to Reasonable Work Blocks**

- **Pre-condition**: Step 2.2.2 completed
- **Goal**: Ensure sessions represent realistic work periods
- **Execution**:
  - Review sessions longer than 8 hours and split if needed
  - Add buffer time (30 min before/after) to sessions
  - Ensure sessions don't overlap with non-work hours (e.g., 22:00-06:00)
  - Update session records in database
- **Validation**: All sessions represent realistic work periods with proper buffers

### Phase 3: Work Item to Hours Conversion

#### 3.1 Commit-Based Hour Allocation

- [ ] **Step 3.1.1: Define Commit Hour Allocation Rules**

- **Pre-condition**: Step 2.2.3 completed
- **Goal**: Establish rules for converting commits to hours
- **Execution**:
  - Create rules for different commit types (AI framework, security, etc.)
  - Define base hours per commit type
  - Create complexity multipliers based on commit message analysis
  - Document rules in `config/commit_hours.json`
- **Validation**: Configuration file with commit-to-hours mapping rules

- [ ] **Step 3.1.2: Analyze Commit Messages for WBSO Relevance**

- **Pre-condition**: Step 3.1.1 completed
- **Goal**: Categorize commits by WBSO project relevance
- **Execution**:
  - Scan commit messages for AI/privacy/security keywords
  - Categorize commits as: AI_FRAMEWORK, ACCESS_CONTROL, PRIVACY, SECURITY, GENERAL
  - Apply WBSO relevance score (0-1) to each commit
  - Update database with categorization
- **Validation**: Database table with categorized commits and relevance scores

- [ ] **Step 3.1.3: Calculate Hours for Each Commit**

- **Pre-condition**: Step 3.1.2 completed
- **Goal**: Assign hours to each commit based on rules and relevance
- **Execution**:
  - Apply base hours for commit type
  - Multiply by WBSO relevance score
  - Apply complexity multipliers
  - Store calculated hours in database
- **Validation**: Database table with hours assigned to each commit

#### 3.2 Issue-Based Hour Allocation

- [ ] **Step 3.2.1: Define Issue Hour Allocation Rules**

- **Pre-condition**: Step 3.1.3 completed
- **Goal**: Establish rules for converting issues to hours
- **Execution**:
  - Create rules for different issue types (bug, feature, investigation)
  - Define base hours per issue type
  - Create complexity multipliers based on issue labels and content
  - Document rules in `config/issue_hours.json`
- **Validation**: Configuration file with issue-to-hours mapping rules

- [ ] **Step 3.2.2: Analyze Issues for WBSO Relevance**

- **Pre-condition**: Step 3.2.1 completed
- **Goal**: Categorize issues by WBSO project relevance
- **Execution**:
  - Scan issue titles and bodies for AI/privacy/security keywords
  - Categorize issues as: TECHNICAL_INVESTIGATION, SECURITY_FEATURE, PRIVACY_COMPLIANCE, GENERAL
  - Apply WBSO relevance score (0-1) to each issue
  - Update database with categorization
- **Validation**: Database table with categorized issues and relevance scores

- [ ] **Step 3.2.3: Calculate Hours for Each Issue**

- **Pre-condition**: Step 3.2.2 completed
- **Goal**: Assign hours to each issue based on rules and relevance
- **Execution**:
  - Apply base hours for issue type
  - Multiply by WBSO relevance score
  - Apply complexity multipliers
  - Store calculated hours in database
- **Validation**: Database table with hours assigned to each issue

### Phase 4: Declarable Task Allocation

#### 4.1 WBSO Activity Categorization

- [ ] **Step 4.1.1: Define WBSO Activity Categories**

- **Pre-condition**: Step 3.2.3 completed
- **Goal**: Map work to approved WBSO activity categories
- **Execution**:
  - Define categories based on WBSO form: AI_FRAMEWORK, ACCESS_CONTROL, PRIVACY_CLOUD, AUDIT_LOGGING, DATA_INTEGRITY
  - Create mapping rules from commit/issue categories to WBSO categories
  - Document mapping in `config/wbso_categories.json`
- **Validation**: Configuration file with WBSO category mapping rules

- [ ] **Step 4.1.2: Categorize All Work Items**

- **Pre-condition**: Step 4.1.1 completed
- **Goal**: Assign WBSO categories to all work items
- **Execution**:
  - Apply mapping rules to commits and issues
  - Assign primary WBSO category to each work item
  - Store categorization in database
- **Validation**: Database table with WBSO categories assigned to all work items

- [ ] **Step 4.1.3: Calculate Declarable Hours**

- **Pre-condition**: Step 4.1.2 completed
- **Goal**: Calculate total declarable hours by WBSO category
- **Execution**:
  - Sum hours for each WBSO category
  - Calculate percentage distribution across categories
  - Generate summary report
- **Validation**: Report showing total hours and distribution by WBSO category

#### 4.2 Hour Optimization and Target Achievement

- [ ] **Step 4.2.1: Analyze Current Total vs 510 Target**

- **Pre-condition**: Step 4.1.3 completed
- **Goal**: Determine gap to 510-hour target
- **Execution**:
  - Calculate total declarable hours
  - Compare to 510-hour target
  - Identify shortfall or excess
- **Validation**: Report showing current total vs target with gap analysis

- [ ] **Step 4.2.2: Identify Optimization Opportunities**

- **Pre-condition**: Step 4.2.1 completed
- **Goal**: Find ways to reach 510-hour target
- **Execution**:
  - Review low-scoring commits/issues for missed hours
  - Identify additional research/learning time
  - Look for context switching and coordination time
  - Document optimization opportunities
- **Validation**: List of specific opportunities to increase hours

- [ ] **Step 4.2.3: Apply Generous but Justifiable Allocations**

- **Pre-condition**: Step 4.2.2 completed
- **Goal**: Reach 510+ hours with reasonable justification
- **Execution**:
  - Apply additional hours to identified opportunities
  - Add research and investigation time
  - Include documentation and planning time
  - Update database with optimized hours
- **Validation**: Total hours >= 510 with clear justification for each addition

### Phase 5: Calendar Integration and Conflict Detection

#### 5.1 Calendar Setup and Access

- [ ] **Step 5.1.1: Create Dedicated WBSO Google Calendar**

- **Pre-condition**: Step 4.2.3 completed
- **Goal**: Set up dedicated calendar for WBSO activities
- **Execution**:
  - Create new Google Calendar named "WBSO Activities"
  - Set up color coding: WBSO activities (blue), non-declarable (red)
  - Configure sharing settings for export
- **Validation**: Dedicated Google Calendar created with proper settings

- [ ] **Step 5.1.2: Export Existing Calendar Data**

- **Pre-condition**: Step 5.1.1 completed
- **Goal**: Get existing calendar items for conflict detection
- **Execution**:
  - Export personal calendar data for relevant time period
  - Export work calendar data if applicable
  - Save as CSV files for analysis
- **Validation**: CSV files with existing calendar items

- [ ] **Step 5.1.3: Identify Non-Declarable Activities**

- **Pre-condition**: Step 5.1.2 completed
- **Goal**: Mark existing calendar items as non-declarable
- **Execution**:
  - Review exported calendar items
  - Mark appointments, personal time, breaks as non-declarable
  - Create list of non-declarable time periods
- **Validation**: List of non-declarable activities with time periods

#### 5.2 WBSO Calendar Event Creation

- [ ] **Step 5.2.1: Create WBSO Calendar Events**

- **Pre-condition**: Step 5.1.3 completed
- **Goal**: Add WBSO work sessions to calendar
- **Execution**:
  - For each work session, create calendar event
  - Use session start/end times
  - Add description with WBSO category and work details
  - Color-code as WBSO activity (blue)
- **Validation**: Calendar populated with WBSO work sessions

- [ ] **Step 5.2.2: Add Non-Declarable Events**

- **Pre-condition**: Step 5.2.1 completed
- **Goal**: Mark non-declarable time periods in calendar
- **Execution**:
  - Create calendar events for non-declarable activities
  - Use appropriate descriptions (e.g., "Dentist Appointment", "Lunch Break")
  - Color-code as non-declarable (red)
- **Validation**: Calendar shows both WBSO and non-declarable activities

- [ ] **Step 5.2.3: Resolve Calendar Conflicts**

- **Pre-condition**: Step 5.2.2 completed
- **Goal**: Ensure no double-counting of time
- **Execution**:
  - Review overlapping events
  - Adjust WBSO session times to avoid conflicts
  - Document any time periods that cannot be allocated
- **Validation**: No overlapping events, all conflicts resolved

### Phase 6: Reporting and Validation

#### 6.1 Generate Comprehensive Reports

- [ ] **Step 6.1.1: Create Daily Work Reports**

- **Pre-condition**: Step 5.2.3 completed
- **Goal**: Generate detailed daily work summaries
- **Execution**:
  - Query database for work sessions by date
  - Include commits, issues, hours, and WBSO categories
  - Export as CSV: `reports/daily_work_{date}.csv`
- **Validation**: Daily CSV reports for each work day

- [ ] **Step 6.1.2: Create Weekly Summary Reports**

- **Pre-condition**: Step 6.1.1 completed
- **Goal**: Generate weekly hour summaries
- **Execution**:
  - Aggregate daily data by ISO week
  - Calculate total hours per week
  - Show breakdown by WBSO category
  - Export as CSV: `reports/weekly_summary.csv`
- **Validation**: Weekly summary with totals and breakdowns

- [ ] **Step 6.1.3: Create Monthly Summary Reports**

- **Pre-condition**: Step 6.1.2 completed
- **Goal**: Generate monthly hour summaries
- **Execution**:
  - Aggregate weekly data by month
  - Calculate total hours per month
  - Show breakdown by WBSO category
  - Export as CSV: `reports/monthly_summary.csv`
- **Validation**: Monthly summary with totals and breakdowns

#### 6.2 WBSO Compliance Validation

- [ ] **Step 6.2.1: Validate WBSO Category Distribution**

- **Pre-condition**: Step 6.1.3 completed
- **Goal**: Ensure hours align with WBSO project requirements
- **Execution**:
  - Check distribution across WBSO categories
  - Verify alignment with approved project phases
  - Document any deviations
- **Validation**: Report showing WBSO category alignment

- [ ] **Step 6.2.2: Validate Time Allocations**

- **Pre-condition**: Step 6.2.1 completed
- **Goal**: Ensure time allocations are reasonable and justifiable
- **Execution**:
  - Review hour allocations for reasonableness
  - Check for any unrealistic time periods
  - Validate against industry standards
- **Validation**: Report confirming reasonable time allocations

- [ ] **Step 6.2.3: Create Final WBSO Documentation Package**

- **Pre-condition**: Step 6.2.2 completed
- **Goal**: Prepare complete documentation for tax authorities
- **Execution**:
  - Compile all reports into single package
  - Create executive summary
  - Include methodology documentation
  - Prepare audit trail
- **Validation**: Complete documentation package ready for submission

### Phase 7: Final Validation and Delivery

#### 7.1 Quality Assurance

- [ ] **Step 7.1.1: Review Total Hours Achievement**

- **Pre-condition**: Step 6.2.3 completed
- **Goal**: Confirm 510+ hour target achieved
- **Execution**:
  - Calculate final total declarable hours
  - Verify >= 510 hours
  - Document final total and breakdown
- **Validation**: Confirmation of 510+ hours achieved

- [ ] **Step 7.1.2: Validate Calendar Integration**

- **Pre-condition**: Step 7.1.1 completed
- **Goal**: Ensure calendar accurately reflects all work
- **Execution**:
  - Review Google Calendar for completeness
  - Verify all work sessions are represented
  - Check color coding is correct
- **Validation**: Calendar accurately shows all WBSO and non-declarable activities

- [ ] **Step 7.1.3: Final Documentation Review**

- **Pre-condition**: Step 7.1.2 completed
- **Goal**: Ensure all documentation is complete and accurate
- **Execution**:
  - Review all generated reports
  - Verify data consistency across reports
  - Check for any missing information
- **Validation**: All documentation complete and accurate

#### 7.2 Project Completion

- [ ] **Step 7.2.1: Create Project Summary**

- **Pre-condition**: Step 7.1.3 completed
- **Goal**: Document project completion and results
- **Execution**:
  - Write project completion summary
  - Document total hours achieved
  - List key deliverables created
- **Validation**: Project summary document completed

- [ ] **Step 7.2.2: Archive Project Data**

- **Pre-condition**: Step 7.2.1 completed
- **Goal**: Safely store all project data for future reference
- **Execution**:
  - Create backup of all data files
  - Archive database and reports
  - Document data location and access methods
- **Validation**: All project data safely archived

- [ ] **Step 7.2.3: Project Handover**

- **Pre-condition**: Step 7.2.2 completed
- **Goal**: Ensure project results are accessible for WBSO submission
- **Execution**:
  - Create handover document
  - List all deliverables and their locations
  - Provide instructions for using the system
- **Validation**: Complete handover documentation ready

## Technical Implementation

### Repository Structure

```
docs/project/hours/
├── PROJECT_PLAN.md                 # This document
├── README.md                       # Updated with new features
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

### Key Scripts

#### 1. Multi-Repository Extractor

- Extract git logs from multiple repositories
- Handle different repository structures
- Aggregate commit data with repository context

#### 2. GitHub Issue Analyzer

- Extract issues using GitHub API
- Categorize issues by type and complexity
- Assign realistic hour allocations

#### 3. Hour Optimizer

- Analyze current totals vs 510 target
- Identify opportunities for additional hours
- Implement generous but justifiable allocations

#### 4. Dedicated WBSO Google Calendar and Conflict Detection

- Create dedicated "WBSO Activities" Google Calendar
- Implement color coding for WBSO vs non-declarable activities
- Manual calendar export and review processes
- Detect conflicts with existing calendar items
- Identify and categorize non-declarable activities
- Generate conflict resolution documentation
- Enable calendar-based WBSO reporting

#### 5. Report Generator

- Generate comprehensive WBSO reports
- Include activity breakdowns
- Create audit trail documentation

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
- **Research and Learning**: 1-3 hours per research session (WBSO-aligned)
- **Testing and Validation**: 1-2 hours per testing session (technical testing)
- **Code Review**: 0.5-1 hour per review session
- **Technical Documentation**: 1-2 hours per technical documentation session

### Non-Declarable Activities (Solo Developer Context)

- **Personal Appointments**: Dentist, doctor, personal meetings, family time
- **Break Time**: Lunch breaks, coffee breaks, personal time, exercise
- **Travel Time**: Commuting, personal travel
- **Administrative Tasks**: Non-technical paperwork, general administration
- **Personal Development**: Non-R&D learning, hobbies, personal projects
- **Health and Wellness**: Medical appointments, therapy, wellness activities

### Buffer Time Strategy

- **Pre-commit Preparation**: 30 minutes before each commit
- **Post-commit Documentation**: 15-30 minutes after each commit
- **Issue Analysis**: 30-60 minutes for issue understanding
- **Cross-repository Coordination**: 30 minutes for context switching

## WBSO Project Alignment

### Approved WBSO Activities (Based on Filled Form)

Based on your specific WBSO project "AI Agent Communicatie in een data-veilige en privacy-bewuste omgeving" (WBSO-AICM-2025-01), the following key areas qualify for R&D tax deduction:

1. **AI Framework & Access Control Development** (40-45% of hours)

   - AI-agent framework design and implementation
   - Role/context-based access control systems
   - Intent recognition algorithms
   - Jailbreak detection mechanisms
   - Natural language processing for authorization

2. **Privacy-Preserving Cloud Integration** (25-30% of hours)

   - Data anonymization/pseudonymization algorithms
   - Safe cloud LLM integration techniques
   - Data screening and processing layers
   - Cloud-worthiness decision rules
   - AVG compliance mechanisms

3. **Privacy-Friendly Audit Logging** (15-20% of hours)

   - Custom audit log structure development
   - Secure reference systems
   - Traceability without privacy leaks
   - Privacy-preserving audit mechanisms

4. **Data Integrity & Protection Systems** (10-15% of hours)
   - Data classification modules (read/edit)
   - Corruption prevention mechanisms
   - Risk operation blocking systems
   - Data integrity validation

## WBSO Compliance Framework

### R&D Activity Categories

1. **Research and Investigation** (25-30% of hours)

   - Technical research and analysis
   - Problem investigation and root cause analysis
   - Technology evaluation and comparison

2. **Development and Implementation** (40-45% of hours)

   - Code development and implementation
   - System architecture and design
   - Technical implementation and optimization

3. **Innovation and Optimization** (15-20% of hours)

   - Performance optimization
   - Algorithm improvement
   - System enhancement and innovation

4. **Quality Assurance and Testing** (10-15% of hours)
   - Testing and validation
   - Quality assurance activities
   - Performance testing and optimization

### Compliance Requirements

- All activities must demonstrate technical innovation
- Activities should be experimental or involve technical uncertainty
- Proper documentation of R&D objectives and outcomes
- Clear link to business objectives and technical challenges

## Success Criteria

### Quantitative Targets

- ✅ Achieve 510+ total WBSO hours
- ✅ Cover all development repositories
- ✅ Include both commits and issues
- ✅ Maintain realistic time allocations

### Qualitative Targets

- ✅ WBSO compliance validation
- ✅ Comprehensive audit trail
- ✅ Clear activity categorization
- ✅ Professional documentation

### Deliverable Targets

- ✅ Multi-repository analysis complete
- ✅ Google Calendar integration functional
- ✅ Comprehensive reporting tools
- ✅ Final WBSO documentation package

## Risk Management

### Technical Risks

- **GitHub API Rate Limits**: Implement rate limiting and caching
- **Repository Access Issues**: Maintain backup access methods
- **Data Quality Issues**: Implement validation and error handling
- **Incomplete Commit Coverage**: Prototypes or failed work may never be committed, leading to underreported hours. *Mitigation*: supplement commit data with sources like workstation login/logout logs or local file change histories.

### Compliance Risks

- **WBSO Eligibility**: Regular review of activity categorization
- **Time Allocation Justification**: Maintain detailed documentation
- **Audit Trail Completeness**: Ensure comprehensive record keeping

### Mitigation Strategies

- Implement robust error handling and logging
- Regular compliance reviews and validation
- Maintain detailed documentation of methodology
- Create backup data extraction methods

## Timeline and Milestones

### Week 1: Foundation

- [ ] Repository inventory complete
- [ ] Multi-repo extraction framework ready
- [ ] Baseline analysis complete

### Week 2: Issue Analysis

- [ ] GitHub issue extraction functional
- [ ] Issue categorization framework complete
- [ ] Issue-to-hours mapping established

### Week 3: Integration

- [ ] Multi-repo processing pipeline complete
- [ ] Hour optimization strategy implemented
- [ ] Cross-repo work session detection functional

### Week 4: Dedicated WBSO Google Calendar and Conflict Detection

- [ ] Dedicated "WBSO Activities" Google Calendar created
- [ ] Color coding scheme implemented (WBSO vs non-declarable)
- [ ] Manual conflict detection and review process established
- [ ] WBSO calendar events populated
- [ ] Calendar export and reporting system functional

### Week 5: Finalization

- [ ] Comprehensive reports generated
- [ ] Compliance validation complete
- [ ] Final documentation package ready

## Next Steps

1. **Immediate Actions**

   - [ ] Create repository inventory
   - [ ] Set up GitHub API access
   - [ ] Begin Phase 1 implementation

2. **Resource Requirements**

   - GitHub API access tokens
   - Google Calendar access (manual exports acceptable)
   - Development time allocation
   - Manual review and editing time for calendar management

3. **Success Metrics**
   - Total hours achieved vs 510 target
   - Repository coverage percentage
   - WBSO compliance validation
   - Documentation completeness

This project plan provides a comprehensive framework for achieving your 510+ hour WBSO target while maintaining compliance and creating a professional audit trail.

## References

- [README.md](README.md)

## Code Files

- [docs/project/hours/process_commits.py](docs/project/hours/process_commits.py) - Single-repository commit processing example.
