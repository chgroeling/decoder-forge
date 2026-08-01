# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0]

### Added

- On-disk cache for generated decoder sources (`decoder_forge/decoder_cache.py`), used
  by the `decode` command. Decoding one word previously spent ~17 seconds rebuilding a
  decoder identical to the last one; a cached decoder takes ~0.3. The key covers the
  instruction-set YAML, the formatting flag and the sources of both `decoder_forge` and
  `arm-transpiller`, so editing the format, the generator or the transpiler pin
  regenerates rather than serving a stale decoder. Entries are stored under
  `$XDG_CACHE_HOME/decoder-forge` (`DECODER_FORGE_CACHE_DIR` overrides) and pruned to
  the 8 most recently used.
- `--no_cache` on the `decode` command, and a `use_cache` argument on `uc_decode()`.

## [3.0.0]

### Added

- `InstructionSize` `IntEnum` in the generated decoder (`SIZE_8BIT` = 8, `SIZE_16BIT` =
  16, `SIZE_32BIT` = 32), and one decoder per size — `decode_8bit`, `decode_16bit`,
  `decode_32bit` — each matching against a word of exactly its own width. Sizes the
  instruction set has no encodings for get an empty decoder that answers `NoMatch`.
- `get_supported_sizes()` in the generated decoder, listing the sizes the instruction
  set actually uses.

### Changed

- **Breaking:** `decode(instr, ctx)` is now `decode(instr, ctx, size)` and returns the
  decoded instruction alone instead of `(result, n_bytes)`. The size is an input: the
  decoder no longer determines instruction widths, and `instr` holds exactly `size`
  bits rather than being padded out to the width of the widest instruction.
- **Breaking:** A 16-bit encoding's operands are extracted at the offsets its own
  `bit_fields` give them (bits 15..0) rather than from the top half of a 32-bit word.
- **Breaking:** `_apply_sideeffect` signature changed from
  `(sideffect_flags, decoded, decoder_state)` to `(sideffect_flags, decoded)`.
- **Breaking:** The `decode` CLI command takes an instruction word as hexadecimal plus
  a required `--size`, instead of a binary file and `--start_address`. The word is
  written most-significant bit first, as an architecture manual spells the encoding.
- **Breaking:** `show-tree` prints one decode tree per instruction size.
- **Breaking:** `generate_code()`, `uc_generate_code()` and `uc_show_decode_tree()` no
  longer take a `decoder_width`; sizes come from each encoding's own pattern length.
- `uc_decode()` writes its result to the `printer` it is given, which it previously
  ignored in favour of `print()`.
- An encoding whose pattern is not 8, 16 or 32 bits long is now a `ValueError`, as is a
  `length_bits` that contradicts its pattern.

### Removed

- **Breaking:** `DecoderState` and the `decoder_state` field on every instruction and
  pseudo-instruction. The size is what the caller passed to `decode`, so the result no
  longer restates it; `NoMatch`, `Undefined`, `Unpredictable` and `See` are field-less.
- **Breaking:** `get_decoder_eval_bytes()` and `get_min_instr_bytes()` from the
  generated decoder — with the size supplied per call there is no read granularity for
  the decoder to report.
- **Breaking:** The `--decoder_width` option on all CLI commands, and `--start_address`
  on `decode`.

## [2.0.0]

### Added

- `DecoderState` `IntEnum` in the generated decoder (`DECODER_NONE`, `DECODED_8BIT`,
  `DECODED_16BIT`, `DECODED_32BIT`) and a corresponding `decoder_state` field on every
  instruction dataclass and pseudo-instruction, recording the matched encoding's bit
  width.

### Changed

- **Breaking:** Pseudo-instruction constructors (`See`, `Undefined`, `Unpredictable`)
  now require a `decoder_state` argument (previously defaulted to 0). The value is
  populated from the encoding that raised the side effect.
- **Breaking:** Side-effect flags (`SEE`/`UNDEFINED`/`UNPREDICTABLE`) are tracked in a
  local `sideffect_flags` variable during decode rather than on `ctx.sideffect`.
- **Breaking:** `_apply_sideeffect` signature changed from `(sideffect_flags, decoded)`
  to `(sideffect_flags, decoded, decoder_state)`.
- Upgrade arm-transpiller to v2.0.0.

### Removed

- **Breaking:** `code` field from pseudo-instruction classes. Use the `opcode` ClassVar
  or compare against `Opcode` enum members instead.

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
