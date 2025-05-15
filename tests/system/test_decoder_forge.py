import subprocess
import pytest
import pathlib
from enum import IntFlag


class InstrFlags(IntFlag):
    I32BIT = 0b0001  # 1


@pytest.fixture
def project_path(request):
    rootpath = request.config.rootpath
    return pathlib.Path(rootpath)


def test_generate_code_armv7m(project_path):
    # Load and inspect output files from tmpdir
    print(f"Project path: {project_path}")
    format_file = project_path / "formats" / "armv7-m.yaml"
    decoder_file = project_path / "build" / "armv7-m-decoder.py"
    subprocess.run(
        ["python", "-m", "decoder_forge.main", "generate-code", "--out_file", decoder_file, format_file],
        check=True,
        capture_output=True,
    )
    code = None
    with open(decoder_file, "r") as f:
        code = f.read()

    compiled_code = compile(code, decoder_file, "exec")

    decoder_ns = {}
    exec(compiled_code, decoder_ns)

    Context = decoder_ns["Context"]
    decode = decoder_ns["decode"]

    tests = [

        # bl 40
        (b"\xf0\x00\xf8\x14", decoder_ns["Bl"](flags=0x1, imm32=40)),
        # bl 33928
        (b"\xf0\x08\xfa\x44", decoder_ns["Bl"](flags=0x1, imm32=33928)),
        # bl -676
        (b"\xf7\xff\xfe\xae", decoder_ns["Bl"](flags=0x1, imm32=-676)),
        # bl -32
        (b"\xf7\xff\xff\xf0", decoder_ns["Bl"](flags=0x1, imm32=-32)),

        # movs r0, #22
        (b"\x20\x16", decoder_ns["MovImmediate"](flags=0x0)),
        # add r1, pc, #196
        (b"\xa1\x31", decoder_ns["AddPcPlusImmediate"](flags=0x0)),
        # bkpt 0x00ab
        (b"\xbe\xab", decoder_ns["Bkpt"](flags=0x0)),
        # ldr r0, [pc, #192]
        (b"\x48\x30", decoder_ns["LdrLiteral"](flags=0x0, t=0, imm32=192)),
    ]

    data = bytes()
    for adr in tests:
        data = data + adr[0]

    data += b"\x00" * 2
    context = Context()

    def translate_flags(flags):
        return InstrFlags(flags)

    adr = 0
    i = 0
    while i < len(tests):
        code = int.from_bytes(data[adr : adr + 4])
        out = decode(code, context=context)

        assert out == tests[i][1]
        if translate_flags(out.flags) == InstrFlags.I32BIT:
            adr += 4
        else:
            adr += 2

        i += 1
