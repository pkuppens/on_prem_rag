# Test Plan: Q&A Interface and Containerized Deployment Integration

**ID**: TEST-PLAN-003  
**Work Items**: [STORY-003](../stories/STORY-003.md), [STORY-004](../stories/STORY-004.md), [TASK-010](../tasks/TASK-010.md), [TASK-011](../tasks/TASK-011.md), [TASK-012](../tasks/TASK-012.md), [TASK-013](../tasks/TASK-013.md), [TASK-014](../tasks/TASK-014.md), [TASK-015](../tasks/TASK-015.md), [TASK-016](../tasks/TASK-016.md), [TASK-017](../tasks/TASK-017.md)  
**Test Type**: Integration  
**Team**: Backend Engineering, DevOps  
**Status**: Ready  
**Priority**: P1  
**Created**: 2025-06-12  
**Updated**: 2025-06-12  
**Test Lead**: Backend Engineer  
**Reviewers**: DevOps Engineer, QA Engineer

## Introduction

### Test Goal

Validate the integration between the Q&A interface, containerized services, and the complete RAG system, ensuring users can successfully ask questions about uploaded documents and receive accurate answers with proper source citations in a containerized environment.

### Scope

**Included:**

- FastAPI Q&A endpoint functionality
- Vector search and retrieval logic
- Ollama LLM integration for answer generation
- Docker container builds and service orchestration
- Environment configuration and startup procedures
- API response formatting and error handling
- Source citation accuracy and formatting

**Excluded:**

- Frontend user interface testing (covered in STORY-006, STORY-007)
- Document upload functionality (covered in TEST-PLAN-002)
- User authentication and authorization
- Production scaling and performance optimization

### Work Items Under Test

- [STORY-003](../stories/STORY-003.md): Basic Q&A Interface
- [STORY-004](../stories/STORY-004.md): Containerized Deployment
- [TASK-010](../tasks/TASK-010.md): FastAPI endpoint creation
- [TASK-011](../tasks/TASK-011.md): Vector search retrieval logic
- [TASK-012](../tasks/TASK-012.md): Ollama LLM integration
- [TASK-013](../tasks/TASK-013.md): API tests for Q&A flow
- [TASK-014](../tasks/TASK-014.md): Application Dockerfile
- [TASK-015](../tasks/TASK-015.md): Docker Compose services
- [TASK-016](../tasks/TASK-016.md): Environment configuration
- [TASK-017](../tasks/TASK-017.md): Container documentation

### Success Criteria

- Q&A API returns accurate answers with source citations
- All Docker services start and communicate successfully
- System responds to queries within acceptable time limits
- Error handling provides meaningful feedback
- Container setup works consistently across platforms

## Test Environment Setup

### Prerequisites

- TEST-PLAN-001 (Development Environment) completed successfully
- TEST-PLAN-002 (Document Processing) completed with test documents indexed
- Docker and Docker Compose v2 installed
- At least 16GB RAM available for all services
- Ollama with Mistral 7B model downloaded locally

### Environment Creation

1. **Fresh Container Environment**: Start with clean Docker state

   ```bash
   docker compose down -v
   docker system prune -f
   docker volume prune -f
   ```

2. **Build Application Container**: Create fresh application image

   ```bash
   docker compose build --no-cache app
   ```

3. **Service Startup**: Start all services in proper order
   ```bash
   docker compose up -d chromadb
   sleep 30
   docker compose up -d ollama
   sleep 60
   docker compose up -d app
   ```

### Data Preparation

**Test Documents**: Use documents from TEST-PLAN-002 that are already indexed

- Technical documentation with specific facts
- Business documents with policies and procedures
- Mixed content for testing various query types

**Test Queries**: Prepare diverse question types

- **Factual**: "What is the company's vacation policy?"
- **Analytical**: "What are the main challenges discussed in the technical report?"
- **Comparative**: "How do the two approaches differ?"
- **Edge Cases**: Ambiguous questions, questions about non-existent topics

### Cleanup Instructions

- Stop all containers between test cases when specified
- Clear query cache if implemented
- Reset Ollama conversation context
- Clear application logs between major test groups

## Test Cases

### TC-001: Docker Container Build and Startup

**Work Item**: [TASK-014](../tasks/TASK-014.md), [TASK-015](../tasks/TASK-015.md)  
**Objective**: Validate Dockerfile builds and all services start correctly  
**Preconditions**: Docker and Docker Compose installed

**Execution Steps**:

1. Review Dockerfile for application service
2. Build application container: `docker compose build app`
3. Verify image size is reasonable (<2GB)
4. Start all services: `docker compose up -d`
5. Check service status: `docker compose ps`
6. Verify all services are healthy: `docker compose exec app curl http://localhost:8000/health`
7. Check logs for errors: `docker compose logs`

**Acceptance Criteria**:

