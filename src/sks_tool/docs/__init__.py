"""The structures of SKS documents, one package per document type.

``parsers`` builds these structures from a ``Document``; ``validators`` checks
them. The three packages follow the same layout: ``docs/<type>/doc.py`` holds
the structure, ``parsers/<type>/parser.py`` reads it and
``validators/<type>/validator.py`` checks it. The blocks a document is made of
get their own subpackage inside their type's package, in all three.
"""
