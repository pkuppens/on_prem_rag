# WBSO Hours Registration Retrofit Project Plan

## Project Overview

**Goal**: Retrofit WBSO hours registration across multiple repositories to reach/exceed 510 hours target by capturing both GitHub commits and issue creation/management activities.

**Scope**: Multi-repository analysis including development work, documentation, investigation, and work analysis tasks.

## Requirements Analysis

### Primary Requirements

1. **Target Hours**: Achieve 510+ hours for WBSO compliance
2. **Multi-Repository**: Capture work across all development repositories
3. **Comprehensive Coverage**: Include both commits and GitHub issues
4. **Generous Allocation**: Justify higher hour allocations for thorough work documentation
5. **Dedicated WBSO Google Calendar**: Create a specific Google Calendar for WBSO activities with color-coded non-declarable items
6. **Conflict Detection**: Detect existing calendar items to avoid double-counting and identify non-declarable activities
7. **Flexible Implementation**: Manual processes and calendar exports are acceptable; not everything needs to be automated
8. **Reporting Tools**: Tools for hour calculation and reporting (can include manual processes)

### Secondary Requirements

1. **WBSO Compliance**: Ensure all activities qualify for R&D tax deduction
2. **Audit Trail**: Maintain clear documentation for tax authorities
3. **Activity Categorization**: Proper classification of R&D activities
4. **Time Validation**: Realistic time allocations with proper breaks

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

## Project Structure

### Phase 1: Repository Discovery and Analysis (Week 1)

**Objective**: Identify all repositories and establish baseline data

#### Tasks

1. **Repository Inventory**

   - [ ] Create repository list with URLs and access tokens
   - [ ] Verify access to all repositories
   - [ ] Document repository purposes and R&D relevance

2. **Data Extraction Setup**

   - [ ] Create multi-repo git log extraction script
   - [ ] Set up GitHub API access for issue analysis
   - [ ] Establish data storage structure for multi-repo analysis

3. **Baseline Analysis**
   - [ ] Extract commit history from all repositories
   - [ ] Generate initial hour estimates
   - [ ] Identify gaps and opportunities for additional hours

#### Deliverables

- Repository inventory document
- Multi-repo data extraction scripts
- Baseline hour analysis report

### Phase 2: GitHub Issue Analysis (Week 2)

**Objective**: Capture issue creation and management as documentation/investigation work

#### Tasks

1. **Issue Analysis Framework**

   - [ ] Create GitHub issue extraction script
   - [ ] Define issue-to-hours mapping rules
   - [ ] Establish issue categorization for WBSO compliance

2. **Issue Processing**

   - [ ] Extract all issues with timestamps and descriptions
   - [ ] Categorize issues by type (bug, feature, investigation, documentation)
   - [ ] Assign realistic hour allocations based on issue complexity

3. **Issue-commit Correlation**
   - [ ] Link issues to related commits
   - [ ] Identify standalone documentation work
   - [ ] Detect investigation and analysis activities

#### Deliverables

- GitHub issue analysis script
- Issue categorization framework
- Issue-to-hours mapping document

### Phase 3: Multi-Repository Integration (Week 3)

**Objective**: Combine all repositories into unified hour tracking

#### Tasks

1. **Data Aggregation**

   - [ ] Create unified data processing pipeline
   - [ ] Implement cross-repository work session detection
   - [ ] Handle overlapping time periods across repositories

2. **Hour Optimization**

   - [ ] Analyze current hour totals vs 510 target
   - [ ] Identify opportunities for additional hour allocation
   - [ ] Implement generous but justifiable time allocations

3. **Work Session Enhancement**
   - [ ] Detect related work across repositories
   - [ ] Add realistic buffer times for context switching
   - [ ] Include investigation and research time

#### Deliverables

- Multi-repo processing pipeline
- Hour optimization strategy
- Enhanced work session detection

### Phase 4: Dedicated WBSO Google Calendar and Conflict Detection (Week 4)

**Objective**: Create a dedicated WBSO Google Calendar with proper categorization and conflict detection

#### Tasks

1. **WBSO Calendar Setup**

   - [ ] Create dedicated "WBSO Activities" Google Calendar
   - [ ] Set up calendar color coding scheme (WBSO activities vs non-declarable items)
   - [ ] Configure calendar sharing and export settings
   - [ ] Design event structure for WBSO compliance

2. **Conflict Detection and Manual Review**

   - [ ] Export existing calendar items from personal/professional calendars
   - [ ] Manually review and identify non-declarable activities (appointments, personal time, etc.)
   - [ ] Create conflict resolution strategy (manual editing acceptable)
   - [ ] Document non-declarable time periods for reporting

3. **WBSO Event Creation**

   - [ ] Manually create WBSO calendar events for work sessions (avoiding conflicts)
   - [ ] Include issue creation events as documentation work
   - [ ] Add proper descriptions and WBSO categorization
   - [ ] Color-code events: WBSO activities (primary color) vs non-declarable (different color)

4. **Calendar Management and Reporting**
   - [ ] Implement manual event creation process for ongoing WBSO activities
   - [ ] Create calendar export functionality for reporting
   - [ ] Generate conflict resolution documentation
   - [ ] Set up manual review process for calendar accuracy

#### Deliverables

- Dedicated "WBSO Activities" Google Calendar with color coding
- Manual calendar export and review process
- Conflict resolution documentation and procedures
- Non-declarable activity identification and reporting
- Calendar-based WBSO reporting system

### Phase 5: Reporting and Validation (Week 5)

**Objective**: Generate comprehensive reports and validate WBSO compliance

#### Tasks

1. **Report Generation**

   - [ ] Create comprehensive WBSO hours report
   - [ ] Generate weekly and monthly summaries
   - [ ] Include activity breakdowns and justifications

2. **Compliance Validation**

   - [ ] Review all activities for WBSO eligibility
   - [ ] Ensure proper R&D activity categorization
   - [ ] Validate time allocations against industry standards

3. **Documentation**
   - [ ] Create final WBSO documentation package
   - [ ] Document methodology and assumptions
   - [ ] Prepare audit trail documentation

#### Deliverables

- Comprehensive WBSO report
- Compliance validation document
- Final documentation package

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

### Commit-Based Hours

- **Development Work**: 2-4 hours per significant commit
- **Bug Fixes**: 1-3 hours depending on complexity
- **Refactoring**: 2-6 hours for major refactoring
- **Documentation**: 1-2 hours per documentation commit

### Issue-Based Hours

- **Issue Creation**: 0.5-1 hour per issue (documentation work)
- **Investigation**: 2-4 hours per investigation issue
- **Feature Planning**: 1-3 hours per feature issue
- **Bug Analysis**: 1-2 hours per bug report

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

### Buffer Time Strategy

- **Pre-commit Preparation**: 30 minutes before each commit
- **Post-commit Documentation**: 15-30 minutes after each commit
- **Issue Analysis**: 30-60 minutes for issue understanding
- **Cross-repository Coordination**: 30 minutes for context switching

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
