# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added the decoder-forge CLI application (located in decoder_forge.main) which:
  – Uses the Click library for command-line functionality.
  – Supports logging verbosity options (-v and -vv).
  – Introduces two new commands:
    ○ show-tree: Displays the decode tree for bit patterns provided in a JSON file.
    ○ generate_code: Generates code for a binary decoder using the Jinja2 template engine.

- Added the module decoder_forge.uc_show_decode_tree that:
  – Introduces the uc_show_decode_tree use case to display the decode tree using a specified JSON file.
  – Provides the print_tree function to format and print a hierarchical decode tree using proper indentations and node symbols.

- Added the module decoder_forge.uc_generate_code that:
  - Implements the uc_generate_code function to:
    - Decode a JSON string defining pattern definitions.
    - Build both a hierarchical decode tree and its flattened representation.
    - Generate decoder code in a specified language using a Jinja2 template.
    - Print the generated code line by line using a provided printer.

- Added the module decoder_forge.pattern which:
  – Introduces the Pattern class to encapsulate a bit mask (fixedmask), fixed bits (fixedbits), and the total bit length.
  – Implements:
    - A static method, parse_pattern, to convert a string representation (with fixed bits and wildcards) into a Pattern instance.
    - A to_string method to convert a Pattern back to its string representation.
    - The split_by_mask method to divide a Pattern into two based on a provided mask.
    - Utility functions (is_undef_bit and is_wildcard_bit) to detect undefined or wildcard bits.

- Added the module decoder_forge.pattern_algorithms which:
  - Provides compute_common_fixedmask to compute the bitwise AND (intersection) of fixedmask values across patterns.
  - Introduces build_groups_by_fixed_bits to group patterns based on their fixed bits.
  - Implements build_pattern_tree_by_fixed_bits to construct a hierarchical tree of Patterns by recursively grouping them.
  - Adds flattend_pattern_tree to convert a hierarchical PatternTree into a flat list for easier traversal or debugging.

- Added a Printer class (in decoder_forge.external.printer) and an IPrinter interface (in decoder_forge.i_printer) to abstract printing operations for testability.

- Added a TemplateEngine class (in decoder_forge.external.template_engine) and an ITemplateEngine interface (in decoder_forge.template_engine) to standardize source code generation using Jinja2.

- Added a templates module under decoder_forge that includes:
  – A template for generating Python decoders.

- Added Sphinx-based documentation to the project.
