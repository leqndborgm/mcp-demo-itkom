"""Formatting helpers for QSC API responses."""

from server.config import QSC_RESULT_KEY

# Attribute IDs we care about, mapped to display labels
_ATTR_LABELS = {
    "grundfarbe000": "Farbe",
    "material000": "Material",
    "material001": "Material",
    "gewicht": "Gewicht",
    "einsatzbereich002": "Einsatzbereich",
    "ausfhrung001": "Ausführung",
    "anwendung001": "Anwendung",
    "oberflche000": "Oberfläche",
    "serie000": "Serie",
}

# Dimension attributes — combined into a single "Maße" line
_DIM_IDS = {"breite001": "B", "hhe000": "H", "tiefe000": "T"}


def _extract_category(doc: dict) -> str:
    """Extract the deepest category name from the nested categories structure."""
    categories = doc.get("categories", [])
    if not categories:
        return ""
    levels = categories[0].get("category", [])
    named = [c.get("name", "") for c in levels if c.get("level", 0) > 0]
    return named[-1] if named else ""


def _extract_attrs(doc: dict) -> dict[str, str]:
    """Extract key attributes from the attributes array."""
    attrs = {}
    dims = {}

    for a in doc.get("attributes", []):
        aid = a.get("id", "")
        values = a.get("values", [])
        if not values:
            continue
        unit = a.get("unit", "")
        val_str = str(values[0])

        if aid in _DIM_IDS:
            dims[_DIM_IDS[aid]] = f"{val_str} {unit}".strip()
        elif aid in _ATTR_LABELS:
            label = _ATTR_LABELS[aid]
            if label in attrs:
                continue  # keep first match (e.g. material000 over material001)
            formatted = f"{val_str} {unit}".strip() if unit else val_str
            attrs[label] = formatted

    if dims:
        parts = [f"{k} {v}" for k, v in dims.items() if v]
        attrs["Maße"] = " x ".join(parts)

    return attrs


def _format_full(item: dict) -> str:
    """Full detail block for a single product."""
    p = item.get("document", {})
    title = p.get("title", "N/A")
    pid = item.get("id", "")
    brand = p.get("brand", "")
    image = p.get("image", "")
    url = p.get("url", "")
    desc = (p.get("description") or "")[:200].strip()
    cat = _extract_category(p)
    attrs = _extract_attrs(p)

    lines = [f"### {title}"]

    if image:
        lines.append(f"![{title}]({image})")

    meta = [f"**Artikel-Nr:** {pid}"]
    if brand:
        meta.append(f"**Marke:** {brand}")
    if cat:
        meta.append(f"**Kategorie:** {cat}")
    lines.append(" | ".join(meta))

    if attrs:
        attr_parts = [f"**{k}:** {v}" for k, v in attrs.items()]
        lines.append(" | ".join(attr_parts))

    if desc:
        lines.append("")
        lines.append(desc)

    if url:
        lines.append(f"\n[Zum Produkt]({url})")

    return "\n".join(lines)


def _format_advertise(item: dict) -> str:
    """One-liner teaser for further suggestions."""
    p = item.get("document", {})
    title = p.get("title", "N/A")
    pid = item.get("id", "")
    brand = p.get("brand", "")
    cat = _extract_category(p)

    parts = [f"**{title}** ({pid})"]
    detail = []
    if brand:
        detail.append(brand)
    if cat:
        detail.append(cat)
    if detail:
        parts.append(" | ".join(detail))

    return "- " + " — ".join(parts)


def format_qsc_results(result: dict, detail_level: str = "") -> str:
    """Format QSC API results based on detail level.

    detail_level:
      ""          — full detail (structured product blocks)
      "advertise" — one-liner teasers
    """
    documents = result.get("result", {}).get(QSC_RESULT_KEY, {}).get("documents", [])

    if not documents:
        return "Keine Produkte gefunden."

    if detail_level == "advertise":
        return "\n".join(_format_advertise(item) for item in documents[:5])

    return "\n\n---\n\n".join(_format_full(item) for item in documents[:5])
