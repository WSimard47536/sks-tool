"""Validators: check the structure of a document against the SKS rules.

``base`` holds the ``Validator`` interface and ``CommonValidator``, which runs
the checks shared by every document. Each document type has its own package
with a ``validator.py`` (``validators/<type>/validator.py``).
"""
