from decoder_forge.bit_pattern import BitPattern
from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class StructDef:
    """Represents a structured data type with a name and a list of member identifiers.

    Attributes:
        name (str): The name of the structure.
        members (list[str]): A list of member names belonging to this structure.
    """

    name: str
    members: list[str]


class AssociatedStructRepo:
    """Repository mapping patterns to structures.

    This class holds a collection of structures along with a mapping from BitPattern
    objects to these structures. It is used to manage the association between individual
    patterns and their corresponding structure definitions.
    """

    def __init__(
        self,
        structs: list[StructDef],
        pat_to_struct: dict[BitPattern, StructDef],
    ):
        """Initializes the repository with given structures and pattern to structure
        mapping.

        Args:
            structs (list[Struct]): A list of structure objects.
            pat_to_struct (dict[BitPattern, Struct]): A dictionary mapping BitPattern objects
                to their corresponding Struct objects.
        """

        self.structs = structs
        self.pat_to_struct = pat_to_struct

    def __repr__(self) -> str:
        return (
            "AssociatedStructRepo("
            + f"structs={repr(self.structs)} "
            + f"pat_to_struct={repr(self.pat_to_struct)}"
            + ")"
        )

    @staticmethod
    def build(
        struct_def: dict[str, dict[str, str]],
        pat_repo: dict[BitPattern, dict[str, str]],
    ):
        """Builds an AssociatedStructRepo instance from structure definitions and
        a pattern repository.

        This method processes dictionary-based structure definitions and a repository
        of patterns to create corresponding Struct objects, and maps each BitPattern to a
        Struct. A special 'Undef' structure is added for internal purposes. If the
        structure definitions already contain a structure named 'Undef', a ValueError
        is raised.

        Args:
            struct_def (dict[str, dict[str, str]]): A dictionary where the key is the
                structure name and the value is another dictionary containing details
                of the structure. Expected to have a key "members" with its value
                (implicitly convertible to a list) representing the members.
            pat_repo (dict[BitPattern, dict[str, str]]): A dictionary mapping BitPattern
                objects to dictionaries containing pattern details. Each inner
                dictionary may contain a "to" key indicating which structure the
                pattern maps to.

        Returns:
            AssociatedStructRepo: An instance of AssociatedStructRepo containing all
            created Structs and the mapping from BitPatterns to Structs.

        Raises:
            ValueError: If a structure with the name 'Undef' exists in the provided
                struct_def; 'Undef' is reserved for internal use.
        """

        # Read all structs
        name_to_struct = {
            name: StructDef(
                name=name, members=list(i["members"] if "members" in i else list())
            )
            for name, i in struct_def.items()
        }

        # Add Undef struct for internal use
        if "Undef" in name_to_struct:
            raise ValueError(
                "The struct name 'Undef' is forbidden. Its used for internal purposes"
            )

        name_to_struct["Undef"] = StructDef(name="Undef", members=["code"])

        # Map patterns on structs
        def get_to_or_undef(pat_data: dict[str, str]):
            if "to" not in pat_data:
                return "Undef"
            return pat_data["to"]

        pat_to_struct = {
            pat: name_to_struct[get_to_or_undef(pat_data)]
            for pat, pat_data in pat_repo.items()
        }

        return AssociatedStructRepo(
            structs=list(name_to_struct.values()), pat_to_struct=pat_to_struct
        )
