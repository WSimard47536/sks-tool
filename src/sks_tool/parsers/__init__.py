"""Parsers: read a ``Document`` into the structure for its type.

``base`` holds the ``Parser`` interface and ``CommonParser``, which reads the
part shared by every document: its front matter keys. Each document type has its own
package with a ``parser.py`` (``parsers/<type>/parser.py``).

This module is kept free of imports so importing a type's parser never pulls
in the registry of document types, which imports every parser.
"""
