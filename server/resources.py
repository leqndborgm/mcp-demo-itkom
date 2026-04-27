"""MCP resources — registered via import side-effect."""

from server.app import mcp

CATALOG_INFO = """# BauMax Katalog-Übersicht

## Sortiment (Top-Kategorien)
- Garten
- Maschinen, Werkzeug & Werkstatt
- Innendeko & Bildershop
- Farben, Tapeten & Wandverkleidungen
- Holz, Fenster & Türen
- Bad & Sanitär
- Eisenwaren
- Bodenbeläge & Fliesen
- Baustoffe
- Smart Home Systeme & Geräte
- Leuchten & Elektro
- Küche
- Heizen, Klima & Lüftung
- Zoo & Aquaristik

## Wichtige Marken
Makita, Bosch Professional, PROREGAL, Velux, ARON, Gutta, Soluna, Pertura, weka, dobar, Alpertec, KWB, Brennenstuhl, JBL

## Hinweise
- Über 500.000 Produkte im Katalog
- Schwerpunkt: Bau, Renovierung, Garten, Werkzeug, Heimwerken
- Kein Elektronik-Fachhandel (keine Laptops, Smartphones etc.)
"""


@mcp.resource("resource://catalog-info")
async def catalog_info() -> str:
    """Overview of the BauMax product catalog: categories, brands, and scope."""
    return CATALOG_INFO
