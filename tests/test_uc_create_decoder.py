from bit_match_gen.patricia.patricia import PatriciaTree
import unittest


class TestCreateDecoder(unittest.TestCase):
    def tqest_insert_creates_correct_structure_single_key(self):
        tree = PatriciaTree()
        tree.insert("key1", lambda: "Data1")
        assert "key1" in tree.root.children
        assert tree.root.children["key1"].data() == "Data1"

 

if __name__ == "__main__":
    unittest.main()
