# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Auto-format generated code with `ruff format` by default; disable with
  `--no_format` on the `generate-code` and `decode` commands.

### Changed

- Switch from flake8 to ruff for linting.

### Removed

- Remove sphinx, sphinx-rtd-theme, docs/, Makefile, and make.bat.
- Remove unused charset-normalizer dependency.

## [1.0.0] - Initial Release

Initial release of decoder-forge.
