decoder-forge documentation 🔨  
==============================

**Craft Decoders for Machine Instructions, Binary Protocols, and Beyond**  

Decoder-forge is a *Python-powered toolkit* that generates source code for decoders used in decoding machine instructions (like ARMv7-M), structured data formats (e.g., MessagePack), and proprietary binary protocols. Whether you’re reverse-engineering firmware, analyzing network packets, or debugging IoT devices, Decoder-forge transforms raw bytes into human-readable insights with flexibility and speed, allowing you to easily create and customize your own decoders.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. autofunction:: decoder_forge.uc_show_decode_tree.print_tree
.. autofunction:: decoder_forge.uc_show_decode_tree.uc_show_decode_tree
   
.. autofunction:: decoder_forge.pattern_algorithms.compute_common_fixedmask
.. autofunction:: decoder_forge.pattern_algorithms.build_groups_by_fixed_bits
.. autofunction:: decoder_forge.pattern_algorithms.build_pattern_tree_by_fixed_bits
.. autofunction:: decoder_forge.pattern_algorithms.flatten_pattern_tree

.. autoclass:: decoder_forge.pattern.Pattern
   :members:               
               
