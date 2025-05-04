from decoder_forge.associated_struct_repo import AssociatedStructRepo
from decoder_forge.associated_struct_repo import StructDef
from decoder_forge.pattern import Pattern


def test_build_empty_struct_def_and_empty_pat_repo_has_structs_with_undef_member():
    struct_def = {}
    pat_repo = {}

    asrepo = AssociatedStructRepo.build(struct_def=struct_def, pat_repo=pat_repo)

    assert asrepo.structs == [StructDef(name="Undef", members=["instr"])]


def test_build_empty_struct_def_and_empty_pat_repo_has_empty_pat_to_struct():
    struct_def = {}
    pat_repo = {}

    asrepo = AssociatedStructRepo.build(struct_def=struct_def, pat_repo=pat_repo)

    assert asrepo.pat_to_struct == {}


def test_build_empty_struct_def_and_filled_pat_repo_has_correct_pat_to_struct():
    struct_def = {}
    pat_repo = {
        Pattern(fixedmask=0x1, fixedbits=0x0, bit_length=8): {},
        Pattern(fixedmask=0x2, fixedbits=0x0, bit_length=8): {},
        Pattern(fixedmask=0x4, fixedbits=0x0, bit_length=8): {},
    }

    asrepo = AssociatedStructRepo.build(struct_def=struct_def, pat_repo=pat_repo)

    assert asrepo.pat_to_struct == {
        Pattern(fixedmask=0x1, fixedbits=0x0, bit_length=8): StructDef(
            name="Undef", members=["instr"]
        ),
        Pattern(fixedmask=0x2, fixedbits=0x0, bit_length=8): StructDef(
            name="Undef", members=["instr"]
        ),
        Pattern(fixedmask=0x4, fixedbits=0x0, bit_length=8): StructDef(
            name="Undef", members=["instr"]
        ),
    }


def test_build_empty_struct_def_and_filled_pat_repo_has_structs_with_undef_member():
    struct_def = {}
    pat_repo = {
        Pattern(fixedmask=0x1, fixedbits=0x0, bit_length=8): {},
        Pattern(fixedmask=0x2, fixedbits=0x0, bit_length=8): {},
        Pattern(fixedmask=0x4, fixedbits=0x0, bit_length=8): {},
    }

    asrepo = AssociatedStructRepo.build(struct_def=struct_def, pat_repo=pat_repo)

    assert asrepo.structs == [StructDef(name="Undef", members=["instr"])]


def test_build_filled_struct_def_and_empty_pat_repo_has_correct_structs():
    struct_def = {
        "StructA": {"members": ["a"]},
        "StructB": {"members": ["b"]},
        "StructC": {"members": ["c"]},
    }
    pat_repo = {}

    asrepo = AssociatedStructRepo.build(struct_def=struct_def, pat_repo=pat_repo)

    # undef always comes last
    assert asrepo.structs == [
        StructDef(name="StructA", members=["a"]),
        StructDef(name="StructB", members=["b"]),
        StructDef(name="StructC", members=["c"]),
        StructDef(name="Undef", members=["instr"]),
    ]


def test_build_filled_struct_def_and_empty_pat_repo_has_correct_pat_to_struct():
    struct_def = {
        "StructA": {"members": ["a"]},
        "StructB": {"members": ["b"]},
        "StructC": {"members": ["c"]},
    }
    pat_repo = {}

    asrepo = AssociatedStructRepo.build(struct_def=struct_def, pat_repo=pat_repo)

    assert asrepo.pat_to_struct == {}


def test_build_filled_struct_def_and_filled_pat_repo_has_correct_pat_to_struct():
    struct_def = {
        "StructA": {"members": ["a"]},
        "StructB": {"members": ["b"]},
        "StructC": {"members": ["c"]},
    }
    pat_repo = {
        Pattern(fixedmask=0x1, fixedbits=0x0, bit_length=8): {},
        Pattern(fixedmask=0x2, fixedbits=0x0, bit_length=8): {"to": "StructA"},
        Pattern(fixedmask=0x4, fixedbits=0x0, bit_length=8): {"to": "StructC"},
    }

    asrepo = AssociatedStructRepo.build(struct_def=struct_def, pat_repo=pat_repo)

    assert asrepo.pat_to_struct == {
        Pattern(fixedmask=0x1, fixedbits=0x0, bit_length=8): StructDef(
            name="Undef", members=["instr"]
        ),
        Pattern(fixedmask=0x2, fixedbits=0x0, bit_length=8): StructDef(
            name="StructA", members=["a"]
        ),
        Pattern(fixedmask=0x4, fixedbits=0x0, bit_length=8): StructDef(
            name="StructC", members=["c"]
        ),
    }


def test_build_filled_struct_def_and_filled_pat_repo_has_correct_structs():
    struct_def = {
        "StructA": {"members": ["a"]},
        "StructB": {"members": ["b"]},
        "StructC": {"members": ["c"]},
    }
    pat_repo = {
        Pattern(fixedmask=0x1, fixedbits=0x0, bit_length=8): {},
        Pattern(fixedmask=0x2, fixedbits=0x0, bit_length=8): {"to": "StructA"},
        Pattern(fixedmask=0x4, fixedbits=0x0, bit_length=8): {"to": "StructC"},
    }

    asrepo = AssociatedStructRepo.build(struct_def=struct_def, pat_repo=pat_repo)

    assert asrepo.structs == [
        StructDef(name="StructA", members=["a"]),
        StructDef(name="StructB", members=["b"]),
        StructDef(name="StructC", members=["c"]),
        StructDef(name="Undef", members=["instr"]),
    ]
