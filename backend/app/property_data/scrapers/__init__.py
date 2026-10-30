"""Multi-source property scraper package."""

from app.property_data.scrapers.jsonld_extractor import extract_from_all_sources
from app.property_data.scrapers.matcher import match_listings, compute_match_score
from app.property_data.scrapers.merger import merge_sources, merge_two_listings
from app.property_data.scrapers.quality import compute_quality_score, get_quality_label
from app.property_data.scrapers.squareyards_v2 import SquareYardsScraperV2
from app.property_data.scrapers.housing import HousingScraper
from app.property_data.scrapers.magicbricks import MagicBricksScraper

__all__ = [
    "extract_from_all_sources",
    "match_listings",
    "compute_match_score",
    "merge_sources",
    "merge_two_listings",
    "compute_quality_score",
    "get_quality_label",
    "SquareYardsScraperV2",
    "HousingScraper",
    "MagicBricksScraper",
]
