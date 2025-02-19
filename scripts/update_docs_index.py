from backend.services.context_enhancer import CodeContextEnhancer

e = CodeContextEnhancer()
e.refresh_persisted_index()

# run with
# PYTHONPATH=$PYTHONPATH:. python scripts/update_docs_index.py
