"""Document parsers.

``common`` is the main parser: it runs the checks shared by every document
type, then hands the document to the parser for its own type (one module per
type in this package).
"""
