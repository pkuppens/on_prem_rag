# Release Build Process Documentation

This document describes the release build process for the On-Premises RAG project, including design decisions, usage instructions, testing procedures, and best practices.

## Table of Contents

1. [Design Decisions](#design-decisions)
2. [When and How to Trigger a Release](#when-and-how-to-trigger-a-release)
3. [Checking Release Results](#checking-release-results)
4. [Testing the Release Build](#testing-the-release-build)
5. [Best Practices for Release Notes](#best-practices-for-release-notes)
6. [Troubleshooting](#troubleshooting)

## Design Decisions

### Why This Approach?

The release workflow was designed with the following principles:

#### 1. **Version Consistency Validation**
- **Decision**: Enforce that git tags match `pyproject.toml` version
- **Rationale**: Prevents accidental version mismatches that could cause confusion in package management
- **Implementation**: Pre-release validation step that fails the build if versions don't match

#### 2. **Semantic Versioning Tags**
- **Decision**: Use `v*.*.*` tag pattern (e.g., v1.0.0, v2.1.3)
- **Rationale**: 
  - Standard practice in the Python ecosystem
  - Clear semantic meaning (major.minor.patch)
  - Easy to parse and validate
  - Supports pre-releases (v1.0.0-beta.1, v1.0.0-rc.1)

#### 3. **Automated Changelog Generation**
- **Decision**: Generate changelog from git commit messages
- **Rationale**:
  - Reduces manual maintenance burden
  - Ensures changelog is always up-to-date
  - Single source of truth (git history)
  - Encourages meaningful commit messages
- **Trade-off**: Requires disciplined commit message practices

#### 4. **GitHub Releases (not GitLab or BitBucket)**
- **Decision**: Use GitHub's native release functionality
- **Rationale**:
  - Native integration with repository
  - Automatic asset hosting
  - RSS feed for release notifications
  - API access for automation
  - No external service dependencies

#### 5. **Optional PyPI Publishing**
- **Decision**: Disabled by default, opt-in via configuration
- **Rationale**:
  - Project is primarily for on-premises deployment
  - Publishing to PyPI requires additional security considerations
  - Can be enabled when project is ready for public distribution
  - Prevents accidental public releases

#### 6. **Build Artifacts**
- **Decision**: Include both wheel (.whl) and source tarball (.tar.gz)
- **Rationale**:
  - Wheel for fast installation
  - Source tarball for transparency and custom builds
  - Supports different installation scenarios

#### 7. **Pre-release Detection**
- **Decision**: Automatically mark releases as pre-release based on version string
- **Rationale**:
  - Prevents users from accidentally using unstable versions
  - Follows semantic versioning conventions
  - Detection keywords: alpha, beta, rc (release candidate)

## When and How to Trigger a Release

### Prerequisites

Before creating a release:

1. **Update Version in pyproject.toml**
   ```bash
   # Edit pyproject.toml
   [project]
   version = "1.0.0"  # Update this line
   ```

2. **Ensure All Tests Pass**
   ```bash
   uv run pytest
   uv run ruff check .
   ```

3. **Update Documentation** (if needed)
   - CHANGELOG.md (optional - auto-generated)
   - README.md (if API changes)
   - Any technical documentation

4. **Commit and Push Changes**
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 1.0.0"
   git push origin main
   ```

### Triggering a Release

#### Standard Release

```bash
# 1. Create a version tag
git tag v1.0.0

# 2. Push the tag to trigger the release workflow
git push origin v1.0.0
```

#### Pre-release (Alpha, Beta, RC)

```bash
# Alpha release
git tag v1.0.0-alpha.1
git push origin v1.0.0-alpha.1

# Beta release
git tag v1.0.0-beta.1
git push origin v1.0.0-beta.1

# Release Candidate
git tag v1.0.0-rc.1
git push origin v1.0.0-rc.1
```

The workflow will automatically mark these as pre-releases in GitHub.

### What Happens Next

1. **GitHub Actions Workflow Triggered**
   - Workflow: `.github/workflows/release.yml`
   - Trigger: Push of version tag matching `v*.*.*`

2. **Version Validation** (Step 1)
   - Extracts version from tag
   - Reads version from `pyproject.toml`
   - Compares versions
   - **Fails if mismatch** ❌

3. **Package Build** (Step 2)
   - Runs `uv build`
   - Creates wheel (.whl)
   - Creates source tarball (.tar.gz)

4. **Changelog Generation** (Step 3)
   - Finds previous tag
   - Generates commit list since last tag
   - Formats as markdown
   - Includes installation instructions

5. **GitHub Release Creation** (Step 4)
   - Creates release with tag
   - Uploads build artifacts
   - Adds generated changelog
   - Marks as pre-release if applicable

6. **Optional: PyPI Publishing** (Step 5)
   - Only runs if enabled (`if: false` by default)
   - Requires `PYPI_TOKEN` secret

## Checking Release Results

### Via GitHub Web Interface

1. **Navigate to Releases**
   - Go to: `https://github.com/pkuppens/on_prem_rag/releases`
   - Or click "Releases" in the right sidebar

2. **Verify Release Details**
   - ✅ Release version matches tag
   - ✅ Changelog is present and accurate
   - ✅ Assets are attached (wheel + tarball)
   - ✅ Pre-release flag is correct (if applicable)

3. **Check Workflow Run**
   - Go to: Actions → Release workflow
   - Click on the latest run
   - Review each step for success/failure
   - Check logs for warnings or errors

### Via GitHub CLI

```bash
# List all releases
gh release list

# View specific release
gh release view v1.0.0

# Download release assets
gh release download v1.0.0
```

### Via GitHub API

```bash
# Get latest release
curl -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/pkuppens/on_prem_rag/releases/latest

# Get specific release by tag
curl -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/pkuppens/on_prem_rag/releases/tags/v1.0.0
```

## Testing the Release Build

### Functional Testing

#### 1. **Download and Install from Release Assets**

```bash
# Download the wheel from GitHub releases
gh release download v1.0.0 --pattern "*.whl"

# Install in a clean virtual environment
python -m venv test_env
source test_env/bin/activate
pip install on_prem_rag-*.whl

# Test basic functionality
python -c "import backend.rag_pipeline; print('Import successful')"
```

#### 2. **Test Installation from Source Tarball**

```bash
# Download tarball
gh release download v1.0.0 --pattern "*.tar.gz"

# Extract and install
tar -xzf on_prem_rag-*.tar.gz
cd on_prem_rag-*/
pip install .

# Run basic tests
python -c "import backend.rag_pipeline; print('Import successful')"
```

#### 3. **Verify Package Metadata**

```bash
# Check installed package info
pip show on-prem-rag

# Should show:
# - Correct version number
# - Author information
# - License
# - Dependencies
```

#### 4. **Run Test Suite with Installed Package**

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests (if package includes tests)
pytest --import-mode=importlib
```

### Release Notes Testing

#### 1. **Changelog Accuracy**

Review the generated changelog for:
- ✅ All significant commits are included
- ✅ Commit messages are clear and meaningful
- ✅ No internal/WIP commits exposed
- ✅ Security fixes are highlighted
- ✅ Breaking changes are prominent

#### 2. **Changelog Completeness**

Compare changelog with:
- Git history: `git log v1.0.0-beta.1..v1.0.0 --oneline`
- Closed issues/PRs since last release
- Feature roadmap from project documentation

#### 3. **Installation Instructions**

Test the installation instructions in the release notes:
- Copy-paste commands into a fresh environment
- Verify they work without modifications
- Check for correct package names and versions

### Pre-release Testing Checklist

Before marking a release as stable (non-pre-release):

- [ ] All CI/CD tests pass
- [ ] Manual functional testing completed
- [ ] Documentation is up-to-date
- [ ] Breaking changes are documented
- [ ] Migration guide provided (if needed)
- [ ] Security vulnerabilities addressed
- [ ] Performance regression tests pass
- [ ] Installation tested on multiple platforms
- [ ] Dependencies are pinned/locked appropriately

### Automated Testing in CI/CD

Consider adding these checks to the release workflow:

```yaml
# Example: Add package validation step
- name: Validate built package
  run: |
    uv pip install dist/*.whl
    uv run python -c "import backend.rag_pipeline; print('Package imports successfully')"
    uv run pytest tests/ --import-mode=importlib
```

## Best Practices for Release Notes

### Commit Message Guidelines

Good commit messages lead to good auto-generated changelogs:

**Good:**
```
feat: Add document chunking with configurable overlap
fix: Resolve memory leak in embedding generation
docs: Update API usage examples in README
```

**Bad:**
```
Update code
Fix stuff
WIP
```

### Commit Message Format

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding/updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

**Examples:**

```
feat(rag): Add support for PDF document ingestion

Implements PDF parsing using pypdf library. Supports:
- Text extraction
- Metadata preservation
- Page boundary detection

Closes #123

---

fix(embeddings): Fix memory leak in batch processing

Explicitly clear GPU cache after each batch.
Reduces memory usage by ~40% for large documents.

---

docs(api): Add FastAPI endpoint examples

Adds comprehensive examples for:
- Document upload
- Query endpoints
- Authentication flow
```

### Manual Release Notes Enhancement

After auto-generation, consider editing to:

1. **Add a Summary**
   ```markdown
   ## Release v1.0.0 - "Stable Release"
   
   This release marks the first stable version of the On-Premises RAG system.
   Key highlights include production-ready document processing, improved 
   embedding performance, and comprehensive API documentation.
   ```

2. **Categorize Changes**
   ```markdown
   ### 🎉 New Features
   - Document chunking with configurable strategies
   - PDF and DOCX support
   
   ### 🐛 Bug Fixes
   - Fixed memory leak in embedding generation
   - Resolved authentication token expiry issues
   
   ### 📚 Documentation
   - Added API usage guide
   - Updated deployment instructions
   
   ### ⚠️ Breaking Changes
   - Renamed `query()` to `search()` in API
   - Changed configuration file format
   ```

3. **Add Migration Guide**
   ```markdown
   ### Migration from v0.9.x to v1.0.0
   
   1. Update configuration file format:
      ```yaml
      # Old format
      chunk_size: 512
      
      # New format
      chunking:
        size: 512
        overlap: 50
      ```
   
   2. Update API calls:
      ```python
      # Old
      results = client.query("search term")
      
      # New
      results = client.search("search term")
      ```
   ```

4. **Highlight Security Fixes**
   ```markdown
   ### 🔒 Security
   - Fixed authentication bypass vulnerability (CVE-2024-XXXXX)
   - Updated dependencies with known security issues
   ```

5. **Add Known Issues**
   ```markdown
   ### Known Issues
   - Large PDF files (>100MB) may cause timeouts (#234)
   - ChromaDB persistence issues on Windows (#245)
   
   Workarounds are documented in the issues above.
   ```

### Release Notes Template

Use this template for manual enhancements:

```markdown
## Release vX.Y.Z - "Release Name"

[Brief summary of the release]

### 🎉 New Features
- [Feature 1]
- [Feature 2]

### 🐛 Bug Fixes
- [Fix 1]
- [Fix 2]

### 📚 Documentation
- [Doc update 1]

### ⚠️ Breaking Changes
- [Breaking change 1] - [Migration instructions]

### 🔒 Security
- [Security fix 1]

### Known Issues
- [Issue 1] - [Workaround link]

### Contributors
Thank you to all contributors:
- @username1
- @username2

### Installation

[Installation instructions from auto-generated notes]
```

## Troubleshooting

### Version Mismatch Error

**Error:**
```
❌ Version mismatch! Tag version (1.0.0) does not match pyproject.toml version (0.9.0)
```

**Solution:**
```bash
# Update pyproject.toml
vim pyproject.toml  # Change version = "0.9.0" to version = "1.0.0"
git add pyproject.toml
git commit -m "Bump version to 1.0.0"
git push

# Delete and recreate tag
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
git tag v1.0.0
git push origin v1.0.0
```

### Build Failure

**Error:**
```
ERROR: Failed to build package
```

**Solution:**
```bash
# Test build locally first
uv build

# Check for issues:
# - Missing dependencies in pyproject.toml
# - Syntax errors in source files
# - Invalid package structure
```

### No Previous Tag Found

**Warning:**
```
First release - generating full changelog
```

**Info:** This is expected for the first release. The changelog will include all commits.

### Release Already Exists

**Error:**
```
Error: Release v1.0.0 already exists
```

**Solution:**
```bash
# Option 1: Delete existing release
gh release delete v1.0.0

# Option 2: Use a different version
git tag v1.0.1
git push origin v1.0.1
```

### PyPI Publishing Fails

**Error:**
```
ERROR: Authentication failed for PyPI
```

**Solution:**
1. Verify `PYPI_TOKEN` secret is set in repository settings
2. Ensure token has correct permissions
3. Check token hasn't expired

### Empty Changelog

**Issue:** Changelog has no commits listed

**Cause:** No commits between last tag and current tag

**Solution:**
```bash
# Verify commits exist
git log v0.9.0..v1.0.0

# If no commits, you may have tagged incorrectly
# Create some changes before releasing
```

## Related Documentation

- [CI/CD Implementation Summary](CICD_POLISH_IMPLEMENTATION.md)
- [Branch Protection Rules](BRANCH_PROTECTION.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)

---

**Last Updated**: 2026-02-13  
**Maintained By**: DevOps Team  
**Version**: 1.0
