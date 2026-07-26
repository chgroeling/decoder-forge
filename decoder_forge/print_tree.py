from decoder_forge.pattern_algorithms import flatten_decode_tree
from decoder_forge.pattern_algorithms import DecodeTree


TREE_INDENT_WIDTH = 20


def print_tree(printer, decode_tree: DecodeTree, f_uid_to_str):
    """
    Print a hierarchical tree of bit patterns in a formatted manner.

    This function first flattens the hierarchical DecodeTree into a list of tuples.
    Each tuple contains a BitPattern, its origin, the depth in the tree, a flag
    indicating if it is the first child and a flag indicating if it is the last
    child at that level. It then formats each node with appropriate indentation
    and prints it using the provided printer.

    Args:
        printer: Writable stream with a ``write(str)`` method.
        pat_tree (DecodeTree): The root of the DecodeTree to be printed.
        repo (dict): A repository mapping patterns to additional metadata (e.g., names).

    Examples:
        >>> # Assume printer is an object implementing IPrinter and repo is a proper
            dictionary
        >>> print_tree(printer, pattern_tree, repo)
    """

    flattend_tree = flatten_decode_tree(decode_tree)

    for item, uid, depth, first_child, last_child in flattend_tree:
        indent = "│ " * depth
        if depth == 0:
            printer.write("\n")

        if uid != "":
            if not last_child:
                tree_node = f"{indent}├─ x"
            else:  # in case the next element will be one depth up
                tree_node = f"{indent}└─ x"

            fmt_tree_node = f"{tree_node:{TREE_INDENT_WIDTH}}"

            uid_str = f_uid_to_str(uid)
            printer.write(f"{fmt_tree_node}| {str(item)} | {uid_str}\n")
        else:
            tree_node = f"{indent}├─┐"
            fmt_tree_node = f"{tree_node:{TREE_INDENT_WIDTH}}"
            printer.write(f"{fmt_tree_node}| {str(item)}\n")