- [ ] Application Dockerfile builds without errors
- [ ] Application image size under 2GB
- [ ] All defined services start successfully
- [ ] Health check endpoints respond correctly
- [ ] No critical errors in service logs
- [ ] Services can communicate with each other

**Cleanup**: Keep services running for subsequent tests

### TC-002: Environment Configuration

**Work Item**: [TASK-016](../tasks/TASK-016.md)  
**Objective**: Validate environment variable configuration and service discovery  
**Preconditions**: Docker services running from TC-001

**Execution Steps**:

1. Review `.env` file and environment variable documentation
2. Test different environment configurations (dev, staging)
3. Verify service discovery between containers
4. Test port configuration and accessibility
5. Validate secret management for API keys
6. Confirm log level configuration affects output

**Acceptance Criteria**:

- [ ] Environment variables load correctly in containers
- [ ] Service discovery works between containers
- [ ] Port configuration is flexible and documented
- [ ] Sensitive data handled securely
- [ ] Log levels adjust application verbosity
- [ ] Configuration changes apply without rebuild

**Cleanup**: Reset to default configuration

### TC-003: FastAPI Q&A Endpoint Functionality

**Work Item**: [TASK-010](../tasks/TASK-010.md)  
**Objective**: Validate Q&A API endpoint accepts queries and returns structured responses  
**Preconditions**: Application container running, test documents indexed

**Execution Steps**:

1. Send GET request to `/api/health` endpoint
2. Send POST request to `/api/query` with test question
3. Verify response format includes answer and sources
4. Test query parameters (limit, threshold, filters)
5. Test empty query and malformed requests
6. Verify API documentation is accessible

**Acceptance Criteria**:

- [ ] Health endpoint returns 200 status
- [ ] Query endpoint accepts POST requests with JSON payload
- [ ] Response includes structured answer and source citations
- [ ] Query parameters modify search behavior appropriately
- [ ] Invalid requests return meaningful error messages
- [ ] API documentation accessible at `/docs`

**Cleanup**: None required

### TC-004: Vector Search Retrieval Logic

**Work Item**: [TASK-011](../tasks/TASK-011.md)  
**Objective**: Validate similarity search returns relevant document chunks  
**Preconditions**: Documents indexed in ChromaDB, application running

**Execution Steps**:

1. Submit query about specific content known to be in indexed documents
2. Verify returned chunks contain relevant information
3. Test similarity threshold affects result quality
4. Validate result limit parameter controls returned chunks
5. Test metadata filtering (document type, date, etc.)
6. Confirm search performance meets requirements

**Acceptance Criteria**:

- [ ] Search returns relevant chunks for factual queries
- [ ] Similarity threshold filters low-relevance results
- [ ] Result limit parameter respected
- [ ] Metadata filtering works accurately
- [ ] Search completes within 5 seconds for typical queries
- [ ] No relevant content missed for good queries

**Cleanup**: None required

### TC-005: Ollama LLM Integration

**Work Item**: [TASK-012](../tasks/TASK-012.md)  
**Objective**: Validate LLM generates coherent answers from retrieved context  
**Preconditions**: Ollama service running with Mistral 7B model

**Execution Steps**:

1. Verify Ollama service responds to health checks
2. Test model loading and response generation
3. Submit context chunks to LLM for answer generation
4. Validate answer quality and coherence
5. Test different prompt templates and configurations
6. Verify answer generation time is acceptable

**Acceptance Criteria**:

- [ ] Ollama service starts and loads model successfully
- [ ] Model generates coherent answers from provided context
- [ ] Answer quality appropriate for business use
- [ ] Response time under 30 seconds for typical queries
- [ ] LLM handles various query types appropriately
- [ ] Error handling when LLM service unavailable

**Cleanup**: None required

### TC-006: End-to-End Q&A Flow

**Work Item**: [STORY-003](../stories/STORY-003.md)  
**Objective**: Validate complete question-answering workflow  
**Preconditions**: All services running, documents indexed

**Execution Steps**:

1. Submit factual question about indexed document content
2. Trace request through vector search and LLM generation
3. Verify answer accuracy against source documents
4. Check source citations point to correct document sections
5. Test multiple question types (factual, analytical, comparative)
6. Validate confidence scoring if implemented

**Acceptance Criteria**:

- [ ] Factual questions answered accurately with source citations
- [ ] Source citations link to correct document sections
- [ ] Answer quality sufficient for business decision-making
- [ ] Various question types handled appropriately
- [ ] Low-confidence answers identified and handled
- [ ] Complete workflow finishes within 45 seconds

**Cleanup**: None required

### TC-007: Error Handling and Edge Cases

**Work Item**: [TASK-013](../tasks/TASK-013.md)  
**Objective**: Validate system handles errors and edge cases gracefully  
**Preconditions**: Application running normally

**Execution Steps**:

