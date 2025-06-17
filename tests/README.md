# Test Suite Documentation

## Upload Progress Testing

The test suite includes integration tests for the document upload progress reporting functionality. These tests verify that:

1. Initial upload progress (5%) is reported correctly
2. Progress updates are sent during PDF processing (10% to 95%)
3. Final completion (100%) is reported
4. WebSocket connections receive real-time progress updates
5. Invalid files are handled appropriately

### Test Files

- `test_upload_progress.py`: Main test suite for upload progress reporting
- `conftest.py`: Shared test fixtures and configuration

### Test Data

The test suite uses the following test files:

- `2005.11401v4.pdf`: Main test PDF file for progress reporting tests

### Running the Tests

To run the upload progress tests:

```bash
# Run all tests
pytest tests/

# Run only upload progress tests
pytest tests/test_upload_progress.py

# Run with verbose output
pytest -v tests/test_upload_progress.py

# Run with progress updates visible
pytest -s tests/test_upload_progress.py
```

### Test Coverage

The test suite covers:

1. Basic Upload Progress

   - Initial upload completion (5%)
   - File saving (10%)
   - Processing completion (95%)
   - Final completion (100%)

2. WebSocket Integration

   - Real-time progress updates
   - Connection handling
   - Progress message format

3. PDF Processing Progress

   - Page-by-page progress updates
   - Progress calculation accuracy
   - Processing completion

4. Error Handling
   - Invalid file handling
   - Progress tracking for failed uploads
   - WebSocket error handling

### Adding New Tests

When adding new tests:

1. Place test files in the `tests/test_data` directory
2. Update `TEST_PDF` constant in `test_upload_progress.py` if using a different file
3. Add new test methods to the `TestUploadProgress` class
4. Use the provided fixtures for consistent test setup

### Notes

- Tests use mocked progress updates to simulate page-by-page processing
- WebSocket tests require async support
- Test data directory is cleaned up automatically
- Upload progress tracking is reset before and after each test
