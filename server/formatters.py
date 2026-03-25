"""Formatting helpers for QSC API responses."""



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

            output.append(f"*- {name} | {pid} | ![Image]({image})")


        if detail_level == "advertise":
            desc = p.get("description", "N/A")[:200] + "..."
            output.append(f"*- {name} | {pid} | {desc} | ![Image]({image})")

        else:
            cat = p.get("category", ["N/A"])
            cat_name = cat[0] if isinstance(cat, list) and cat else str(cat)
            
            desc = p.get("description", "N/A")[:250] + "..."
            output.append(f"*- {name} | {pid} | {cat_name} | {desc} | ![Image]({image})")

    return "\n\n".join(output)
        

