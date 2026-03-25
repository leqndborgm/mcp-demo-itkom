"""Formatting helpers for QSC API responses."""


def long_format_qsc_results(result: dict) -> str:
    """Convert a QSC API response dict into user-ready Markdown."""
    formatted_results = ""
    documents = result.get("result", {}).get("products", {}).get("documents", [])

    if not documents:
        return "Keine Produkte gefunden.\n\n**ERFOLGREICH**"

    for item in documents:
        product_doc = item.get("document", {})

        name = product_doc.get("name", product_doc.get("title", "Kein Name"))
        description = product_doc.get("description", "Keine Beschreibung")
        availability = item.get("availability", "Nicht verfügbar")

        category_raw = product_doc.get("category", "PRODUKT")
        if isinstance(category_raw, list) and category_raw:
            category_raw = category_raw[0]
        category_header = f"**{str(category_raw).upper()}**"

        # Image link logic
        image = product_doc.get(
            "publicPreviewImageUrl",
            product_doc.get(
                "publicPreviewImageUrl",
                product_doc.get("imageUrl", ""),
            ),
        )

        # Build block
        formatted_results += f"{category_header}\n"
        formatted_results += f"* **Name:** {name}\n"
        formatted_results += f"* **Verfügbarkeit:** {availability}\n"
        formatted_results += f"* **Beschreibung:** {description}\n"
        if image:
            formatted_results += f"![Image]({image})\n"
        formatted_results += "\n---\n\n"

    return formatted_results.strip()


def format_qsc_results(result: dict, detail_level: str = "") -> str:
    """Clean and format QSC API results based on detail level."""

    documents = result.get("result", {}).get("products", {}).get("documents", [])

    if not documents:
        return "Keine Produkte gefunden."

    output = []

    for item in documents[:5]:
        p = item.get("document", {})

        # Image link logic
        image = p.get(
            "publicPreviewImageUrl",
            p.get(
                "publicPreviewImageUrl",
                p.get("imageUrl", ""),
            ),
        )
        
        name = p.get("name", p.get("title", "N/A"))
        pid = item.get("id", "N/A")

        if detail_level == "compact":

            output.append(f"- {name} | {pid} | {image}")


        if detail_level == "advertise":
            desc = p.get("description", "N/A")[:200] + "..."
            output.append(f"- {name} | {pid} | {desc} | {image}")

        else:
            cat = p.get("category", ["N/A"])
            cat_name = cat[0] if isinstance(cat, list) and cat else str(cat)
            
            desc = p.get("description", "N/A")[:250] + "..."
            output.append(f"- {name} | {pid} | {cat_name} | {desc} | {image}")

    return "\n\n".join(output)
        

