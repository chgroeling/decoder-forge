# AGENTS.md

## Project Overview

decoder-forge is a Python 3.12+ code generation toolkit that transforms YAML-based descriptions of bit patterns (machine instruction encodings, binary protocols) into efficient decoder source code. Run it via uv.

## Build, Test & Lint

```bash
uv sync                                 # Install dependencies
uv build                                # Build package
uv run pytest                           # Run all tests
uv run pytest tests/unit                # Unit tests only
uv run pytest tests/integration         # Integration tests only
uv run pytest tests/system              # System (e2e) tests
uv run ruff check decoder_forge tests    # Lint
```

Ruff is configured with `line-length = 88` (matching Black conventions) and checks pycodestyle (`E`, `W`) and pyflakes (`F`) rules.

## Architecture

### Layering

- **Use-case modules**: `decoder_forge/uc_*.py` files orchestrate business logic (decode, generate code, show tree) and are called by the CLI in `main.py`.
- **Core types**: `BitPattern` (bit mask/pattern), `DecodeTree`/`DecodeLeaf` (tree nodes) — all dataclasses.
- **Generation**: `generate_code.py` (pipeline) behind `decoder_cache.py` (reuse of a previously generated decoder); `templates/` holds the Jinja2 output templates.

### Input format

YAML files in `formats/` (currently only `armv7-m.yaml`: 260 instructions, 369 encodings) describe instructions as `instructions[].encodings[]`. An encoding carries `name` (T1, T2, ...), `length_bits`, a `pattern` string (`0`/`1` for fixed bits, `x` for variable), the operand `bit_fields` (`field`/`width` entries interleaved with `skip` counts, MSB→LSB), and an ARM pseudocode `decode` block quoted from the ARM ARM. The mask and match values are derived from `pattern` by `BitPattern.parse_pattern`, not stored.

### Generated decoder

Jinja2 templates in `decoder_forge/templates/` emit a self-contained module: bit-pattern matching, one frozen dataclass per instruction, and `arm-transpiller`'s own `armruntime` embedded verbatim (`get_runtime_source("python")` — decoder-forge maintains no copy of the runtime and no adapter around it; the same call with `"c"` is what a C decoder target would embed).

`decode(instr, ctx, size)` returns the decoded instruction. **The size is an input, not an output** — decoder-forge does not classify instruction widths, and a caller walking a variable-length stream has to determine each instruction's size itself before asking.

Encodings are bucketed by their own bit length into one decode tree per `InstructionSize` (8/16/32), each built at that size's width and emitted as its own `decode_8bit` / `decode_16bit` / `decode_32bit` function; `decode` is a thin dispatcher over them. So a 16-bit encoding is matched against a bare 16-bit word and extracts its operands at the offsets its own `bit_fields` give them — it is never padded out to the width of the widest instruction, where its trailing bits would be the *next* instruction's and its operand offsets shifted by 16. Every size gets a function even if the format has no encodings of that length; the empty ones answer `NoMatch`, so asking for an unused size is not an error. An encoding whose pattern is not 8, 16 or 32 bits long has no size to be requested under and is a generation error (`encoding_size`), as is a `length_bits` contradicting the pattern.

### Decoder cache (`decoder_cache.py`)

Generating the ARMv7-M decoder takes ~17s, of which ~16.4s is `_load` transpiling the 369 `decode` blocks (`ruff format` is 0.02s, compiling the 424 KiB result 0.16s). `uc_decode` builds a whole decoder to decode one word, so `load_decoder_source` caches the generated source on disk and reuses it.

The key is a hash of everything the output is a function of: the instruction-set YAML, the `auto_format` flag, and the **generator's own sources** — every `.py`/`.jinja`/`.template`/`.lark` file of both `decoder_forge` and `arm_transpiller`. That last part costs ~3ms and is what makes staleness impossible: editing the template, the pipeline or the transpiler pin (whose version string may not change, since it is a git dependency) all produce different keys. Do not weaken it to a version string.

The cache is an optimisation and never a failure mode — any `OSError` reading or writing it falls back to generating, with a warning. Entries are written to a temporary file and `replace`d into position so an interrupted run cannot leave a half-written decoder for the next call to compile, and pruned to the `_MAX_ENTRIES` most recently used (a hit `touch`es its entry, so the decoder in daily service is not the one evicted). `tests/conftest.py` points the cache at a per-test `tmp_path`, so a test run neither reads nor evicts a developer's real entries.

### Generation pipeline (`generate_code.py`)

Generation is two passes, because a leaf has to satisfy the member set of the *whole* instruction — including members only a sibling encoding produces, which is not known until every encoding has been analysed:

