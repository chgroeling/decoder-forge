import subprocess
import pytest
import pathlib
from enum import IntFlag
from math import ceil


class InstrFlags(IntFlag):
    SET = 0b00001  # 1
    ADD = 0b00010  # 2
    CARRY = 0b00100  # 4
    INDEX = 0b01000  # 8
    WBACK = 0b10000  # 16


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
    instr = None
    with open(decoder_file, "r") as f:
        instr = f.read()

    compiled_code = compile(instr, decoder_file, "exec")

    ns = {}
    exec(compiled_code, ns)

    Context = ns["Context"]
    decode = ns["decode"]
    decode_size = ns["decode_size"]
    size_bytes = ns["get_size_eval_bytes"]()
    instr_bytes = ns["get_decoder_eval_bytes"]()
    ISF = InstrFlags
    # fmt: off

    tests = [ 
        # bl 40
        (b"\xf0\x00\xf8\x14", ns["Bl"](flags=0x0, imm32=40)),
        # bl 33928
        (b"\xf0\x08\xfa\x44", ns["Bl"](flags=0x0, imm32=33928)),
        # bl -676
        (b"\xf7\xff\xfe\xae", ns["Bl"](flags=0x0, imm32=-676)),
        # bl -32
        (b"\xf7\xff\xff\xf0", ns["Bl"](flags=0x0, imm32=-32)),
        # movs r0, #22
        (b"\x20\x16", ns["MovImmediate"](flags=ISF.SET, d=0, imm32=22)),
        # movs	r0, #22
        (b"\x20\x16", ns["MovImmediate"](flags=ISF.SET, d=0, imm32=22)),
        # mov r9, #1
        (b"\xf0\x4f\x09\x01", ns["MovImmediate"](flags=0x0, d=9, imm32=1)),
        # mov.w   r3, #1073741824 ; 0x40000000
        (b"\xf0\x4f\x43\x80", ns["MovImmediate"](flags=0x0, d=3, imm32=1 << 30)),
        # mov.w   r3, #32768 ; 0x8000
        (b"\xf4\x4f\x43\x00", ns["MovImmediate"](flags=0x0, d=3, imm32=0x8000)),
        # movw    r3, #1234 ; 0x4d2
        (b"\xf2\x40\x43\xd2", ns["MovImmediate"](flags=0x0, d=3, imm32=1234)),
        # add r1, pc, #196
        (b"\xa1\x31", ns["AddPcPlusImmediate"](flags=ISF.ADD, d=1, imm32=196)),
        # bkpt 0x00ab
        (b"\xbe\xab", ns["Bkpt"](flags=0x0, imm32=0x00AB)),
        # ldr r0, [pc, #192]
        (b"\x48\x30", ns["LdrLiteral"](flags=ISF.ADD, t=0, imm32=192)),
        # ldr.w	r8, [pc, #228]
        (b"\xf8\xdf\x80\xe4", ns["LdrLiteral"](flags=0x0 + ISF.ADD, t=8, imm32=228)),
        # mov r3, r5
        (b"\x46\x2b", ns["MovRegister"](flags=0x0, d=3, m=5)),
        # movs r2, r3
        (b"\x00\x1a", ns["MovRegister"](flags=ISF.SET, d=2, m=3)),
        # movs.w	ip, r0
        (b"\xea\x5f\x0c\x00",  ns["MovRegister"](flags=ISF.SET, d=12, m=0)),
        # mov.w	r3, r1, lsr #9 / LSR r3,r1,#9
        (b"\xea\x4f\x23\x51", ns["LsrImmediate"](flags=0x0, d=3, m=1, shift_n=9)),
        # movs.w r3, r1, lsr #9 / LSRS r3,r1,#9
        (b"\xea\x5f\x23\x51", ns["LsrImmediate"](flags=ISF.SET, d=3, m=1, shift_n=9)),
        # lsrs	r3, r5, #6
        (b"\x09\xab", ns["LsrImmediate"](flags=ISF.SET, d=3, m=5, shift_n=6)),
        # nop
        (b"\xbf\00", ns["Nop"](flags=0x0)),
        # nop.w
        (b"\xf3\xaf\x80\x00", ns["Nop"](flags=0x0)),
        # adc.w	r4, r4, #253 ; 0xfd
        (b"\xf1\x44\x04\xfd", ns["AdcImmediate"](flags=0x0, d=4, n=4, imm32=253)),
        # adds	r0, r7, #4
        (b"\x1d\x38", ns["AddImmediate"](flags=ISF.SET, d=0, n=7, imm32=0x4)),
        # add r1, r1, #1
        (b"\x31\x01", ns["AddImmediate"](flags=ISF.SET, d=1, n=1, imm32=0x1)),
        # add.w r0, r12, #10
        (b"\xf2\x1c\x00\x10", ns["AddImmediate"](flags=0x0, d=0, n=12, imm32=0x10)),
        # add.w r1, r1, #1048576 @0x100000
        (b"\xf5\x01\x11\x80", ns["AddImmediate"](flags=0x0, d=1, n=1, imm32=0x100000)),
        # adc.w	r1, r1, r4, lsl #20
        (b"\xeb\x41\x51\x04", ns["AdcRegister"](flags=0x0, d=1, n=1, m=4, shift_t=1, shift_n=20)),
        # adcs	r5, r5
        (b"\x41\x6d",  ns["AdcRegister"](flags=ISF.SET, d=5, n=5, m=5, shift_t=1, shift_n=0)),
        # ldr r1, [r0, #4]
        (b"\x68\x41", ns["LdrImmediate"](flags=ISF.INDEX+ISF.ADD, t=1, n=0, imm32=0x4)),
        # ldr	r0, [sp, #0]
        (b"\x9b\x00", ns["LdrImmediate"](flags=ISF.INDEX+ISF.ADD, t=3, n=13, imm32=0x0)),
        # ldr.w	r1, [r0, #171]
        (b"\xf8\xdc\x00\xAB", ns["LdrImmediate"](flags=ISF.INDEX+ISF.ADD, t=0, n=12, imm32=0xAB)),
        # ldr.w	r4, [r0, #-8]
        (b"\xf8\x50\x4c\x08", ns["LdrImmediate"](flags=ISF.INDEX, t=4, n=0, imm32=0x8)),
        # cmp	r3, #39	@ 0x27
        (b"\x2b\x27", ns["CmpImmediate"](flags=0x0, n=3, imm32=0x27)),
        # cmp.w	r3, #500  @ 0x1f4
        (b"\xf5\xb3\x7f\xfa", ns["CmpImmediate"](flags=0x0, n=3, imm32=0x1f4)),
        # str r1, [r2, #0]
        (b"\x60\x11", ns["StrImmediate"](flags=ISF.INDEX+ISF.ADD, t=1, n=2, imm32=0x0)),
        # str r0, [r7, #4]
        (b"\x60\x78", ns["StrImmediate"](flags=ISF.INDEX+ISF.ADD, t=0, n=7, imm32=0x4)),
        # str r3, [sp, #0]
        (b"\x93\x00", ns["StrImmediate"](flags=ISF.INDEX+ISF.ADD, t=3, n=13, imm32=0x0)),
        # str.w	r3, [r0, #0]
        (b"\xf8\xcc\x00\x00", ns["StrImmediate"](flags=ISF.INDEX+ISF.ADD, t=0, n=12, imm32=0x0)),
        # str.w	r3, [r0, #-4]
        (b"\xf8\x40\x3c\x04", ns["StrImmediate"](flags=ISF.INDEX, t=3, n=0, imm32=0x4)),
        # beq.n	2
        (b"\xd0\x01", ns["BCond"](flags=0x0, cond=0, imm32=0x2)),
        # b.n 2
        (b"\xe0\x01", ns["B"](flags=0x0, imm32=0x2)),
        # beq.w	+336
        (b"\xf0\x00\x80\xa8", ns["BCond"](flags=0x0, cond=0, imm32=336)),
        # bgt.w	dae4 -- gt = 12
        (b"\xf3\x00\x80\xab", ns["BCond"](flags=0x0, cond=12, imm32=342)),
        # b.w -190 (- 0xBE)
        (b"\xf7\xff\xbf\xa1", ns["B"](flags=0x0, imm32=-190)),
        # subs	r2, r2, r0
        (b"\x1a\x12", ns["SubRegister"](flags=ISF.SET, d=2, n=2, m=0, shift_t=1, shift_n=0)),
        # subs.w	r2, r2, ip
        (b"\xeb\xb2\x02\x0c", ns["SubRegister"](flags=ISF.SET, d=2, n=2, m=12, shift_t=1, shift_n=0)),
        # push	{r1}
        (b"\xb4\x02", ns["Push"](flags=0x0, registers=0x2)),
        #stmdb	sp!, {r4, r5, r6, r7, r8, lr}
        (b"\xe9\x2d\x41\xf0", ns["Push"](flags=0x0, registers=0x2))
    ]
    # fmt: on

    data = bytes()
    for adr in tests:
        data = data + adr[0]

    context = Context()

    def translate_flags(flags):
        return ISF(flags)

    adr = 0
    i = 0

    while i < len(tests):
        # read the part of the code which is necessary to estimate its size
        data_for_size_eval = int.from_bytes(data[adr : adr + size_bytes])

        # calculate size of the following code
        instr_size = int(ceil(decode_size(data_for_size_eval) / 8))

        # read the code
        instr = int.from_bytes(data[adr : adr + instr_size])

        # align it to ths msb of der decoder size
        right_shift = (instr_bytes - instr_size) * 8
        instr = instr << right_shift

        # decode
        out = decode(instr, context=context)

        assert out == tests[i][1]
        adr += instr_size
        i += 1
