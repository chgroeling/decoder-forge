from bit_match_gen.patricia.patricia import PatriciaTree

def example1():
    # Example usage
    tree = PatriciaTree()
    tree.insert("hello", lambda: print("Hello"))
    tree.insert("helium", lambda: print("Helium"))
    tree.insert("hero", lambda: print("Hero"))
    tree.insert("master", lambda: print("Master"))
    tree.insert("mastering", lambda: print("Mastering"))
    tree.insert("mastricht", lambda: print(""))
    action = tree.search("mastering")
    if action:
        action()  # Should print "Hello"

    tree.print_tree()  # Visualize the tree


def example2():
    # Example usage
    tree = PatriciaTree()
    tree.insert("110001", lambda: print("Hello"))
    tree.insert("110010", lambda: print("Helium"))
    tree.insert("110100", lambda: print("Hero"))
    tree.insert("110000", lambda: print("Master"))
    tree.insert("111000", lambda: print("Mastering"))
    tree.insert("011111", lambda: print(""))
    action = tree.search("mastering")
    if action:
        action()  # Should print "Hello"

    tree.print_tree()  # Visualize the tree


def main():
    example2()
