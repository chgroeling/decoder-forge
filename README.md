# decoder-forge

Generate efficient decoder source code from YAML descriptions of bit patterns — machine instruction encodings, binary protocols, and similar fixed-format bitstreams.

## Features

- **YAML-driven** — describe bit patterns with `0`/`1` for fixed bits and `x` for variable fields; no hand-written matching code.
- **Automatic code generation** — produces a self-contained Python module with a `decode(instr, ctx)` entry point that matches patterns by specificity (most fixed bits first).
- **ARM pseudocode transpilation** — encoding decode logic is written in ARM pseudocode and transpiled to Python via [`arm-transpiller`](https://github.com/chgroeling/arm-transpiller).
- **Variable-length decoding** — Thumb (16/32-bit) and similar variable-width ISAs work out of the box; the decoder reports the byte-length of each matched instruction.
- **Side-effect handling** — `UNDEFINED`, `UNPREDICTABLE`, and `SEE` conditions from the ARM ARM are propagated through runtime side effects and surfaced as pseudo-instructions, each carrying the matched encoding's size via its `decoder_state`.

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

### Decode a binary file

```bash
decoder-forge decode formats/armv7-m.yaml firmware.bin --start_address 0xD4
```

### Visualize the decode tree

```bash
decoder-forge show-tree formats/armv7-m.yaml
```

All commands accept `--decoder_width` (default: 32) and `-v` / `-vv` for verbose output.

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
| `decode(instr: int, ctx: Context) -> (result, n_bytes)` | Match and decode a single instruction |
| `get_decoder_eval_bytes() -> int` | Bytes to read per decode attempt |
| `get_min_instr_bytes() -> int` | Minimum instruction size |
| `Context` | Runtime context passed through to the transpiled decode block |
| `NoMatch` / `Undefined` / `Unpredictable` / `See` | Pseudo-instructions |

One frozen dataclass per instruction carries all decoded fields as required members, each annotated with its Python type and (as a trailing comment) its ARM type. Pseudo-instructions (`NoMatch` excepted) carry a `decoder_state` that reflects the bit width of the encoding that raised them (`DECODED_8BIT` / `DECODED_16BIT` / `DECODED_32BIT`).

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
