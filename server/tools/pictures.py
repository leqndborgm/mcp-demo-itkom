"""Image-based product discovery tools — identify, match, and recommend from photos."""

import asyncio

from server.app import mcp
from server.api import build_search_body, get_documents, qsc_search
from server.config import QSC_RESULT_KEY
from server.formatters import format_qsc_results
from server.utils import time_it

DISPLAY_ROWS = 3
FETCH_ROWS = 5


@mcp.tool()
@time_it
async def identify_product(
    product_name: str,
    brand: str = "",
    category: str = "",
    attributes: list[str] | None = None,
    confidence: str = "high",
) -> str:
    """
    Identify a product from an uploaded image and find matching items in the BauMax catalog.

    INSTRUCTIONS FOR AI — analyze the image carefully before calling this tool:

    - product_name: Generic, catalog-friendly name. Use the product-category level, not overly
      specific (e.g. "Akkubohrschrauber" not "Latthammer", "Fugenmörtel" not "Portlandzement").
    - brand: Brand or manufacturer name if clearly visible on the product, packaging, or label.
      Leave empty if not recognizable — do NOT guess.
    - category: Product category (e.g. "Elektrowerkzeug", "Baustoffe", "Garten", "Sanitär",
      "Beleuchtung", "Farben & Lacke", "Befestigung").
    - attributes: Notable visual attributes. For consumer products: color, size, material.
      For professional/B2B products also include technical specs: voltage, capacity, drive type,
      application. Examples: ["18V", "kabellos", "Li-Ion", "SDS-Plus", "blau", "1/2 Zoll"].
    - confidence: Set to "high" if the product is clearly visible and recognizable.
      Set to "low" if the image is blurry, partially obscured, or the product type is ambiguous.

    EDGE CASES:
    - Blurry or partial image → confidence="low", use a broader product_name (the category).
    - No brand visible → leave brand empty.
    - Image shows packaging/label → extract product_name from the label text if readable.
    - Multiple products in image → call this tool for the most prominent one, then use
      recommend_for_scene for a full scene analysis.
    - Industrial/professional product → focus on technical attributes (voltage, weight class,
      norm compliance) as these matter most to B2B buyers.
    """
    query = " ".join(k for k in [brand, product_name] if k)
    result = await qsc_search(build_search_body(query, rows=FETCH_ROWS))
    docs = get_documents(result)

    # Fallback 1: product_name only (drop brand)
    if not docs and brand:
        result = await qsc_search(build_search_body(product_name, rows=FETCH_ROWS))
        docs = get_documents(result)

    # Fallback 2: first technical attribute + product_name (e.g. "18V Bohrschrauber")
    if not docs and attributes:
        fallback_query = f"{attributes[0]} {product_name}"
        result = await qsc_search(build_search_body(fallback_query, rows=FETCH_ROWS))
        docs = get_documents(result)

    if not docs:
        if confidence == "low":
            return (
                "Das Bild ist zu unscharf oder das Produkt nicht eindeutig erkennbar. "
                "Bitte lade ein klareres Foto hoch oder beschreibe das Produkt manuell."
            )
        return "Kein passendes Produkt im BauMax-Katalog gefunden."

    confidence_label = "✓ Erkannt" if confidence == "high" else "~ Mögliche Übereinstimmung"
    header_parts = [f"**{confidence_label}:** {product_name}"]
    if brand:
        header_parts.append(f"**Marke:** {brand}")
    if category:
        header_parts.append(f"**Kategorie:** {category}")
    if attributes:
        header_parts.append(f"**Merkmale:** {', '.join(attributes)}")
    header = " | ".join(header_parts)

    main = format_qsc_results({"result": {QSC_RESULT_KEY: {"documents": docs[:DISPLAY_ROWS]}}})

    overflow = docs[DISPLAY_ROWS:]
    if overflow:
        suggestions = format_qsc_results(
            {"result": {QSC_RESULT_KEY: {"documents": overflow}}}, "advertise"
        )
        return f"{header}\n\n{main}\n\nWEITERE TREFFER:\n{suggestions}"

    return f"{header}\n\n{main}"