1. Submit question about non-existent content
2. Test very long queries (>1000 characters)
3. Send malformed API requests
4. Test system behavior when ChromaDB unavailable
5. Test system behavior when Ollama unavailable
6. Submit queries in different languages

**Acceptance Criteria**:

- [ ] Non-existent content queries return appropriate "no answer" response
- [ ] Very long queries handled or rejected gracefully
- [ ] Malformed requests return clear error messages
- [ ] Database unavailability handled with proper error responses
- [ ] LLM unavailability handled with fallback or error
- [ ] Non-English queries handled appropriately

**Cleanup**: Restart any failed services

### TC-008: API Performance and Concurrency

**Work Item**: [TASK-013](../tasks/TASK-013.md)  
**Objective**: Validate API performance under realistic load  
**Preconditions**: All services healthy and responsive

**Execution Steps**:

1. Submit 10 concurrent queries to API endpoint
2. Measure response times under concurrent load
3. Test API rate limiting if implemented
4. Monitor resource usage during load testing
5. Verify no data corruption or race conditions
6. Test graceful degradation under resource pressure

**Acceptance Criteria**:

- [ ] Concurrent queries handled without blocking
- [ ] Response times remain reasonable under load
- [ ] Rate limiting works if implemented
- [ ] Resource usage stays within acceptable limits
- [ ] No data corruption or inconsistent responses
- [ ] System recovers gracefully from overload

**Cleanup**: Allow system to return to idle state

### TC-009: Cross-Platform Container Deployment

**Work Item**: [STORY-004](../stories/STORY-004.md)  
**Objective**: Validate containers work across different platforms  
**Preconditions**: Docker available on target platforms

**Execution Steps**:

1. Test container deployment on Windows with Docker Desktop
2. Test container deployment on macOS with Docker Desktop
3. Test container deployment on Linux with Docker Engine
4. Verify platform-specific volume mounting works
5. Test environment variable handling across platforms
6. Validate networking behavior is consistent

**Acceptance Criteria**:

- [ ] Containers build and run on Windows
- [ ] Containers build and run on macOS
- [ ] Containers build and run on Linux
- [ ] Volume mounting works correctly on all platforms
- [ ] Environment variables work consistently
- [ ] Network communication stable across platforms

**Cleanup**: Platform-specific cleanup procedures

### TC-010: Documentation and Setup Validation

**Work Item**: [TASK-017](../tasks/TASK-017.md)  
**Objective**: Validate container documentation and setup procedures  
**Preconditions**: Fresh environment following setup documentation

**Execution Steps**:

1. Follow container setup documentation from scratch
2. Verify all prerequisite software documented
3. Test troubleshooting procedures for common issues
4. Validate environment variable documentation
5. Check that example configurations work as documented
6. Verify backup and recovery procedures

**Acceptance Criteria**:

- [ ] Setup documentation leads to working system
- [ ] Prerequisites clearly documented and sufficient
- [ ] Troubleshooting procedures resolve common issues
- [ ] Environment configuration examples work correctly
- [ ] Example configurations demonstrate key features
- [ ] Backup/recovery procedures documented and tested

**Cleanup**: Document any setup improvements needed

## Integration Validation

### TC-011: Full System Integration Test

**Work Item**: [STORY-003](../stories/STORY-003.md), [STORY-004](../stories/STORY-004.md)  
**Objective**: Validate complete system from document upload through Q&A  
**Preconditions**: Fresh environment, no pre-existing data

**Execution Steps**:

1. Start system using documented container procedures
2. Upload and process test documents through API
3. Wait for document processing completion
4. Submit questions about uploaded documents
5. Verify end-to-end traceability of answers to sources
6. Test system restart preserves processed data

**Acceptance Criteria**:

- [ ] Complete workflow from upload to Q&A works end-to-end
- [ ] Document processing integrates with Q&A functionality
- [ ] Data persists correctly across service restarts
- [ ] Performance acceptable for realistic document volumes
- [ ] System monitoring provides visibility into all components
- [ ] Error recovery maintains system consistency

**Cleanup**: Archive successful test configuration

## Performance Targets

### Response Time Requirements

- **API Health Check**: <1 second
- **Simple Query**: <15 seconds
- **Complex Query**: <45 seconds
- **Container Startup**: <2 minutes
- **Service Discovery**: <30 seconds

### Resource Usage Limits

- **Total Memory**: <8GB for all services
- **CPU Usage**: <70% during normal operations
- **Disk Usage**: <10GB for application and logs
- **Network Latency**: <100ms between services

### Quality Metrics

- **Answer Accuracy**: >80% for factual questions
- **Source Attribution**: >95% accuracy
- **API Availability**: >99% uptime during testing
- **Container Startup**: 100% success rate

---

**Test Execution Notes**: This test plan requires both technical validation of container orchestration and qualitative assessment of Q&A accuracy. Human testers must evaluate answer quality and verify that the complete system delivers business value through the containerized deployment.
