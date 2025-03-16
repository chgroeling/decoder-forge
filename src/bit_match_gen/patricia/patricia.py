class Node:
    """
    A class representing a node in a Patricia Tree.

    Attributes:
        label (str): The label for this node.
        data (any): The data or action associated with this node.
        children (dict): A dictionary of child nodes, where the keys are labels
                         and the values are Node instances.

    Parameters:
        label (str, optional): The label for the node. Defaults to None.
        data (any, optional): The data associated with the node. Defaults to None.
    """

    def __init__(self, label=None, data=None):
        """
        Initializes a Node with a given label and optional data.

        Args:
            label (str, optional): The label for the node. Defaults to None.
            data (any, optional): The data associated with the node. Defaults to None.
        """

        self.label = label
        self.data = data
        self.children = dict()


class PatriciaTree:
    def __init__(self):
        self.root = Node()

    def insert(self, key, action):
        current_node = self.root
        while True:
            if not current_node.children:
                current_node.children[key] = Node(key, action)
                return

            match = False
            for label, child_node in list(current_node.children.items()):
                prefix_length = self._longest_common_prefix_length(key, label)
                if prefix_length > 0:
                    if prefix_length == len(label):
                        key = key[prefix_length:]
                        current_node = child_node
                        if not key:
                            child_node.data = action
                            return
                        match = True
                        break
                    else:
                        new_node = Node(label[:prefix_length])
                        new_node.children[label[prefix_length:]] = child_node
                        child_node.label = label[prefix_length:]

                        if prefix_length == len(key):
                            new_node.data = action
                        else:
                            new_node.children[key[prefix_length:]] = Node(
                                key[prefix_length:], action
                            )

                        current_node.children[label[:prefix_length]] = new_node
                        del current_node.children[label]
                        return
            if not match:
                current_node.children[key] = Node(key, action)
                return

    def search(self, key):
        def search_rec(node, key):
            if not node:
                return None

            if key == "":
                return node.data if node.data is not None else None

            for label, child_node in node.children.items():
                if key.startswith(label):
                    return search_rec(child_node, key[len(label) :])
                elif label.startswith(key):
                    return child_node.data
                elif "." in label or "." in key:
                    match_length = self._match_length_with_wildcard(key, label)
                    if match_length > 0:
                        return search_rec(child_node, key[match_length:])
            return None

        return search_rec(self.root, key)

    def _longest_common_prefix_length(self, s1, s2):
        length = min(len(s1), len(s2))
        for i in range(length):
            if s1[i] != s2[i]:
                return i
        return length

    def _match_length_with_wildcard(self, key, label):
        min_length = min(len(key), len(label))
        for i in range(min_length):
            if key[i] != "." and key[i] != label[i]:
                return 0
        return min_length

    def print_tree(self, node=None, prefix=""):
        if node is None:
            node = self.root
        sorted_children = sorted(
            node.children.items(), key=lambda x: (-bool(x[1].data), -len(x[0]), x[0])
        )
        for label, child in sorted_children:
            print(f"{prefix}{label} ({'END' if child.data else 'CONT'})")
            self.print_tree(child, prefix + "  ")
