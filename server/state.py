"""Shared in-memory state — importable by tools AND HTTP route handlers.

Kept in its own module to avoid circular imports:
  tools/merkzettel.py  → state.py  (writes)
  app.py               → state.py  (reads for API endpoint)
"""

# list_name → ordered list of product dicts
# Each item: {id, name, quantity, notes, added_at}
merkzettel_lists: dict[str, list[dict]] = {}
