#!/usr/bin/env python3

# run with
# PYTHONPATH=$PYTHONPATH:. python scripts/update_docs_index.py

from backend.services.context_enhancer import CodeContextEnhancer

e = CodeContextEnhancer()
e.refresh_persisted_index()
