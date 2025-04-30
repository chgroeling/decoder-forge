# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added the `decoder-forge` CLI application, located in `decoder_forge.main`.
  - The CLI utilizes the `click` library for command line functionality.
  - Introduced an option to modify the application's logging verbosity (-v and -vv).
  - Added the `show-tree` command, which displays the decode tree for the specified bit patterns contained in a JSON file.
  
- Added the `Pattern` class and utility functions for bit pattern handling to `pattern.py`:
  - Introduced the `Pattern` class to encapsulate a bit mask (fixedmask), fixed bits (fixedbits), and the total bit length.
  - Implemented a static method `parse_pattern` to convert a string representation (with fixed bits and wildcards).
  - Added the `to_string` static method to convert a Pattern instance back into its string representation.
  - Added the `__eq__` method: Enables direct equality comparison between Pattern instances.
  - Added the `split_by_mask` method: Splits a Pattern into two separate Pattern objects based on a provided mask.
  - Added utility functions `is_undef_bit` and `is_wildcard_bit`to detect undefined ('o', 'O') and wildcard ('x', 'X', '.', including undefined) 
    bits respectively.
    
- Added new file `pattern_algorithms.py`:
  – Introduces the `compute_common_fixedmask` function, which computes the bitwise AND (intersection) of the fixedmask values from a list of Pattern objects.
  - Added the `generate_tree_by_common_bits` method. This function generates a hierarchical tree structure of Patterns by computing a common fixed bit mask and recursively grouping patterns based on their fixed bits. Each group is represented as either a leaf or a tree node depending on the significance of the common fixed bits.

- Added the `Printer` class in `printer.py` and the `IPrinter` interface in `i_printer.py`. Both are designed to abstract the print command for more testable use cases.

- Added the `uc_show_decode_tree` use case in `uc_show_decode_tree.py`. This use case is designed to display the decode tree using a specified JSON file that contains bit patterns for building the tree.

- Added Sphinx documentation to thr project
