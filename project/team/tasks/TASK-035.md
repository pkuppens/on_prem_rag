# TASK-035: WBSO Justification Generator for Calendar Events

## Story Reference

- **Epic**: EPIC-002 (WBSO Compliance and Documentation)
- **Feature**: FEAT-003 (Work Session Tracking and Hours Registration)
- **Story**: STORY-008 (WBSO Hours Registration System)

## Task Description

Create a WBSO justification generator that produces proper R&D activity descriptions for calendar events based on work session data. This ensures all calendar events have comprehensive WBSO compliance documentation for tax deduction purposes.

## Business Context

For WBSO tax deduction compliance, each work session must have detailed R&D activity descriptions that justify the work as qualifying research and development. The calendar events need to include technical details, R&D justifications, and proper categorization to meet tax authority requirements.

## Acceptance Criteria

- [x] **WBSO Activity Templates**: Create detailed templates for each WBSO category
- [x] **Calendar Event Generation**: Generate Google Calendar-compatible events
- [x] **R&D Justifications**: Include comprehensive R&D activity descriptions
- [x] **Technical Details**: Provide specific technical activities and methodologies
- [x] **Repository Context**: Include relevant repository and project information
- [x] **WBSO Compliance**: Ensure all events meet WBSO tax deduction requirements
- [x] **Event Metadata**: Include WBSO project reference and categorization

## Technical Requirements

### WBSO Activity Templates

```python
wbso_activity_templates = {
    'AI_FRAMEWORK': {
        'title': 'AI Framework Development',
        'description': 'Development and implementation of AI agent framework components including natural language processing, intent recognition, and agent communication protocols.',
        'technical_details': [
            'Natural language processing implementation',
            'Intent recognition algorithm development',
            'Agent communication protocol design',
            'AI framework architecture optimization',
            'Machine learning model integration'
        ],
        'rd_justification': 'Systematic investigation into AI agent frameworks and natural language processing techniques to create novel communication protocols for data-safe environments.'
    }
    # ... other categories
}
```

### Calendar Event Format

```json
{
  "summary": "WBSO: AI Framework Development - on_prem_rag",
  "description": "WBSO Project: WBSO-AICM-2025-01: AI Agent Communicatie...",
  "start": {
    "dateTime": "2025-05-05T13:00:00",
    "timeZone": "Europe/Amsterdam"
  },
  "end": {
    "dateTime": "2025-05-05T17:00:00",
    "timeZone": "Europe/Amsterdam"
  },
  "colorId": "1",
  "extendedProperties": {
    "private": {
      "wbso_project": "WBSO-AICM-2025-01: AI Agent Communicatie...",
      "wbso_category": "AI_FRAMEWORK",
      "session_id": "session_001",
      "work_hours": "3.5",
      "is_synthetic": "false",
      "commit_count": "3"
    }
  }
}
```

### WBSO Categories and Justifications

1. **AI_FRAMEWORK**

   - Keywords: ai, agent, llm, gpt, openai, anthropic, claude, framework, nlp, natural language
   - Justification: AI framework development and natural language processing implementation

2. **ACCESS_CONTROL**

   - Keywords: auth, authentication, authorization, security, access, permission, role, jwt, oauth
   - Justification: Access control and authentication system development

3. **PRIVACY_CLOUD**

   - Keywords: privacy, cloud, data, protection, gdpr, avg, anonymization, pseudonymization
   - Justification: Privacy-preserving cloud integration and data protection mechanisms

4. **AUDIT_LOGGING**

   - Keywords: audit, log, logging, trace, monitor, track, history
   - Justification: Audit logging and system monitoring implementation

5. **DATA_INTEGRITY**

   - Keywords: integrity, validation, corruption, backup, recovery, consistency
   - Justification: Data integrity protection and validation systems

6. **GENERAL_RD**
   - Keywords: research, development, rd, innovation, experiment, prototype
   - Justification: General research and development activities

