# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added the decoder-forge CLI application (located in decoder_forge.main) which:
  - Uses the Click library for command-line functionality.
  - Supports logging verbosity options (-v and -vv).
  - Introduces two new commands:
    - show-tree: Displays the decode tree for bit patterns provided in a YAML file.
    - generate_code: Generates code for a binary decoder defined by bit patterns provided in a YAML file.

- Added module decoder_forge.uc_show_decode_tree:
  - Introduces the uc_show_decode_tree use case, which displays a decode tree based on a YAML string.
  - Provides the print_tree function to format and print a hierarchical decode tree with proper indentation and node symbols.

- Added module decoder_forge.uc_generate_code:
  - Introduces the uc_generate_code use case, which generates a bit decoder based on a YAML string.

- Added Jinja template module in decoder_forge.templates:
  - Added the python_decoder.py.jinja template, which is used to generate Python bit-decoders.

- Added the module decoder_forge.bit_utils which:
  - Introduces the function "create_bitmask", which constructs a bitmask with a specified number of consecutive bits set to 1.

- Added the module decoder_forge.bit_pattern which:
  - Introduces the BitPattern class to encapsulate a bit mask (fixedmask), fixed bits (fixedbits), and the total bit length.
  - Implements:
    - A static method, parse_pattern, to convert a string representation (with fixed bits and wildcards) into a BitPattern instance.
    - A to_string method to convert a BitPattern back to its string representation.
    - The split_by_mask method to divide a BitPattern into two based on a provided mask.
    - Utility functions (is_undef_bit and is_wildcard_bit) to detect undefined or wildcard bits.
    - A combine method, which computes the union of the fixed masks and fixed bits by performing bitwise OR operations.
    - An extend_and_shift_to_msb method, which allows a BitPattern instance to be extended to a larger bit length.

- Added the module decoder_forge.pattern_algorithms which:
  - Provides compute_common_fixedmask to compute the bitwise AND (intersection) of fixedmask values across patterns.
  - Implements build_groups_by_fixed_bits to group bit patterns based on their fixed bits.
  - Implements build_decode_tree_by_fixed_bits to construct a hierarchical tree of BitPatterns by recursively grouping them.
  - Adds flattend_pattern_tree to convert a hierarchical DecodeTree into a flat list for easier traversal or debugging.

- Added a Printer class (in decoder_forge.external.printer) and an IPrinter interface (in decoder_forge.i_printer) to abstract printing operations for testability.

- Added a TemplateEngine class (in decoder_forge.external.template_engine) and an ITemplateEngine interface (in decoder_forge.template_engine) to standardize source code generation using Jinja2.

- Added the module decoder_forge.AssociatedStructRepo which:
  - Introduces the AssociatedStructRepo class which manages a repository of structure definitions and provides a mapping between BitPattern objects and their corresponding Struct objects.

- Added a templates module under decoder_forge that includes:
  - A template for generating Python decoders.

- Added Sphinx-based documentation to the project.

- Added the Transpiller class in decoder_forge.transpiller:
  - Integrates recursive AST traversal and code generation.
  - Utilizes VisitorPython to transform a YAML-based AST into Python code.
  - Supports binary and unary operations, assignments, evaluations, function calls, and conditional statements.
  - Provides a consistent framework for handling code transpilation within the project.