1. `_analyse_encoding` transpiles each encoding's `decode` block and derives its members, their types, its operand extractions and whether it can raise a side effect.
2. `_build_leaf` emits the bodies once the merged per-instruction structs are known.

`_load` drives both and returns the pattern repository, the de-duplicated struct list and the struct-name → ID map.

### Typing

Each encoding is transpiled with `PythonGenerator(input_types=...)`, which types every operand as the `bits<width>` of its **own** `bit_fields` entry rather than relying on the package's global `known_types` table. The same field name is a different width in different encodings (`Rd`/`Rdn`/`Rdm`/`Rn` are 3 bits in the Thumb 16-bit high-register forms and 4 in the 32-bit ones; `register_list` is 8 or 13). Without it 13 encodings fail to transpile at all.

From those inputs `infer_types(program, input_types)` yields a width-carrying type (`bitsN`/`uintN`/`sintN`/`bool`) for every variable a block defines *and* for the operands it was handed — so pass-through members the block never assigns (68 members over 32 encodings) are typed by the same call rather than patched in afterwards. It needs no `generate()` beforehand, so typing an encoding does not depend on having transpiled it. The encoding's own `input_types` win over the global name table, which is what keeps a field at the width its own encoding gives it.

All encodings of an instruction share one struct, so a member's type is the join of what each contributes (`join_types`) — `shift_n` is `bits1` in one `ADC_register` encoding and `bits6` in another; `d` is a `uint32` register number in one form and a raw `bits4` field elsewhere. Each member is annotated with the type that represents it in the output language and keeps the ARM type as a trailing comment.

How an ARM value is *spelled* — its annotation and its zero — comes from the backend, not from decoder-forge: `PythonGenerator.type_annotation()` / `.zero_value()` (`bool`/`False` for truth values, `int`/`0` otherwise), both added upstream on request. They are pure functions of the type, so `_load` holds one backend instance for the whole run and never calls `generate()` on it. This is what keeps the template free of hardcoded Python type syntax; `CGenerator` answers the same two questions with `bool`/`false` and `uint32_t`/`int32_t`, which is the precondition for a C decoder target.

A member whose type stays undetermined is logged as a warning — the block then calls a function or reads a constant the embedded runtime does not define, and decoding it would raise `NameError`. The ARMv7-M format currently produces no such warning.

### Instruction members

An instruction object's members are, in order:

- **The encoding form that matched** — `encoding`, an `Encoding` enum entry (`T1`, `T2`,
  ...). It is the one member no `decode` block produces: all encodings of an instruction
  share a single class, so without it the result does not say which form was decoded.
  The entry's ID is the number in the name (`T1` is 1, not the position it occupies); a
  name without a number, or one whose number another name already claimed (`A1` and `T1`
  in a format covering both instruction sets), gets the lowest free ID instead. `NoMatch`
  is not a decoded instruction and has no such member.
