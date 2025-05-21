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

    ns = {}
    exec(compiled_code, ns)

    Context = ns["Context"]
    decode = ns["decode"]
    ISF = InstrFlags

    tests = [
        # bl 40
        (b"\xf0\x00\xf8\x14", ns["Bl"](flags=ISF.I32BIT, imm32=40)),
        # bl 33928
        (b"\xf0\x08\xfa\x44", ns["Bl"](flags=ISF.I32BIT, imm32=33928)),
        # bl -676
        (b"\xf7\xff\xfe\xae", ns["Bl"](flags=ISF.I32BIT, imm32=-676)),
        # bl -32
        (b"\xf7\xff\xff\xf0", ns["Bl"](flags=ISF.I32BIT, imm32=-32)),
        # movs r0, #22
        (b"\x20\x16", ns["MovImmediate"](flags=ISF.SET, d=0, carry=0, imm32=22)),
        # mov r9, #1
        (
            b"\xf0\x4f\x09\x01",
            ns["MovImmediate"](flags=ISF.I32BIT, d=9, carry=0, imm32=1),
        ),
        # mov.w   r3, #1073741824 ; 0x40000000
        (
            b"\xf0\x4f\x43\x80",
            ns["MovImmediate"](flags=ISF.I32BIT, d=3, carry=0, imm32=1 << 30),
        ),
        # mov.w   r3, #32768 ; 0x8000
        (
            b"\xf4\x4f\x43\x00",
            ns["MovImmediate"](flags=ISF.I32BIT, d=3, carry=0, imm32=0x8000),
        ),
        # movw    r3, #1234 ; 0x4d2
        (
            b"\xf2\x40\x43\xd2",
            ns["MovImmediate"](flags=ISF.I32BIT, d=3, carry=0, imm32=1234),
        ),
        # add r1, pc, #196
        (b"\xa1\x31", ns["AddPcPlusImmediate"](flags=ISF.ADD, d=1, imm32=196)),
        # bkpt 0x00ab
        (b"\xbe\xab", ns["Bkpt"](flags=0x0, imm32=0x00AB)),
        # ldr r0, [pc, #192]
        (b"\x48\x30", ns["LdrLiteral"](flags=ISF.ADD, t=0, imm32=192)),
        # ldr.w	r8, [pc, #228]
        (
            b"\xf8\xdf\x80\xe4",
            ns["LdrLiteral"](flags=ISF.I32BIT + ISF.ADD, t=8, imm32=228),
        ),
        # mov r3, r5
        (b"\x46\x2b", ns["MovRegister"](flags=0x0, d=3, m=5)),
        # mov.w	r3, r1, lsr #9 / LSR r3,r1,#9
        (
            b"\xea\x4f\x23\x51",
            ns["LsrImmediate"](flags=ISF.I32BIT, d=3, m=1, shift_n=9),
        ),
        # movs.w r3, r1, lsr #9 / LSRS r3,r1,#9
        (
            b"\xea\x5f\x23\x51",
            ns["LsrImmediate"](flags=ISF.I32BIT + ISF.SET, d=3, m=1, shift_n=9),
        ),
        # lsrs	r3, r5, #6
        (b"\x09\xab", ns["LsrImmediate"](flags=ISF.SET, d=3, m=5, shift_n=6)),
        # nop
        (b"\xbf\00", ns["Nop"](flags=0x0)),
        # nop.w
        (b"\xf3\xaf\x80\x00", ns["Nop"](flags=ISF.I32BIT)),
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
        if translate_flags(out.flags) & ISF.I32BIT:
            adr += 4
        else:
            adr += 2

        i += 1
