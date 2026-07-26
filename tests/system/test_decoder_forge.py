import subprocess
import sys
import os
import pytest
import pathlib


@pytest.fixture
def project_path(request):
    rootpath = request.config.rootpath
    return pathlib.Path(rootpath)


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
    decode = ns["decode"]
    instr_bytes = ns["get_decoder_eval_bytes"]()
    # fmt: off

    tests = [
        # bl 40
        (b"\xf0\x00\xf8\x14", ns["BL"](imm32=40)),
        # bl 33928
        (b"\xf0\x08\xfa\x44", ns["BL"](imm32=33928)),
        # bl -676
        (b"\xf7\xff\xfe\xae", ns["BL"](imm32=-676)),
        # bl -32
        (b"\xf7\xff\xff\xf0", ns["BL"](imm32=-32)),
        # movs r0, #22
        (b"\x20\x16", ns["MOV_immediate"](d=0, setflags=True, imm32=22, carry=0)),
        # mov r9, #1
        (b"\xf0\x4f\x09\x01", ns["MOV_immediate"](d=9, setflags=False, imm32=1, carry=0)),
        # mov.w   r3, #1073741824 ; 0x40000000
        (b"\xf0\x4f\x43\x80", ns["MOV_immediate"](d=3, setflags=False, imm32=1 << 30, carry=0)),
        # mov.w   r3, #32768 ; 0x8000
        (b"\xf4\x4f\x43\x00", ns["MOV_immediate"](d=3, setflags=False, imm32=0x8000, carry=0)),
        # movw    r3, #1234 ; 0x4d2
        (b"\xf2\x40\x43\xd2", ns["MOV_immediate"](d=3, setflags=False, imm32=1234, carry=0)),
        # add r1, pc, #196  (ADR)
        (b"\xa1\x31", ns["ADR"](d=1, imm32=196, add=True)),
        # bkpt 0x00ab
        (b"\xbe\xab", ns["BKPT"](imm32=0x00AB)),
        # ldr r0, [pc, #192]
        (b"\x48\x30", ns["LDR_literal"](t=0, imm32=192, add=True)),
        # ldr.w	r8, [pc, #228]
        (b"\xf8\xdf\x80\xe4", ns["LDR_literal"](t=8, imm32=228, add=True)),
        # mov r3, r5
        (b"\x46\x2b", ns["MOV_register"](d=3, m=5, setflags=False)),
        # movs r2, r3
        (b"\x00\x1a", ns["MOV_register"](d=2, m=3, setflags=True)),
        # movs.w	ip, r0
        (b"\xea\x5f\x0c\x00", ns["MOV_register"](d=12, m=0, setflags=True)),
        # mov.w	r3, r1, lsr #9 / LSR r3,r1,#9
        (b"\xea\x4f\x23\x51", ns["LSR_immediate"](d=3, m=1, setflags=False, shift_n=9)),
        # movs.w r3, r1, lsr #9 / LSRS r3,r1,#9
        (b"\xea\x5f\x23\x51", ns["LSR_immediate"](d=3, m=1, setflags=True, shift_n=9)),
        # lsrs	r3, r5, #6
        (b"\x09\xab", ns["LSR_immediate"](d=3, m=5, setflags=True, shift_n=6)),
        # nop
        (b"\xbf\00", ns["NOP"]()),
        # nop.w
        (b"\xf3\xaf\x80\x00", ns["NOP"]()),
        # adc.w	r4, r4, #253 ; 0xfd
        (b"\xf1\x44\x04\xfd", ns["ADC_immediate"](d=4, n=4, setflags=False, imm32=253)),
        # adds	r0, r7, #4
        (b"\x1d\x38", ns["ADD_immediate"](d=0, n=7, setflags=True, imm32=0x4)),
        # add r1, r1, #1
        (b"\x31\x01", ns["ADD_immediate"](d=1, n=1, setflags=True, imm32=0x1)),
        # add.w r0, r12, #10  (ADDW T4; corrected encoding, bit20=0, imm8=0x0A)
        (b"\xf2\x0c\x00\x0a", ns["ADD_immediate"](d=0, n=12, setflags=False, imm32=10)),
        # add.w r1, r1, #1048576 @0x100000
        (b"\xf5\x01\x11\x80", ns["ADD_immediate"](d=1, n=1, setflags=False, imm32=0x100000)),
        # adc.w	r1, r1, r4, lsl #20
        (b"\xeb\x41\x51\x04", ns["ADC_register"](d=1, n=1, m=4, setflags=False, shift_t=1, shift_n=20)),
        # adcs	r5, r5
        (b"\x41\x6d", ns["ADC_register"](d=5, n=5, m=5, setflags=True, shift_t=1, shift_n=0)),
        # ldr r1, [r0, #4]
        (b"\x68\x41", ns["LDR_immediate"](t=1, n=0, imm32=0x4, index=True, add=True, wback=False)),
        # ldr	r3, [sp, #0]
        (b"\x9b\x00", ns["LDR_immediate"](t=3, n=13, imm32=0x0, index=True, add=True, wback=False)),
        # ldr.w	r1, [r0, #171]
        (b"\xf8\xdc\x00\xAB", ns["LDR_immediate"](t=0, n=12, imm32=0xAB, index=True, add=True, wback=False)),
        # ldr.w	r4, [r0, #-8]
        (b"\xf8\x50\x4c\x08", ns["LDR_immediate"](t=4, n=0, imm32=0x8, index=True, add=False, wback=False)),
        # cmp	r3, #39	@ 0x27
        (b"\x2b\x27", ns["CMP_immediate"](n=3, imm32=0x27)),
        # cmp.w	r3, #500  @ 0x1f4
        (b"\xf5\xb3\x7f\xfa", ns["CMP_immediate"](n=3, imm32=0x1f4)),
        # str r1, [r2, #0]
        (b"\x60\x11", ns["STR_immediate"](t=1, n=2, imm32=0x0, index=True, add=True, wback=False)),
        # str r0, [r7, #4]
        (b"\x60\x78", ns["STR_immediate"](t=0, n=7, imm32=0x4, index=True, add=True, wback=False)),
        # str r3, [sp, #0]
        (b"\x93\x00", ns["STR_immediate"](t=3, n=13, imm32=0x0, index=True, add=True, wback=False)),
        # str.w	r3, [r0, #0]
        (b"\xf8\xcc\x00\x00", ns["STR_immediate"](t=0, n=12, imm32=0x0, index=True, add=True, wback=False)),
        # str.w	r3, [r0, #-4]
        (b"\xf8\x40\x3c\x04", ns["STR_immediate"](t=3, n=0, imm32=0x4, index=True, add=False, wback=False)),
        # beq.n	2
        (b"\xd0\x01", ns["B"](imm32=0x2, cond=0)),
        # b.n 2
        (b"\xe0\x01", ns["B"](imm32=0x2, cond=0)),
        # beq.w	+336
        (b"\xf0\x00\x80\xa8", ns["B"](imm32=336, cond=0)),
        # bgt.w	dae4 -- gt = 12
        (b"\xf3\x00\x80\xab", ns["B"](imm32=342, cond=12)),
        # b.w -190 (- 0xBE)
        (b"\xf7\xff\xbf\xa1", ns["B"](imm32=-190, cond=0)),
        # subs	r2, r2, r0
        (b"\x1a\x12", ns["SUB_register"](d=2, n=2, m=0, setflags=True, shift_t=1, shift_n=0)),
        # subs.w	r2, r2, ip
        (b"\xeb\xb2\x02\x0c", ns["SUB_register"](d=2, n=2, m=12, setflags=True, shift_t=1, shift_n=0)),
        # push	{r1}
        (b"\xb4\x02", ns["PUSH"](t=0, registers=0x2, UnalignedAllowed=False)),
        # stmdb	sp!, {r4, r5, r6, r7, r8, lr}  (== push.w)
        (b"\xe9\x2d\x41\xf0", ns["PUSH"](t=0, registers=0x41F0, UnalignedAllowed=False)),
        # ldmia   r2!, {r0, r1}
        (b"\xca\x03", ns["LDM"](n=2, registers=0x3, wback=True)),
        # ldmia   r2!, {}  -- register_list=0 → UNPREDICTABLE pseudo-instruction
        (b"\xca\x00", ns["Unpredictable"](code=0xCA00)),
        # add r8, r1  -- DN:Rdn, Rdn is 3 bits wide in this encoding
        (b"\x44\x88", ns["ADD_register"](d=8, n=8, m=1, setflags=False, shift_t=1, shift_n=0)),
        # add sp, r8  -- DM:Rdm, Rdm is 3 bits wide in this encoding
        (b"\x44\xc5", ns["ADD_SP_plus_register"](d=13, m=8, setflags=False, shift_t=1, shift_n=0)),
        # pop {r0, pc}  -- P:'0000000':register_list
        (b"\xbd\x01", ns["POP"](t=0, registers=0x8001, UnalignedAllowed=False)),
        # push {r4, lr}  -- '0':M:'000000':register_list
        (b"\xb5\x10", ns["PUSH"](t=0, registers=0x4010, UnalignedAllowed=False)),
    ]
    # fmt: on

    data = bytes()
    for adr in tests:
        data = data + adr[0]

    context = Context()

    adr = 0
    i = 0

    while i < len(tests):
        # Read the maximum instruction width and MSB-align it (the vectors are
        # big-endian per instruction); a short tail is zero-extended into the low bits.
        chunk = data[adr : adr + instr_bytes]
        instr = int.from_bytes(chunk, "big") << ((instr_bytes - len(chunk)) * 8)

        # decode reports the decoded instruction and how many bytes it occupies
        out, n_bytes = decode(instr, ctx=context)

        assert out == tests[i][1]
        adr += n_bytes
        i += 1
