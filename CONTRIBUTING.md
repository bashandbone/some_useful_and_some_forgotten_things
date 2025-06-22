# Contributing Guide

Thank you for your interest in contributing to this collection of useful scripts and tools! This guide will help you get set up with our development workflow and understand how to contribute effectively.

## Development Workflow Overview

This repository uses a modern development workflow built around two key tools:

- **[hk](https://github.com/jdx/hk)**: A high-performance git hook manager that handles pre-commit and pre-push validation
- **[mise](https://mise.jdx.dev/)**: A task runner and tool manager that orchestrates development tasks

This combination provides automated code quality checks, consistent tooling across environments, and optimized performance through concurrent execution.

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Tools

1. **mise** (tool and task manager):
   ```bash
   # Install mise
   curl https://mise.jdx.dev/install.sh | sh
   
   # Add to your shell profile (e.g., ~/.bashrc, ~/.zshrc)
   echo 'eval "$(mise activate bash)"' >> ~/.bashrc  # for bash
   echo 'eval "$(mise activate zsh)"' >> ~/.zshrc    # for zsh
   
   # Reload your shell or source the profile
   source ~/.bashrc  # or ~/.zshrc
   ```

2. **Git** (version 2.9 or later for hook support)

### Optional but Recommended

- **ripgrep** (for fast text searching)
- **fd** (for fast file finding)

## Project Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/bashandbone/some_useful_and_some_forgotten_things.git
   cd some_useful_and_some_forgotten_things
   ```

2. **Install all development tools**:
   ```bash
   # This reads mise.toml and installs all required tools including hk
   mise install
   ```

3. **Install git hooks**:
   ```bash
   # This sets up pre-commit and pre-push hooks
   hk install
   ```

4. **Verify setup**:
   ```bash
   # Check that tools are available
   mise list
   hk --version
   
   # Run a quick health check
   mise run lint --dry-run
   ```

## Development Tasks

Our workflow is built around mise tasks defined in `mise.toml`. Here are the most common commands:

### Code Quality

```bash
# Run all linters and formatters (auto-fix when possible)
mise run lint-fix
# Aliases: mise run fix, mise run format

# Run linters in check-only mode (no auto-fix)
mise run lint

# Run fast linters only (excludes slow checks)
mise run lint --profile=fast

# Run all linters including slow ones
mise run lint --profile=slow
```

### Testing

```bash
# Run all tests
mise run test

# Run specific test suites
mise run test-unit
mise run test-integration

# Run tests with coverage
mise run test-coverage
```

### Building

```bash
# Build the project
mise run build

# Clean build artifacts
mise run clean

# Full rebuild
mise run rebuild
```

### CI Pipeline

```bash
# Run the complete CI pipeline locally
mise run ci

# This is equivalent to running:
# - mise run test
# - mise run lint
# - mise run build
```

## Git Hooks Explained

The hk configuration automatically manages several git hooks:

### Pre-commit Hook

Runs automatically when you `git commit`. It will:

1. **Stash unstaged changes** to ensure only staged changes are checked
2. **Run fast linters** on staged files only
3. **Auto-fix issues** when possible (e.g., formatting, import sorting)
4. **Re-stage fixed files** automatically
5. **Restore unstaged changes** after completion

If any unfixable issues are found, the commit will be blocked with clear error messages.

### Pre-push Hook

Runs automatically when you `git push`. It performs:

1. **Full linting suite** including slow checks
2. **Security scans** for sensitive data
3. **Documentation checks** to ensure docs are up-to-date
4. **Integration tests** if applicable

### Manual Hook Execution

You can run hooks manually at any time:

```bash
# Run pre-commit checks on all files
hk check

# Run pre-commit checks with auto-fix
hk fix

# Run specific linters
hk check --only=prettier,eslint

# Run with different profiles
hk check --profile=slow
```

## Understanding the Tool Integration

### How hk and mise work together

1. **mise.toml** defines development tasks and tool dependencies
2. **hk.pkl** configures git hooks and references mise tasks
3. **GitHub workflows** use mise-action to run the same tasks in CI/CD

This ensures consistency between local development and continuous integration.

### Performance Benefits

- **Concurrent execution**: Multiple linters run in parallel when safe
- **File locking**: Prevents race conditions when tools modify the same files
- **Incremental checks**: Only checks changed files in pre-commit hooks
- **Smart caching**: Tools cache results when possible

## Common Workflows

### Making a Contribution

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** using your preferred editor

3. **Test your changes**:
   ```bash
   # Run relevant tests
   mise run test
   
   # Check code quality
   mise run lint-fix
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   # Pre-commit hooks run automatically
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   # Pre-push hooks run automatically
   ```

### Fixing Hook Failures

If pre-commit hooks fail:

1. **Review the error messages** - they usually indicate exactly what needs to be fixed
2. **Run the fixer manually**:
   ```bash
   mise run lint-fix
   ```
3. **Stage the fixed files**:
   ```bash
   git add .
   ```
4. **Retry the commit**:
   ```bash
   git commit
   ```

### Working with Large Changes

For large refactoring or when hooks are too slow:

1. **Skip hooks temporarily** (use sparingly):
   ```bash
   git commit --no-verify -m "WIP: large refactoring"
   ```

2. **Run full checks before pushing**:
   ```bash
   mise run ci
   git push
   ```

## Troubleshooting

### Common Issues

#### "mise command not found"

**Solution**: Ensure mise is properly installed and activated in your shell:
```bash
# Check if mise is in PATH
which mise

# If not found, reinstall and activate
curl https://mise.jdx.dev/install.sh | sh
echo 'eval "$(mise activate bash)"' >> ~/.bashrc
source ~/.bashrc
```

#### "hk command not found"

**Solution**: Install hk through mise:
```bash
mise install hk@latest
# Or install globally
mise use -g hk@latest
```

#### Pre-commit hooks are slow

**Solutions**:
- Use `--profile=fast` for quicker checks during development
- Consider `git commit --no-verify` for WIP commits (but run full checks before pushing)
- Check if you have unnecessary files staged (hooks only run on staged files)

#### Linter conflicts or false positives

**Solutions**:
- Check the specific linter configuration in `hk.pkl`
- Run individual linters to isolate the issue:
  ```bash
  hk check --only=prettier
  hk check --only=eslint
  ```
- Disable specific rules in the tool's configuration file if needed

#### CI/CD failures after local success

**Possible causes**:
- Different tool versions between local and CI
- Environment-specific issues
- Missing dependencies in CI

**Solutions**:
- Check that `mise.toml` pins tool versions
- Run `mise run ci` locally to replicate CI environment
- Check GitHub Actions logs for specific error details

### Getting Help

1. **Check tool documentation**:
   - [hk documentation](https://hk.jdx.dev/)
   - [mise documentation](https://mise.jdx.dev/)

2. **Run with verbose output**:
   ```bash
   mise run lint --verbose
   hk check --verbose
   ```

3. **Check configuration**:
   ```bash
   # View current tool versions
   mise list
   
   # View hk configuration
   hk config
   
   # View available tasks
   mise tasks
   ```

## Configuration Files

Understanding the key configuration files:

- **`mise.toml`**: Defines tools, tasks, and environment variables
- **`hk.pkl`**: Configures git hooks, linters, and their behavior
- **`.github/workflows/`**: CI/CD pipeline configuration
- **Tool-specific configs**: `.eslintrc`, `.prettierrc`, etc.

## Best Practices

### Code Quality

- **Run `mise run lint-fix` frequently** during development
- **Commit small, focused changes** to make hook execution faster
- **Write descriptive commit messages** that explain the "why" not just the "what"

### Performance

- **Stage only necessary files** to minimize hook execution time
- **Use appropriate profiles** (`--profile=fast` for quick checks)
- **Keep dependencies up to date** for performance improvements

### Collaboration

- **Don't commit with `--no-verify`** unless absolutely necessary
- **Run `mise run ci` before pushing** large changes
- **Update documentation** when adding new tools or workflows

## Contributing to the Workflow

If you want to improve the development workflow itself:

1. **Tool updates**: Modify `mise.toml` to add/update tools
2. **Hook configuration**: Edit `hk.pkl` to adjust linting behavior
3. **Task definitions**: Add new tasks in `mise.toml`
4. **CI/CD improvements**: Update `.github/workflows/` files

Always test workflow changes thoroughly and document any breaking changes.

---

Thank you for contributing! This workflow is designed to make development more efficient and enjoyable while maintaining high code quality standards.
