# Test Assertions Rule

## Purpose

Ensure all test assertions provide clear, actionable error messages when they fail.

## Standard Practice

### Always Include Error Messages

Every `assert` statement in tests MUST include a descriptive error message that explains:

- What the assertion is checking
- What was expected
- Context about the failure when possible

### Examples

#### ❌ Poor - Generic assertions

```python
assert result is True
assert Path(cache_dir).exists()
assert len(items) == 5
```

#### ✅ Good - Clear error messages

```python
assert result is True, "download_model should return True on successful download"
assert Path(cache_dir).exists(), f"Cache directory should exist at: {cache_dir}"
assert len(items) == 5, f"Expected 5 items in list, got {len(items)}"
```

### Error Message Guidelines

1. **Be Specific**: Describe exactly what should have happened
2. **Include Context**: Add variable values when helpful for debugging
3. **Use Action-Oriented Language**: "should exist", "should return", "should contain"
4. **Include Actual Values**: Use f-strings to show what was actually received

### Common Patterns

#### Boolean Results

```python
assert result is True, "function_name should return True when operation succeeds"
assert result is False, "function_name should return False when operation fails"
```

#### File/Directory Existence

```python
assert Path(file_path).exists(), f"File should exist at: {file_path}"
assert not Path(file_path).exists(), f"File should not exist at: {file_path}"
```

#### Collections and Lengths

```python
assert len(items) == expected, f"Expected {expected} items, got {len(items)}"
assert item in collection, f"Item '{item}' should be in collection: {collection}"
```

#### Equality with Context

```python
assert actual == expected, f"Expected {expected}, got {actual}"
assert result.status == "success", f"Expected status 'success', got '{result.status}'"
```

## Application

- Apply this standard to ALL new test files
- When editing existing tests, add error messages to any assertions being modified
- During code reviews, check that all assertions have clear error messages
- Use this pattern consistently across unit tests, integration tests, and end-to-end tests

This rule ensures that test failures provide immediate, actionable information for debugging without requiring additional investigation.
