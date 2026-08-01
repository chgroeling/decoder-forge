# decoder-forge

Generate efficient decoder source code from YAML descriptions of bit patterns — machine instruction encodings, binary protocols, and similar fixed-format bitstreams.

## Features

- **YAML-driven** — describe bit patterns with `0`/`1` for fixed bits and `x` for variable fields; no hand-written matching code.
- **Automatic code generation** — produces a self-contained Python module with a `decode(instr, ctx, size)` entry point that matches patterns by specificity (most fixed bits first).
- **ARM pseudocode transpilation** — encoding decode logic is written in ARM pseudocode and transpiled to Python via [`arm-transpiller`](https://github.com/chgroeling/arm-transpiller).
- **One decoder per instruction size** — 8/16/32-bit encodings each get their own decode tree, built at their own width. A 16-bit instruction is matched against a bare 16-bit word, so its trailing bits are its own rather than the next instruction's. Which size applies is the caller's to say.
- **Side-effect handling** — `UNDEFINED`, `UNPREDICTABLE`, and `SEE` conditions from the ARM ARM are propagated through runtime side effects and surfaced as pseudo-instructions.

## Installation

Requires Python 3.12+. Uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
git clone https://github.com/chgroeling/decoder-forge.git
cd decoder-forge
uv sync
```

## Usage

The CLI provides three subcommands:

### Generate a decoder

```bash
decoder-forge generate-code formats/armv7-m.yaml --out_file decoder.py
```

### Decode an instruction word

```bash
decoder-forge decode formats/armv7-m.yaml f000f814 --size 32   # -> BL(imm32=40)
decoder-forge decode formats/armv7-m.yaml 2016 --size 16       # -> MOV_immediate(d=0, ...)
```

The word is written most-significant bit first, the way an architecture manual spells
the encoding — not the byte order a little-endian image stores it in. `--size` is
required: the decoder does not classify instruction widths.

Generating the ARMv7-M decoder takes ~17 seconds, almost all of it transpiling the
pseudocode `decode` blocks, so the generated source is cached and reused: the first
call takes those 17 seconds, later ones ~0.3. The cache key covers the format *and*
decoder-forge's and `arm-transpiller`'s own sources, so editing either one regenerates
rather than serving a stale decoder — `--no_cache` exists to measure generation itself,
not to work around staleness. Entries live in `$XDG_CACHE_HOME/decoder-forge`
(override with `DECODER_FORGE_CACHE_DIR`), pruned to the 8 most recently used.

### Visualize the decode trees

```bash
decoder-forge show-tree formats/armv7-m.yaml
```

One tree is printed per instruction size the format uses.

All commands accept `-v` / `-vv` for verbose output.

## YAML Format

Instruction sets are defined in YAML. Each instruction has an `id`, `mnemonic`, and one or more `encodings`. Each encoding specifies a bit pattern string and an ARM pseudocode `decode` block.

```yaml
instructions:
  - id: ADC_immediate
    mnemonic: ADC
    encodings:
      - name: T1
        length_bits: 32
        pattern: 11110x01010xxxxx0xxxxxxxxxxxxxxx
        bit_fields:
          - skip: 5
          - field: i
            width: 1
          - skip: 5
          - field: S
            width: 1
          - field: Rn
            width: 4
          - skip: 1
          - field: imm3
            width: 3
          - field: Rd
            width: 4
          - field: imm8
            width: 8
        decode: |
          d = UInt(Rd); n = UInt(Rn); setflags = (S == '1');
          imm32 = ThumbExpandImm(i:imm3:imm8);
```

**Patterns** use `0` and `1` for fixed bits, `x` for variable. **`bit_fields`** is read MSB to LSB: `skip` entries advance through the bitstream, `field` entries extract named values of the given width.

## Generated Decoder API

The generated module exposes:

| Symbol | Description |
|--------|-------------|
| `decode(instr: int, ctx: Context, size: InstructionSize) -> result` | Match and decode one instruction word of the given size |
| `decode_8bit` / `decode_16bit` / `decode_32bit` `(instr, ctx)` | The per-size decoders `decode` routes to; call directly if the size is already known |
| `InstructionSize` | `SIZE_8BIT` / `SIZE_16BIT` / `SIZE_32BIT`, valued as bit counts |
| `get_supported_sizes() -> tuple[InstructionSize, ...]` | The sizes this instruction set has encodings for |
| `Context` | Runtime context passed through to the transpiled decode block |
| `NoMatch` / `Undefined` / `Unpredictable` / `See` | Pseudo-instructions |

`instr` holds exactly `size` bits — no padding, and no bits belonging to whatever follows it. A size the instruction set does not use answers `NoMatch` rather than raising.

One frozen dataclass per instruction carries all decoded fields as required members, each annotated with its Python type and (as a trailing comment) its ARM type.

## Development

```bash
uv sync                                # install all dependencies
uv run pytest                          # run all tests
uv run pytest tests/unit               # unit tests
uv run pytest tests/integration        # integration tests
uv run pytest tests/system             # system (e2e) tests
uv run ruff check decoder_forge tests    # lint
```

## License

GPL-3.0-only. See [LICENSE](LICENSE).
