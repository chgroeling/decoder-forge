# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0]

### Added

- Export an `Opcode` `IntEnum` in the generated decoder, with one entry per
  instruction (`OP_<UPPER_NAME>`) and entries for the pseudo-instructions
  (`OP_NO_MATCH`, `OP_UNDEFINED`, `OP_UNPREDICTABLE`, `OP_SEE`). The enum is
  the single source of truth for instruction identity — each dataclass
  references its value directly in its `opcode` ClassVar.

### Changed

- Rename the per-class `_id` ClassVar to `opcode` so downstream code can
  compare against `Opcode` members without convention-signalling underscore
  prefix (e.g., `result.opcode == Opcode.OP_B`).

## [1.1.1]

### Changed

- Bump arm-transpiller dependency to v1.1.1.

## [1.1.0]

### Added

- Auto-format generated code with `ruff format` by default; disable with
  `--no_format` on the `generate-code` and `decode` commands.

### Changed

- Switch from flake8 to ruff for linting.
- Bump arm-transpiller dependency to v1.1.0.

### Fixed

- Split leaf-name comment in generated code across two lines to avoid E501
  line-too-long errors for long instruction names.

### Removed

- Remove sphinx, sphinx-rtd-theme, docs/, Makefile, and make.bat.
- Remove unused charset-normalizer dependency.

## [1.0.0] - Initial Release

Initial release of decoder-forge.
