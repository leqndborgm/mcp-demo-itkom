"""Merkzettel — named, persistent product lists across a session.

B2B use case: contractors maintain separate lists per project
("Projekt Müller", "Projekt Schmidt") and export them for ordering.
State is in-memory and lives as long as the server process runs.
"""

from datetime import datetime

from server.app import mcp
from server.state import merkzettel_lists as _lists
from server.utils import time_it


def _get_or_create(list_name: str) -> list[dict]:
    return _lists.setdefault(list_name, [])


def _format_list(list_name: str, items: list[dict]) -> str:
    """Render a single Merkzettel as a markdown table."""
    lines = [
        f"## Merkzettel: {list_name}",
        f"*{len(items)} Artikel*",
        "",
        "| # | Produkt | Artikel-Nr. | Menge | Notiz |",
        "|---|---------|-------------|-------|-------|",
    ]
    for i, item in enumerate(items, 1):
        note = item.get("notes") or "—"
        lines.append(
            f"| {i} | {item['name']} | `{item['id']}` | {item['quantity']} | {note} |"
        )
    return "\n".join(lines)


@mcp.tool()
@time_it
async def merkzettel_add(
    product_id: str,
    product_name: str,
    list_name: str = "Standard",
    quantity: int = 1,
    notes: str = "",
) -> str:
    """
    Add a product to a named Merkzettel (project list / wishlist).

    INSTRUCTIONS FOR AI:
    Trigger this tool when the user says anything like:
    "auf die Liste", "merken", "Merkzettel", "zu Projekt X hinzufügen",
    "das nehm ich", "bookmarken", "speichern".

    Use the product_id (Artikel-Nr.) and product_name from the most recent search result.
    If the user names a project, use it as list_name (e.g. "Projekt Müller").
    If adding multiple products at once, call this tool once per product.

    - product_id:   Artikel-Nr. from the product result (e.g. "4711")
    - product_name: Product title, as shown in search results
    - list_name:    Project or list name — default is "Standard"
    - quantity:     Number of units the user wants (default: 1)
    - notes:        Optional free-text note (e.g. "für OG Bad", "günstigste Option prüfen")
    """
    items = _get_or_create(list_name)

    # If already on list: update quantity and notes instead of duplicating
    for item in items:
        if item["id"] == product_id:
            item["quantity"] += quantity
            if notes:
                item["notes"] = notes
            return (
                f"'{product_name}' ist bereits auf '{list_name}' — "
                f"Menge aktualisiert auf {item['quantity']}."
            )

    items.append({
        "id": product_id,
        "name": product_name,
        "quantity": quantity,
        "notes": notes,
        "added_at": datetime.now().strftime("%H:%M"),
    })

    return (
        f"'{product_name}' wurde zu '{list_name}' hinzugefügt. "
        f"({len(items)} Artikel auf der Liste)"
    )


@mcp.tool()
@time_it
async def merkzettel_view(list_name: str = "") -> str:
    """
    Show the contents of one or all Merkzettel lists.

    INSTRUCTIONS FOR AI:
    - Leave list_name empty to show ALL lists.
    - Provide list_name to show a specific list.
    - Always call this when the user asks:
      "was ist auf meiner Liste", "zeig Merkzettel", "was hab ich gemerkt",
      "welche Projekte hab ich", "zeig Projekt X".
    - After displaying, offer to export, remove items, or continue searching.
    """
    active = {name: items for name, items in _lists.items() if items}

    if not active:
        return "Alle Merkzettel sind leer. Produkte können mit 'auf die Liste' hinzugefügt werden."

    if list_name:
        items = _lists.get(list_name)
        if not items:
            known = ", ".join(f"'{n}'" for n in active) or "keine"
            return (
                f"Merkzettel '{list_name}' ist leer oder existiert nicht. "
                f"Vorhandene Listen: {known}."
            )
        return _format_list(list_name, items)

    # Show all active lists
    parts = [_format_list(name, items) for name, items in active.items()]
    summary = f"**{len(active)} aktive Liste(n): {', '.join(active)}**\n\n"
    return summary + "\n\n---\n\n".join(parts)


@mcp.tool()
@time_it
async def merkzettel_remove(
    product_id: str,
    list_name: str = "Standard",
) -> str:
    """
    Remove a specific product from a Merkzettel by its Artikel-Nr.

    INSTRUCTIONS FOR AI:
    Use when the user says "entfern das", "lösch das von der Liste",
    "das will ich doch nicht", "raus aus Projekt X".
    Use the product_id (Artikel-Nr.) of the item to remove.
    If unsure which list, call merkzettel_view first to confirm.
    """
    items = _lists.get(list_name, [])
    removed = [i for i in items if i["id"] == product_id]

    if not removed:
        return f"Artikel-Nr. '{product_id}' wurde auf '{list_name}' nicht gefunden."

    _lists[list_name] = [i for i in items if i["id"] != product_id]
    remaining = len(_lists[list_name])
    return (
        f"'{removed[0]['name']}' von '{list_name}' entfernt. "
        f"Noch {remaining} Artikel auf der Liste."
    )


@mcp.tool()
@time_it
async def merkzettel_clear(list_name: str = "Standard") -> str:
    """
    Remove all items from a Merkzettel.

    INSTRUCTIONS FOR AI:
    Only use when the user EXPLICITLY asks to clear or delete the entire list
    (e.g. "liste leeren", "alles löschen", "Projekt X abschließen").
    Do NOT call this speculatively. If there are 5+ items, confirm with the user first.
    """
    items = _lists.get(list_name, [])
    if not items:
        return f"Merkzettel '{list_name}' ist bereits leer."

    count = len(items)
    _lists[list_name] = []
    return f"Merkzettel '{list_name}' wurde geleert ({count} Artikel entfernt)."