@mcp.tool()
@time_it
async def find_similar_products(
    product_name: str,
    category: str = "",
    key_features: list[str] | None = None,
    exclude_brand: str = "",
) -> str:
    """
    Find alternative or similar products for a product identified in an image.

    Use this tool when:
    - The user wants alternatives to a specific product they photographed.
    - The user photographs a competitor product and wants BauMax equivalents.
    - The user asks "what else is similar to this?" or "do you have something like this?".

    INSTRUCTIONS FOR AI:
    - product_name: The product type to search alternatives for (e.g. "Akkubohrschrauber",
      "Winkelschleifer", "Fugenmörtel"). Use the generic product category name.
    - category: Narrows the search to a department (e.g. "Elektrowerkzeug", "Baustoffe").
    - key_features: The most important technical or visual features to match, extracted from the
      image. Limit to 2–3 decisive specs (e.g. ["18V", "kabellos"] or ["SDS-Plus", "schlagend"]).
      These drive the search quality — be specific.
    - exclude_brand: Brand to exclude from results (typically the brand already identified in the
      image). Leave empty if the user has no brand preference.

    IMPORTANT: Present alternatives as a professional comparison, not replacements.
    Highlight what makes each option different (specs, price class, application).
    For B2B buyers, note bulk availability, professional series, or system compatibility.
    """
    feature_str = " ".join(key_features[:2]) if key_features else ""
    query = " ".join(k for k in [feature_str, category or product_name] if k)

    result = await qsc_search(build_search_body(query, rows=FETCH_ROWS))
    docs = get_documents(result)

    # Fallback: product name only
    if not docs:
        result = await qsc_search(build_search_body(product_name, rows=FETCH_ROWS))
        docs = get_documents(result)

    # Filter excluded brand — keep original list if filter leaves nothing
    if exclude_brand and docs:
        filtered = [
            d for d in docs
            if exclude_brand.lower()
            not in (d.get("document", {}).get("brand", "") or "").lower()
        ]
        if filtered:
            docs = filtered

    if not docs:
        return f"Keine Alternativen zu '{product_name}' im BauMax-Katalog gefunden."

    header = f"**Alternativen zu:** {product_name}"
    if key_features:
        header += f" | **Gesuchte Merkmale:** {', '.join(key_features)}"
    if exclude_brand:
        header += f" | **Ohne Marke:** {exclude_brand}"

    main = format_qsc_results({"result": {QSC_RESULT_KEY: {"documents": docs[:DISPLAY_ROWS]}}})
    return f"{header}\n\n{main}"


@mcp.tool()
@time_it
async def recommend_for_scene(
    scene_type: str,
    project_description: str,
    needed_products: list[str],
    existing_items: list[str] | None = None,
) -> str:
    """
    Analyze an environment or project photo and recommend products from the BauMax catalog.

    Use this tool when:
    - A user uploads a photo of a space, not a product (garden, room, building site, workshop).
    - The user asks "what do I need for this?" or "what would fit here?".
    - A professional (contractor, facility manager, architect) uploads a project or site photo
      and needs a product recommendation or material list.

    INSTRUCTIONS FOR AI — extract the following from the scene image:
    - scene_type: The type of environment photographed. Be specific.
      Examples: "Garten", "Terrasse", "Badezimmer", "Küche", "Baustelle", "Werkstatt",
      "Keller", "Fassade", "Dach", "Garage", "Lagerraum", "Büro".
    - project_description: A short description of the work or project evident in the photo.
      Think like a B2B advisor: what would a contractor or facility manager do here?
      Examples: "Terrasse mit Naturstein neu pflastern",
                "Badezimmer komplett renovieren inkl. Fliesen und Sanitär",
                "Werkstatt einrichten und ausleuchten",
                "Fassade dämmen und verputzen".
    - needed_products: List of 3–6 specific product types required for this project.
      Think in full project scope — include materials, tools, AND accessories/consumables.
      A contractor needs everything: main materials, fixing materials, tools, safety equipment.
      Examples for garden: ["Rasenmäher", "Gartenschlauch", "Pflastersteine", "Gartenleuchte",
                             "Unkrautvlies", "Randsteine"]
      Examples for bathroom reno: ["Fliesenkleber", "Fugenmörtel", "Silikon", "Wannenträger",
                                    "Fliesenschneider", "Abdichtungsfolie"]
      Examples for building site: ["Schutzhelm", "Arbeitshandschuhe", "Beton", "Schalung",
                                    "Bewehrungsstahl", "Rüttelplatte"]
    - existing_items: Items already visible in the scene that do NOT need to be purchased.
      Avoids redundant suggestions. Examples: ["Rasenmäher vorhanden", "Leiter sichtbar"].

    IMPORTANT: Think like a B2B procurement advisor, not a consumer.
    The goal is a complete, actionable product list a professional could order immediately.
    """
    if not needed_products:
        return (
            "Keine Produktbedürfnisse aus dem Bild erkannt. "
            "Bitte beschreibe das Projekt oder die Szene genauer."
        )

    # Search for all needed products in parallel
    search_tasks = [
        qsc_search(build_search_body(product, rows=2))
        for product in needed_products[:6]
    ]
    results = await asyncio.gather(*search_tasks, return_exceptions=True)

    lines = [
        f"## Produktempfehlungen: {scene_type}",
        f"**Projekt:** {project_description}",
    ]
    if existing_items:
        lines.append(f"**Bereits vorhanden:** {', '.join(existing_items)}")
    lines.append("")

    found_count = 0
    not_found = []

    for product_name, result in zip(needed_products[:6], results):
        if isinstance(result, Exception):
            not_found.append(product_name)
            continue
        docs = get_documents(result)
        if not docs:
            not_found.append(product_name)
            continue

        found_count += 1
        lines.append(f"### {product_name}")
        formatted = format_qsc_results({"result": {QSC_RESULT_KEY: {"documents": docs[:1]}}})
        lines.append(formatted)
        lines.append("")

    if found_count == 0:
        return (
            f"Für die erkannte Szene ({scene_type}: {project_description}) wurden keine "
            "passenden Produkte im BauMax-Katalog gefunden. "
            "Bitte beschreibe das Projekt genauer oder versuche es mit einem anderen Bild."
        )

    total = min(len(needed_products), 6)
    lines.append(f"---\n*{found_count} von {total} Produktkategorien im Katalog gefunden.*")
    if not_found:
        lines.append(f"*Nicht gefunden: {', '.join(not_found)}*")

    return "\n".join(lines)
