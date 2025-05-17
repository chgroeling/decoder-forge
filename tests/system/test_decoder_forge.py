import subprocess
import pytest
import pathlib
from enum import IntFlag


class InstrFlags(IntFlag):
    I32BIT = 0b0001  # 1
    SET = 0b0010  # 2
    ADD = 0b0100  # 4
    CARRY = 0b1000  # 8


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
        [
            "python",
            "-m",
            "decoder_forge.main",
            "generate-code",
            "--out_file",
            decoder_file,
            format_file,
        ],
        check=True,
        capture_output=True,
    )
    code = None
    with open(decoder_file, "r") as f:
        code = f.read()

    compiled_code = compile(code, decoder_file, "exec")

    df_ns = {}
    exec(compiled_code, df_ns)

    Context = df_ns["Context"]
    decode = df_ns["decode"]
    ISF = InstrFlags

    tests = [
        # bl 40
        (b"\xf0\x00\xf8\x14", df_ns["Bl"](flags=ISF.I32BIT, imm32=40)),
        # bl 33928
        (b"\xf0\x08\xfa\x44", df_ns["Bl"](flags=ISF.I32BIT, imm32=33928)),
        # bl -676
        (b"\xf7\xff\xfe\xae", df_ns["Bl"](flags=ISF.I32BIT, imm32=-676)),
        # bl -32
        (b"\xf7\xff\xff\xf0", df_ns["Bl"](flags=ISF.I32BIT, imm32=-32)),
        # movs r0, #22
        (b"\x20\x16", df_ns["MovImmediate"](flags=ISF.SET, d=0, imm32=22)),
        # mov r9, #1
        #(b"\xf0\x4f\x09\x01", df_ns["MovImmediate"](flags=ISF.I32BIT, d=9, imm32=1)),
        # add r1, pc, #196
        (b"\xa1\x31", df_ns["AddPcPlusImmediate"](flags=0x0)),
        # bkpt 0x00ab
        (b"\xbe\xab", df_ns["Bkpt"](flags=0x0)),
        # ldr r0, [pc, #192]
        (b"\x48\x30", df_ns["LdrLiteral"](flags=0x0, t=0, imm32=192)),
    ]

    data = bytes()
    for adr in tests:
        data = data + adr[0]

    data += b"\x00" * 2
    context = Context()

    def translate_flags(flags):
        return ISF(flags)

    adr = 0
    i = 0

    while i < len(tests):
        code = int.from_bytes(data[adr : adr + 4])
        out = decode(code, context=context)

        assert out == tests[i][1]
        if translate_flags(out.flags) == ISF.I32BIT:
            adr += 4
        else:
            adr += 2

        i += 1
