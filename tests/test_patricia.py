from bit_match_gen.patricia.patricia import PatriciaTree
import unittest


class TestPatriciaTreeInsert(unittest.TestCase):
    def test_insert_creates_correct_structure_single_key(self):
        tree = PatriciaTree()
        tree.insert("key1", lambda: "Data1")
        assert "key1" in tree.root.children
        assert tree.root.children["key1"].data() == "Data1"

    def test_insert_creates_correct_structure_common_prefix(self):
        tree = PatriciaTree()
        tree.insert("prefixA", lambda: "DataA")
        tree.insert("prefixB", lambda: "DataB")

        assert len(tree.root.children) == 1
        assert "prefix" in tree.root.children
        assert "A" in tree.root.children["prefix"].children
        assert "DataA" in tree.root.children["prefix"].children["A"].data()
        assert "B" in tree.root.children["prefix"].children
        assert "DataB" in tree.root.children["prefix"].children["B"].data()

    def test_insert_creates_correct_structure_with_splitting(self):
        tree = PatriciaTree()
        tree.insert("split", lambda: "Original")
        tree.insert("splitting", lambda: "Extended")
        assert "split" in tree.root.children
        assert "ting" in tree.root.children["split"].children

    def test_insert_overwrite_existing(self):
        tree = PatriciaTree()

        def action1():
            return "First"

        def action2():
            return "Second"

        tree.insert("overwrite", action1)
        tree.insert("overwrite", action2)
        self.assertIs(tree.root.children["overwrite"].data, action2)


if __name__ == "__main__":
    unittest.main()
