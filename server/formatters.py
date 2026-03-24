"""Formatting helpers for QSC API responses."""


def format_qsc_results(result: dict) -> str:
    """Convert a QSC API response dict into user-ready Markdown."""
    formatted_results = ""
    documents = result.get("result", {}).get("products", {}).get("documents", [])

    if not documents:
        return "Keine Produkte gefunden.\n\n**ERFOLGREICH**"

    for item in documents:
        product_doc = item.get("document", {})

        name = product_doc.get("name", product_doc.get("title", "Kein Name"))
        product_id = item.get("id", "Keine ID")
        position = item.get("position", item.get("pos", ""))
        description = product_doc.get("description", "Keine Beschreibung")

        category_raw = product_doc.get("category", "PRODUKT")
        if isinstance(category_raw, list) and category_raw:
            category_raw = category_raw[0]
        category_header = f"**{str(category_raw).upper()}**"

        # Image link logic
        image = product_doc.get(
            "publicPreviewImageUrl",
            product_doc.get(
                "privatePreviewImageUrl",
                product_doc.get("imageUrl", ""),
            ),
        )

        # Build block
        formatted_results += f"{category_header}\n"
        formatted_results += f"* **Name:** {name}\n"
        formatted_results += f"* **Produkt-ID:** {product_id}\n"
        if position:
            formatted_results += f"* **Position:** {position}\n"
        formatted_results += f"* **Beschreibung:** {description}\n"
        if image:
            formatted_results += f"![Produktbild]({image})\n"
        formatted_results += "\n---\n\n"

    return formatted_results.strip()
