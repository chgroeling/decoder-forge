# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added the Pattern class and utility functions for bit pattern handling:
  - Introduced the Pattern class to encapsulate a bit mask (fixedmask), fixed bits (fixedbits), and the total bit length.
  - Implemented a static method parse_pattern to convert a string representation (with fixed bits and wildcards)
    into a Pattern object.
  - Added the to_string static method to convert a Pattern instance back into its string representation.
- Utility functions is_undef_bit and is_wildcard_bit were added to detect undefined ('o', 'O') and wildcard
  ('x', 'X', '.', including undefined) bits respectively.
  
