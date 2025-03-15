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
    """
    A class representing a Patricia Tree data structure.

    Attributes:
        root (Node): The root node of the Patricia Tree.

    Methods:
        insert(key, action): Inserts a key along with an associated action into the tree.
        search(key): Searches for a key in the tree and returns the associated action if found.
        print_tree(node=None, prefix=""): Prints the structure of the tree in a human-readable format.
    """

    def __init__(self):
        """
        Initializes an empty Patricia Tree.
        """
        self.root = Node()

    def insert(self, key, action):
        """
        Inserts a key along with an associated action into the Patricia Tree.

        This method traverses the tree, finds the appropriate place for the key,
        and handles splitting nodes if there are common prefixes.

        Args:
            key (str): The key to insert into the tree.
            action (callable): The action or data associated with the key.
        """

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
                        # Split the node
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

    def _longest_common_prefix_length(self, s1, s2):
        """
        Helper function to find the length of the longest common prefix
        between two strings.

        Args:
            s1 (str): The first string.
            s2 (str): The second string.

        Returns:
            int: The length of the longest common prefix.
        """

        length = min(len(s1), len(s2))
        for i in range(length):
            if s1[i] != s2[i]:
                return i
        return length

    def search(self, key):
        """
        Searches for a key in the tree and returns the associated action if found.

        Args:
            key (str): The key to search for in the tree.

        Returns:
            callable or None: The action associated with the key if found, otherwise None.
        """

        current_node = self.root
        while current_node:
            for label, child_node in current_node.children.items():
                if key.startswith(label):
                    if len(key) == len(label):
                        return child_node.data
                    key = key[len(label) :]
                    current_node = child_node
                    break
            else:
                return None

    def print_tree(self, node=None, prefix=""):
        """
        Prints the structure of the tree in a human-readable format.

        Args:
            node (Node, optional): The node to print. If None, starts from the root. Defaults to None.
            prefix (str, optional): The prefix to use for the current level of the tree. Defaults to "".
        """
        if node is None:
            node = self.root
        for label, child in sorted(node.children.items(), key=lambda x: -len(x[0])):
            print(f"{prefix}{label} ({'END' if child.data else 'CONT'})")
            self.print_tree(child, prefix + "  ")

