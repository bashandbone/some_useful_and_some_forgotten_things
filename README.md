# Some Useful (and Some Forgotten) Things

This is a smattering of scripts and projects that I've written for various reasons -- some for learning, some for automating something. I've of course written a lot more scripts than this; consider this a curated sampling that I'm sharing because someone might find them useful.

## Development Workflow

This repository uses [hk](https://github.com/jdx/hk) (git hook manager) integrated with [mise](https://mise.jdx.dev/) (task runner) for a streamlined development experience. This setup provides:

- **Automated code quality**: Pre-commit and pre-push hooks ensure consistent formatting and linting
- **Performance optimized**: Concurrent execution with file locking prevents race conditions  
- **Consistent tooling**: Same tools used locally and in CI/CD
- **Auto-fixing**: Many issues can be automatically resolved

## Quick Start

1. **Install prerequisites**:
   ```bash
   # Install mise (if not already installed)
   curl https://mise.jdx.dev/install.sh | sh
   
   # Install hk
   mise install hk@latest
   ```

2. **Set up the project**:
   ```bash
   git clone <repository-url>
   cd some_useful_and_some_forgotten_things
   mise install  # Install all tools defined in mise.toml
   hk install    # Install git hooks
   ```

3. **Common commands**:
   ```bash
   mise run lint      # Run all linters and formatters
   mise run test      # Run tests
   mise run build     # Build the project
   mise run ci        # Run full CI pipeline locally
   ```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines, workflow explanations, and troubleshooting tips.

## What's Inside

The repository contains various utilities and scripts organized by purpose. Each subdirectory typically contains its own README with specific usage instructions.
