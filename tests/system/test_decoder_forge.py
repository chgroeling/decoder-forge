import subprocess
import sys
import os
import pytest
import pathlib


@pytest.fixture
def project_path(request):
    rootpath = request.config.rootpath
    return pathlib.Path(rootpath)


def expect(cls, **members):
    """Build the instruction object a vector expects.

    Every instruction carries a ``sideeffects`` member reporting the UNDEFINED /
    UNPREDICTABLE / SEE conditions its decode flagged. Nearly every vector below flags
    none, so the member defaults to 0 and only the vectors that do flag one say so.
    """
    members.setdefault("sideeffects", 0)
    return cls(**members)


def test_generate_code_armv7m(project_path):
    # Generate the decoder from the new instructions/encodings format and exercise it.
    print(f"Project path: {project_path}")
    format_file = project_path / "formats" / "armv7-m.yaml"
    decoder_file = project_path / "build" / "armv7-m-decoder.py"
    os.makedirs(decoder_file.parent, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
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
    InstructionSize = ns["InstructionSize"]
    # Every instruction object names the encoding form it was decoded from, so each
    # vector states which of T1, T2, ... the word matches.
    Encoding = ns["Encoding"]
    decode = ns["decode"]
    # fmt: off

    tests = [
        # bl 40
        (b"\xf0\x00\xf8\x14", expect(ns["BL"], encoding=Encoding.T1, imm32=40)),
        # bl 33928
        (b"\xf0\x08\xfa\x44", expect(ns["BL"], encoding=Encoding.T1, imm32=33928)),
        # bl -676
        (b"\xf7\xff\xfe\xae", expect(ns["BL"], encoding=Encoding.T1, imm32=-676)),
        # bl -32
        (b"\xf7\xff\xff\xf0", expect(ns["BL"], encoding=Encoding.T1, imm32=-32)),
        # movs r0, #22
        (b"\x20\x16", expect(ns["MOV_immediate"], encoding=Encoding.T1, d=0, setflags=True, imm32=22, carry=0)),  # noqa: E501
        # mov r9, #1
        (b"\xf0\x4f\x09\x01", expect(ns["MOV_immediate"], encoding=Encoding.T2, d=9, setflags=False, imm32=1, carry=0)),  # noqa: E501
        # mov.w   r3, #1073741824 ; 0x40000000
        (b"\xf0\x4f\x43\x80", expect(ns["MOV_immediate"], encoding=Encoding.T2, d=3, setflags=False, imm32=1 << 30, carry=0)),  # noqa: E501
        # mov.w   r3, #32768 ; 0x8000
        (b"\xf4\x4f\x43\x00", expect(ns["MOV_immediate"], encoding=Encoding.T2, d=3, setflags=False, imm32=0x8000, carry=0)),  # noqa: E501
        # movw    r3, #1234 ; 0x4d2
        (b"\xf2\x40\x43\xd2", expect(ns["MOV_immediate"], encoding=Encoding.T3, d=3, setflags=False, imm32=1234, carry=0)),  # noqa: E501
        # add r1, pc, #196  (ADR)
        (b"\xa1\x31", expect(ns["ADR"], encoding=Encoding.T1, d=1, imm32=196, add=True)),  # noqa: E501
        # bkpt 0x00ab
        (b"\xbe\xab", expect(ns["BKPT"], encoding=Encoding.T1, imm32=0x00AB)),
        # ldr r0, [pc, #192]
        (b"\x48\x30", expect(ns["LDR_literal"], encoding=Encoding.T1, t=0, imm32=192, add=True)),  # noqa: E501
        # ldr.w	r8, [pc, #228]
        (b"\xf8\xdf\x80\xe4", expect(ns["LDR_literal"], encoding=Encoding.T2, t=8, imm32=228, add=True)),  # noqa: E501
        # mov r3, r5
        (b"\x46\x2b", expect(ns["MOV_register"], encoding=Encoding.T1, d=3, m=5, setflags=False)),  # noqa: E501
        # movs r2, r3
        (b"\x00\x1a", expect(ns["MOV_register"], encoding=Encoding.T2, d=2, m=3, setflags=True)),  # noqa: E501
        # movs.w	ip, r0
        (b"\xea\x5f\x0c\x00", expect(ns["MOV_register"], encoding=Encoding.T3, d=12, m=0, setflags=True)),  # noqa: E501
        # mov.w	r3, r1, lsr #9 / LSR r3,r1,#9
        (b"\xea\x4f\x23\x51", expect(ns["LSR_immediate"], encoding=Encoding.T2, d=3, m=1, setflags=False, shift_n=9)),  # noqa: E501
        # movs.w r3, r1, lsr #9 / LSRS r3,r1,#9
        (b"\xea\x5f\x23\x51", expect(ns["LSR_immediate"], encoding=Encoding.T2, d=3, m=1, setflags=True, shift_n=9)),  # noqa: E501
        # lsrs	r3, r5, #6
        (b"\x09\xab", expect(ns["LSR_immediate"], encoding=Encoding.T1, d=3, m=5, setflags=True, shift_n=6)),  # noqa: E501
        # nop
        (b"\xbf\00", expect(ns["NOP"], encoding=Encoding.T1)),
        # nop.w
        (b"\xf3\xaf\x80\x00", expect(ns["NOP"], encoding=Encoding.T2)),
        # adc.w	r4, r4, #253 ; 0xfd
        (b"\xf1\x44\x04\xfd", expect(ns["ADC_immediate"], encoding=Encoding.T1, d=4, n=4, setflags=False, imm32=253)),  # noqa: E501
        # adds	r0, r7, #4
        (b"\x1d\x38", expect(ns["ADD_immediate"], encoding=Encoding.T1, d=0, n=7, setflags=True, imm32=0x4)),  # noqa: E501
        # add r1, r1, #1
        (b"\x31\x01", expect(ns["ADD_immediate"], encoding=Encoding.T2, d=1, n=1, setflags=True, imm32=0x1)),  # noqa: E501
        # add.w r0, r12, #10  (ADDW T4; corrected encoding, bit20=0, imm8=0x0A)
        (b"\xf2\x0c\x00\x0a", expect(ns["ADD_immediate"], encoding=Encoding.T4, d=0, n=12, setflags=False, imm32=10)),  # noqa: E501
        # add.w r1, r1, #1048576 @0x100000
        (b"\xf5\x01\x11\x80", expect(ns["ADD_immediate"], encoding=Encoding.T3, d=1, n=1, setflags=False, imm32=0x100000)),  # noqa: E501
        # adc.w	r1, r1, r4, lsl #20
        (b"\xeb\x41\x51\x04", expect(ns["ADC_register"], encoding=Encoding.T2, d=1, n=1, m=4, setflags=False, shift_t=1, shift_n=20)),  # noqa: E501
        # adcs	r5, r5
        (b"\x41\x6d", expect(ns["ADC_register"], encoding=Encoding.T1, d=5, n=5, m=5, setflags=True, shift_t=1, shift_n=0)),  # noqa: E501
        # ldr r1, [r0, #4]
        (b"\x68\x41", expect(ns["LDR_immediate"], encoding=Encoding.T1, t=1, n=0, imm32=0x4, index=True, add=True, wback=False)),  # noqa: E501
        # ldr	r3, [sp, #0]
        (b"\x9b\x00", expect(ns["LDR_immediate"], encoding=Encoding.T2, t=3, n=13, imm32=0x0, index=True, add=True, wback=False)),  # noqa: E501
        # ldr.w	r1, [r0, #171]
        (b"\xf8\xdc\x00\xAB", expect(ns["LDR_immediate"], encoding=Encoding.T3, t=0, n=12, imm32=0xAB, index=True, add=True, wback=False)),  # noqa: E501
        # ldr.w	r4, [r0, #-8]
        (b"\xf8\x50\x4c\x08", expect(ns["LDR_immediate"], encoding=Encoding.T4, t=4, n=0, imm32=0x8, index=True, add=False, wback=False)),  # noqa: E501
        # cmp	r3, #39	@ 0x27
        (b"\x2b\x27", expect(ns["CMP_immediate"], encoding=Encoding.T1, n=3, imm32=0x27)),  # noqa: E501
        # cmp.w	r3, #500  @ 0x1f4
        (b"\xf5\xb3\x7f\xfa", expect(ns["CMP_immediate"], encoding=Encoding.T2, n=3, imm32=0x1f4)),  # noqa: E501
        # str r1, [r2, #0]
        (b"\x60\x11", expect(ns["STR_immediate"], encoding=Encoding.T1, t=1, n=2, imm32=0x0, index=True, add=True, wback=False)),  # noqa: E501
        # str r0, [r7, #4]
        (b"\x60\x78", expect(ns["STR_immediate"], encoding=Encoding.T1, t=0, n=7, imm32=0x4, index=True, add=True, wback=False)),  # noqa: E501
        # str r3, [sp, #0]
        (b"\x93\x00", expect(ns["STR_immediate"], encoding=Encoding.T2, t=3, n=13, imm32=0x0, index=True, add=True, wback=False)),  # noqa: E501
        # str.w	r3, [r0, #0]
        (b"\xf8\xcc\x00\x00", expect(ns["STR_immediate"], encoding=Encoding.T3, t=0, n=12, imm32=0x0, index=True, add=True, wback=False)),  # noqa: E501
        # str.w	r3, [r0, #-4]
        (b"\xf8\x40\x3c\x04", expect(ns["STR_immediate"], encoding=Encoding.T4, t=3, n=0, imm32=0x4, index=True, add=False, wback=False)),  # noqa: E501
        # beq.n	2
        (b"\xd0\x01", expect(ns["B"], encoding=Encoding.T1, imm32=0x2, cond=0)),
        # b.n 2 -- T2 is unconditional, so cond is AL (14) rather than an encoded field
        (b"\xe0\x01", expect(ns["B"], encoding=Encoding.T2, imm32=0x2, cond=14)),
        # beq.w	+336
        (b"\xf0\x00\x80\xa8", expect(ns["B"], encoding=Encoding.T3, imm32=336, cond=0)),
        # bgt.w	dae4 -- gt = 12
        (b"\xf3\x00\x80\xab", expect(ns["B"], encoding=Encoding.T3, imm32=342, cond=12)),  # noqa: E501
        # b.w -190 (- 0xBE) -- T4 is unconditional, so cond is AL (14)
        (b"\xf7\xff\xbf\xa1", expect(ns["B"], encoding=Encoding.T4, imm32=-190, cond=14)),  # noqa: E501
        # subs	r2, r2, r0
        (b"\x1a\x12", expect(ns["SUB_register"], encoding=Encoding.T1, d=2, n=2, m=0, setflags=True, shift_t=1, shift_n=0)),  # noqa: E501
        # subs.w	r2, r2, ip
        (b"\xeb\xb2\x02\x0c", expect(ns["SUB_register"], encoding=Encoding.T2, d=2, n=2, m=12, setflags=True, shift_t=1, shift_n=0)),  # noqa: E501
        # push	{r1}
        (b"\xb4\x02", expect(ns["PUSH"], encoding=Encoding.T1, t=0, registers=0x2, UnalignedAllowed=False)),  # noqa: E501
        # stmdb	sp!, {r4, r5, r6, r7, r8, lr}  (== push.w)
        (b"\xe9\x2d\x41\xf0", expect(ns["PUSH"], encoding=Encoding.T2, t=0, registers=0x41F0, UnalignedAllowed=False)),  # noqa: E501
        # ldmia   r2!, {r0, r1}
        (b"\xca\x03", expect(ns["LDM"], encoding=Encoding.T1, n=2, registers=0x3, wback=True)),  # noqa: E501
        # ldmia   r2!, {}  -- register_list=0 flags UNPREDICTABLE; the instruction is
        # still decoded in full and reports the condition on its sideeffects member
        (b"\xca\x00", expect(ns["LDM"], encoding=Encoding.T1, sideeffects=ns["SIDEFFECT_UNPREDICTABLE"], n=2, registers=0x0, wback=True)),  # noqa: E501
        # add r8, r1  -- DN:Rdn, Rdn is 3 bits wide in this encoding
        (b"\x44\x88", expect(ns["ADD_register"], encoding=Encoding.T2, d=8, n=8, m=1, setflags=False, shift_t=1, shift_n=0)),  # noqa: E501
        # add sp, r8  -- DM:Rdm, Rdm is 3 bits wide in this encoding
        (b"\x44\xc5", expect(ns["ADD_SP_plus_register"], encoding=Encoding.T2, d=13, m=8, setflags=False, shift_t=1, shift_n=0)),  # noqa: E501
        # pop {r0, pc}  -- P:'0000000':register_list
        (b"\xbd\x01", expect(ns["POP"], encoding=Encoding.T1, t=0, registers=0x8001, UnalignedAllowed=False)),  # noqa: E501
        # push {r4, lr}  -- '0':M:'000000':register_list
        (b"\xb5\x10", expect(ns["PUSH"], encoding=Encoding.T1, t=0, registers=0x4010, UnalignedAllowed=False)),  # noqa: E501
    ]
    # fmt: on

    context = Context()

    for raw, expected in tests:
        # Each vector is one instruction, written most-significant byte first the way
        # the ARM manual spells the encoding. Its length is its size -- which is the
        # caller's to know, so the test states it rather than asking the decoder.
        size = InstructionSize(len(raw) * 8)
        instr = int.from_bytes(raw, "big")

        assert decode(instr, ctx=context, size=size) == expected
