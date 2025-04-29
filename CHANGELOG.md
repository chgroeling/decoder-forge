# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added the `Pattern` class and utility functions for bit pattern handling to `pattern.py`:
  - Introduced the `Pattern` class to encapsulate a bit mask (fixedmask), fixed bits (fixedbits), and the total bit length.
  - Implemented a static method `parse_pattern` to convert a string representation (with fixed bits and wildcards)
    into a `Pattern` object.
  - Added the `to_string` static method to convert a Pattern instance back into its string representation.
  - Added the separate method to split Patterns by a given fixedmask
  - Added the `__eq__` method: Enables direct equality comparison between Pattern instances.
  - Added the `split_by_mask` method: Splits a Pattern into two separate Pattern objects based on a provided mask.
  - Added utility functions `is_undef_bit` and `is_wildcard_bit`to detect undefined ('o', 'O') and wildcard ('x', 'X', '.', including undefined) 
    bits respectively.
- Added new file pattern_algorithms.py:
  – Introduces the `compute_common_fixedmask` function, which computes the bitwise AND (intersection) of the fixedmask values from a list of Pattern objects.
  - Added the `generate_tree_by_common_bits` method in `pattern_algorithmns.py`. This function generates a hierarchical tree structure of Patterns by computing a common fixed bit mask and recursively grouping patterns based on their fixed bits. Each group is represented as either a leaf or a tree node depending on the significance of the common fixed bits.