## Implementation Steps

1. **Template Creation**

   - Define comprehensive WBSO activity templates
   - Include technical details and R&D justifications
   - Map repository contexts to project descriptions

2. **Event Title Generation**

   - Create concise, descriptive titles
   - Include repository context when available
   - Follow consistent naming convention

3. **Event Description Generation**

   - Include WBSO project reference
   - Add detailed activity description
   - List technical activities performed
   - Provide R&D justification
   - Include commit activities and repository context

4. **Metadata Integration**

   - Add WBSO project reference
   - Include session categorization
   - Add work hours and session details
   - Flag synthetic vs real sessions

5. **Calendar Compatibility**
   - Ensure Google Calendar API compatibility
   - Set appropriate timezone (Europe/Amsterdam)
   - Use blue color coding for WBSO activities
   - Set private visibility

## Dependencies

- `docs/project/hours/data/work_log_complete.json` - Complete work log with all sessions
- WBSO categorization system from TASK-034
- Repository context mapping

## Definition of Done

- [x] WBSO justification generator script created and tested
- [x] 94 calendar events generated for all WBSO-eligible sessions
- [x] All events include comprehensive R&D activity descriptions
- [x] Proper WBSO categorization and justifications applied
- [x] Google Calendar API compatibility ensured
- [x] Event metadata includes all required WBSO information
- [x] Output format validated and tested
- [x] Code reviewed and committed to repository

## Results Summary

### Generated Calendar Events

- **Total Events**: 94 calendar events
- **Real Events**: 37 events (from system events)
- **Synthetic Events**: 57 events (from unassigned commits)
- **Total Hours**: 438.27 WBSO hours

### Category Breakdown

- **GENERAL_RD**: 68 events (350.77 hours)
- **AI_FRAMEWORK**: 19 events (64.5 hours)
- **PRIVACY_CLOUD**: 3 events (10.0 hours)
- **AUDIT_LOGGING**: 1 event (3.0 hours)
- **ACCESS_CONTROL**: 2 events (6.5 hours)
- **DATA_INTEGRITY**: 1 event (3.5 hours)

### WBSO Compliance Features

- **Project Reference**: All events reference WBSO-AICM-2025-01 project
- **R&D Justifications**: Comprehensive technical justifications for each category
- **Technical Details**: Specific activities and methodologies documented
- **Repository Context**: Relevant project and repository information included
- **Metadata**: Complete session and categorization information

## Estimated Effort

- **Script Development**: 2 hours
- **Template Creation**: 1 hour
- **Testing and Validation**: 0.5 hours
- **Documentation**: 0.5 hours
- **Total**: 4 hours

## Related Files

- [docs/project/hours/scripts/wbso_justification_generator.py](docs/project/hours/scripts/wbso_justification_generator.py) - Main WBSO justification generator
- [docs/project/hours/data/wbso_calendar_events.json](docs/project/hours/data/wbso_calendar_events.json) - Generated calendar events
- [project/team/tasks/TASK-034.md](project/team/tasks/TASK-034.md) - Synthetic session generation (prerequisite)

## Code Files

- [docs/project/hours/scripts/wbso_justification_generator.py](docs/project/hours/scripts/wbso_justification_generator.py) - WBSO justification generator with comprehensive R&D activity descriptions
- [docs/project/hours/data/wbso_calendar_events.json](docs/project/hours/data/wbso_calendar_events.json) - Generated calendar events with WBSO compliance

## Notes

This task successfully generated 94 calendar events with comprehensive WBSO compliance documentation. Each event includes detailed R&D activity descriptions, technical justifications, and proper categorization. The events are ready for Google Calendar integration and meet all requirements for WBSO tax deduction compliance.

The justification generator ensures that every work session has proper documentation for tax authorities, including technical details, R&D justifications, and project context. This provides a strong foundation for WBSO compliance and audit support.