- **The side effects the block flagged** — `sideeffects`, a bit set of the runtime's
  `SIDEFFECT_*` constants. The other member no `decode` block produces; see
  [Side effects](#side-effects).
- **What the block assigns** — `extract_output_variables`.
- **Plus the encoding's own `bit_fields` that never become one of them** — fields the block merely tests (`extract_unassigned_inputs`, e.g. `firstcond`/`mask` in `IT`) and fields it does not mention at all (`option` in `DSB`, the coprocessor register numbers of `MCR`). Both are passed through verbatim so no encoded information is lost. The candidate set is restricted to `bit_fields` because the transpiler also reports enum/constant tokens (`SRType_LSL`, `TRUE`) as inputs.
- **Minus the variables subsumed by another output** — `extract_subsumed_variables`. A variable the block splices verbatim into another output, and reads nowhere else, is a bit-slice of that output and adds nothing. Only `I1`/`I2` in `B` T4 and `BL` T1 qualify across the whole format: they are bits 23 and 22 of the `imm32` they help build. Keeping them duplicated information in `BL` and forced `B` T1/T2/T3 to invent a value for a field their encoding has no notion of. The analysis is width-aware (a truncating `SignExtend`/`ZeroExtend` does not preserve its operands), which is why it takes the encoding's `input_types` and lives upstream; a read in any other position — a condition, an arithmetic operand, a bit index — keeps the variable, which is what separates `I1` from `n` in `LDM` T1 (read only as the index in `registers<n>`) and from `dp_operation` in the VFP encodings (read only as an `if` selector).

**No member is optional.** An instruction is only ever constructed with all of its values present, so every dataclass field is required and the leaf hands the constructor a value for each. Two groups get a value the `decode` block never produces, pre-set to the zero of their type (`False` for truth values, `0` otherwise):

1. **Members a sibling encoding contributes but this one does not** — `B` gains `cond` from T1/T3, so T2 and T4 supply it; likewise `t` in `POP`/`PUSH` T3, `index`/`add`/`wback` in `LDR_register` T1. If the encoding nevertheless extracts the member as an operand, it is filled from that operand rather than zeroed.
2. **Members the block assigns on some paths only**, which would otherwise be unbound locals. This comes from `arm-transpiller`'s definite-assignment analysis (`extract_conditionally_assigned`, requested by decoder-forge and replacing an equivalent local implementation): a branching statement binds only what all of its alternatives bind, and only if the alternatives are exhaustive — an `if` without `else` and a non-exhaustive `case` can fall through, while `VRINTA_VRINTN_VRINTP_VRINTM`'s `case RM` covers all four values of its 2-bit selector and so does bind `rmode`/`away`. Exhaustiveness is decided from the *inferred type* of the case selector, which is why the analysis lives upstream; the encoding's `input_types` are passed in so the selector is sized by its own `bit_fields`. Just three leaves are left needing it: `imm32`/`imm64` in `VMOV_immediate`, `round_zero`/`round_nearest` in `VCVT_VCVTR_integer` and `VCVT_fixed_point`.

### Side effects

Runtime state is threaded through the `ctx` argument the transpiler emits. A transpiled `decode` block flags `SEE`/`UNDEFINED`/`UNPREDICTABLE` by setting bits on the local `sideffect_flags` variable — there are no hooks. Its value ends up on the decoded instruction's `sideeffects` member, and that is the whole of what the decoder does with it: **the decoder reports side effects, it does not act on them.** An encoding that flags `UNDEFINED` is still decoded and returned with every field filled in, and it is the caller who decides what an `UNDEFINED`, `UNPREDICTABLE` or `SEE` condition means for it — which of the three matters, and in what order, is a policy the decoder has no business fixing. `SEE` names its redirect target in a comment on the flagging line only; the target is not otherwise recorded.

Whether a block can flag anything is decided at generation time via `extract_side_effects` (which reports explicit statements and ones raised inside runtime helpers such as `ThumbExpandImm`). 271 of the 369 ARMv7-M encodings can; the other 98 never touch `sideffect_flags`, so their leaves pass `SIDEFFECT_NONE` rather than reading a variable they did not contribute to.

The one result that is not an instruction is `NoMatch`, returned when no encoding matches and for a size the instruction set has no encodings of. It is field-less: the size is what the caller passed in, so the result does not restate it, and nothing was decoded, so it has neither an `encoding` nor a `sideeffects` member. `Context` is used exactly as the package defines it, which is what the C port needs (`Context` is a fixed struct there).

## Code Conventions

- **Type hints** on all public functions; `Protocol` for interfaces; dataclasses for data objects.
- **Docstrings**: Google-style (Args/Returns/Raises/Example), consumed by Sphinx Napoleon.
- **Naming**: `snake_case` modules/functions, `PascalCase` classes, `UPPER_SNAKE` constants.
- **Line length**: 88 characters.
- **Imports**: `typing` types (`Optional`, `list`, `dict`, `cast`, etc.) used throughout; no `from __future__` needed (3.11+ target).

## Versioning, Commits &amp; Changelog

- **Semantic Versioning** — Version numbers follow [SemVer](https://semver.org/): `MAJOR.MINOR.PATCH`. MAJOR for breaking changes, MINOR for backward-compatible features, PATCH for backward-compatible fixes.
- **Conventional Commits** — Commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/) format: `type(scope): description`. Common types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`. Breaking changes use `!` after the type/scope or a `BREAKING CHANGE:` footer.
- **Keep a Changelog** — `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/) format with `Added`, `Changed`, `Fixed`, `Removed` sections. Every release gets its own heading.

## Directory Map

```
decoder_forge/              # Source package (CLI, core logic, templates)
  main.py                   # click CLI: decode / generate-code / show-tree
  uc_*.py                   # Use cases, one per CLI command
  generate_code.py          # Generation pipeline
  decoder_cache.py          # On-disk cache of generated decoders
  bit_pattern.py            # BitPattern
  pattern_algorithms.py     # Decode-tree building and flattening
  templates/                # Jinja2 templates for code generation
formats/                    # YAML format/instruction-set definitions
tests/
  conftest.py               # Redirects the decoder cache to a per-test tmp_path
  unit/                     # Isolated tests on BitPattern, algorithms, repo
  integration/              # Transpiler, generated code execution, cache tests
  system/                   # Full end-to-end ARMv7-M decoder tests
  data/formats/             # Test fixture YAML files
docs/                       # Sphinx documentation (autodoc + Napoleon, RTD theme)
```
