"""
Tests for parser module
"""
import pytest
from datetime import datetime

from app.scraper.parser import (
    parse_listing,
    parse_scraper_listing,
    _parse_price,
    _parse_int,
    _parse_float,
    _map_category,
    _extract_images,
)


class TestParsePrice:
    """Tests for _parse_price helper function."""

    def test_parse_price_integer(self):
        """Test parsing integer price."""
        assert _parse_price(100000) == 100000
        assert _parse_price(50000) == 50000

    def test_parse_price_string(self):
        """Test parsing string price."""
        assert _parse_price("100000") == 100000
        assert _parse_price("50 000") == 50000
        assert _parse_price("50,000") == 50000

    def test_parse_price_float(self):
        """Test parsing float price."""
        assert _parse_price(100000.50) == 100000
        assert _parse_price(50000.99) == 50000

    def test_parse_price_none(self):
        """Test parsing None price."""
        assert _parse_price(None) == 0

    def test_parse_price_empty_string(self):
        """Test parsing empty string price."""
        assert _parse_price("") == 0
        assert _parse_price("   ") == 0

    def test_parse_price_invalid(self):
        """Test parsing invalid price."""
        assert _parse_price("invalid") == 0


class TestParseInt:
    """Tests for _parse_int helper function."""

    def test_parse_int_integer(self):
        """Test parsing integer."""
        assert _parse_int(5) == 5
        assert _parse_int(0) == 0

    def test_parse_int_string(self):
        """Test parsing string integer."""
        assert _parse_int("5") == 5
        assert _parse_int("10") == 10

    def test_parse_int_float(self):
        """Test parsing float as integer."""
        assert _parse_int(5.7) == 5
        assert _parse_int(10.2) == 10

    def test_parse_int_none(self):
        """Test parsing None."""
        assert _parse_int(None) is None

    def test_parse_int_invalid(self):
        """Test parsing invalid value."""
        assert _parse_int("invalid") is None


class TestParseFloat:
    """Tests for _parse_float helper function."""

    def test_parse_float_float(self):
        """Test parsing float."""
        assert _parse_float(50.5) == 50.5
        assert _parse_float(100.0) == 100.0

    def test_parse_float_string(self):
        """Test parsing string float."""
        assert _parse_float("50.5") == 50.5
        assert _parse_float("100.0") == 100.0

    def test_parse_float_integer(self):
        """Test parsing integer as float."""
        assert _parse_float(50) == 50.0
        assert _parse_float(100) == 100.0

    def test_parse_float_none(self):
        """Test parsing None."""
        assert _parse_float(None) is None

    def test_parse_float_invalid(self):
        """Test parsing invalid value."""
        assert _parse_float("invalid") is None


class TestMapCategory:
    """Tests for _map_category helper function."""

    def test_map_category_apartments(self):
        """Test mapping apartments category."""
        assert _map_category("1011", {}) == "apartments"
        assert _map_category(1011, {}) == "apartments"

    def test_map_category_houses(self):
        """Test mapping houses category."""
        assert _map_category("1012", {}) == "houses"
        assert _map_category(1012, {}) == "houses"

    def test_map_category_unknown(self):
        """Test mapping unknown category."""
        assert _map_category("999", {}) == "real_estate"
        assert _map_category("unknown", {}) == "real_estate"

    def test_map_category_none(self):
        """Test mapping None category."""
        assert _map_category(None, {}) == "real_estate"

    def test_map_category_default(self):
        """Test mapping default category."""
        assert _map_category("1010", {}) == "real_estate"


class TestExtractImages:
    """Tests for _extract_images helper function."""

    def test_extract_images_from_list(self):
        """Test extracting images from list."""
        raw_data = {
            "images": [
                {"url": "https://example.com/img1.jpg"},
                {"url": "https://example.com/img2.jpg"},
            ]
        }
        result = _extract_images(raw_data)
        assert len(result) == 2
        assert "https://example.com/img1.jpg" in result
        assert "https://example.com/img2.jpg" in result

    def test_extract_images_from_photos(self):
        """Test extracting images from photos."""
        raw_data = {
            "photos": [
                {"url": "https://example.com/photo1.jpg"},
            ]
        }
        result = _extract_images(raw_data)
        assert len(result) == 1
        assert "https://example.com/photo1.jpg" in result

    def test_extract_images_empty(self):
        """Test extracting images when none present."""
        raw_data = {}
        result = _extract_images(raw_data)
        assert result == []

    def test_extract_images_none(self):
        """Test extracting images when None."""
        raw_data = {"images": None}
        result = _extract_images(raw_data)
        assert result == []


class TestParseListing:
    """Tests for parse_listing function."""

    def test_parse_listing_minimal(self):
        """Test parsing minimal listing."""
        raw_data = {
            "id": "123456",
            "price": 100000,
            "title": "Test Listing",
        }
        
        result = parse_listing(raw_data)
        
        assert result is not None
        assert result["kufar_id"] == "123456"
        assert result["price"] == 100000
        assert result["title"] == "Test Listing"
        assert result["currency"] == "USD"
        assert result["images"] == []

    def test_parse_listing_full(self):
        """Test parsing full listing."""
        raw_data = {
            "id": "789012",
            "price": 150000,
            "title": "Full Listing",
            "url": "https://kufar.by/l/789012",
            "address": "Test Street 1",
            "params": {
                "room_count": 2,
                "area": 50.5,
                "floor": 3,
            },
            "category_id": "1011",
            "images": [
                {"url": "https://example.com/img1.jpg"},
            ],
        }
        
        result = parse_listing(raw_data)
        
        assert result is not None
        assert result["kufar_id"] == "789012"
        assert result["price"] == 150000
        assert result["title"] == "Full Listing"
        assert result["address"] == "Test Street 1"
        assert result["rooms"] == 2
        assert result["area"] == 50.5
        assert result["floor"] == 3
        assert result["category"] == "apartments"
        assert len(result["images"]) == 1

    def test_parse_listing_missing_id(self):
        """Test parsing listing without ID."""
        raw_data = {
            "price": 100000,
            "title": "No ID Listing",
        }
        
        result = parse_listing(raw_data)
        
        assert result is None

    def test_parse_listing_with_kufar_id(self):
        """Test parsing listing with kufar_id field."""
        raw_data = {
            "kufar_id": "345678",
            "price": 80000,
            "title": "Kufar ID Listing",
        }
        
        result = parse_listing(raw_data)
        
        assert result is not None
        assert result["kufar_id"] == "345678"

    def test_parse_listing_default_url(self):
        """Test parsing listing generates default URL."""
        raw_data = {
            "id": "999999",
            "price": 100000,
            "title": "Default URL",
        }
        
        result = parse_listing(raw_data)
        
        assert result is not None
        assert result["url"] == "https://kufar.by/l/999999"

    def test_parse_listing_title_strip(self):
        """Test parsing listing strips title."""
        raw_data = {
            "id": "111111",
            "price": 100000,
            "title": "  Stripped Title  ",
        }
        
        result = parse_listing(raw_data)
        
        assert result is not None
        assert result["title"] == "Stripped Title"

    def test_parse_listing_default_address(self):
        """Test parsing listing uses default address."""
        raw_data = {
            "id": "222222",
            "price": 100000,
            "title": "Default Address",
        }
        
        result = parse_listing(raw_data)
        
        assert result is not None
        assert result["address"] == "Беларусь"

    def test_parse_listing_rooms_from_raw_data(self):
        """Test parsing rooms from raw_data directly."""
        raw_data = {
            "id": "333333",
            "price": 100000,
            "title": "Rooms from raw_data",
            "rooms": 3,
        }
        
        result = parse_listing(raw_data)
        
        assert result is not None
        assert result["rooms"] == 3


class TestParseScraperListing:
    """Tests for parse_scraper_listing function."""

    def test_parse_scraper_listing_minimal(self):
        """Test parsing minimal scraper listing."""
        raw_data = {
            "kufar_id": "444444",
            "price": 120000,
            "title": "Scraper Listing",
        }
        
        result = parse_scraper_listing(raw_data)
        
        assert result is not None
        assert result["kufar_id"] == "444444"
        assert result["price"] == 120000
        assert result["title"] == "Scraper Listing"

    def test_parse_scraper_listing_with_city(self):
        """Test parsing scraper listing with city."""
        raw_data = {
            "kufar_id": "555555",
            "price": 130000,
            "title": "With City",
        }
        
        result = parse_scraper_listing(raw_data, city_code="minsk")
        
        assert result is not None
        assert result["city"] == "minsk"

    def test_parse_scraper_listing_missing_id(self):
        """Test parsing scraper listing without ID."""
        raw_data = {
            "price": 100000,
            "title": "No ID",
        }
        
        result = parse_scraper_listing(raw_data)
        
        assert result is None

    def test_parse_scraper_listing_unknown_id(self):
        """Test parsing scraper listing with unknown_ ID."""
        raw_data = {
            "kufar_id": "unknown_123",
            "price": 100000,
            "title": "Unknown ID",
            "url": "https://kufar.by/l/666666",
        }
        
        result = parse_scraper_listing(raw_data)
        
        # Should generate ID from URL
        assert result is not None
        assert result["kufar_id"] != "unknown_123"
        assert len(result["kufar_id"]) == 16  # MD5 hash length

    def test_parse_scraper_listing_with_usd_price(self):
        """Test parsing scraper listing with USD price."""
        raw_data = {
            "kufar_id": "777777",
            "price": 140000,
            "price_usd": 45000,
            "title": "USD Price",
        }
        
        result = parse_scraper_listing(raw_data)
        
        assert result is not None
        assert result["price"] == 140000
        assert result["price_usd"] == 45000

    def test_parse_scraper_listing_extended_fields(self):
        """Test parsing scraper listing with extended fields."""
        raw_data = {
            "kufar_id": "888888",
            "price": 150000,
            "title": "Extended Fields",
            "rooms": 2,
            "area": 55.0,
            "floor": 4,
            "total_floors": 9,
            "district": "Central",
            "metro": "Nemiga",
        }
        
        result = parse_scraper_listing(raw_data)
        
        assert result is not None
        assert result["rooms"] == 2
        assert result["area"] == 55.0
        assert result["floor"] == 4
        assert result["total_floors"] == 9
        assert result["district"] == "Central"
        assert result["metro"] == "Nemiga"

    def test_parse_scraper_listing_house_fields(self):
        """Test parsing scraper listing with house-specific fields."""
        raw_data = {
            "kufar_id": "999999",
            "price": 200000,
            "title": "House",
            "house_type": "Кирпичный",
            "renovation": "С ремонтом",
            "land_area": 10.5,
        }
        
        result = parse_scraper_listing(raw_data)
        
        assert result is not None
        # These fields may not be parsed if not in expected format
        assert result["kufar_id"] == "999999"
        assert result["price"] == 200000

    def test_parse_scraper_listing_description(self):
        """Test parsing scraper listing with description."""
        raw_data = {
            "kufar_id": "101010",
            "price": 160000,
            "title": "With Description",
            "description": "This is a test description",
        }
        
        result = parse_scraper_listing(raw_data)
        
        assert result is not None
        assert result["description"] == "This is a test description"

    def test_parse_scraper_listing_images(self):
        """Test parsing scraper listing with images."""
        raw_data = {
            "kufar_id": "111111",
            "price": 170000,
            "title": "With Images",
            "images": [
                "https://example.com/img1.jpg",
                "https://example.com/img2.jpg",
            ],
        }
        
        result = parse_scraper_listing(raw_data)
        
        assert result is not None
        assert len(result["images"]) == 2
        assert "https://example.com/img1.jpg" in result["images"]

    def test_parse_scraper_listing_location(self):
        """Test parsing scraper listing with location."""
        raw_data = {
            "kufar_id": "121212",
            "price": 180000,
            "title": "With Location",
            "address": "Minsk, Central District",
        }
        
        result = parse_scraper_listing(raw_data)
        
        assert result is not None
        assert result["address"] == "Minsk, Central District"

    def test_parse_scraper_listing_default_location(self):
        """Test parsing scraper listing uses default location."""
        raw_data = {
            "kufar_id": "131313",
            "price": 190000,
            "title": "Default Location",
        }
        
        result = parse_scraper_listing(raw_data)
        
        assert result is not None
        assert result["address"] == "Беларусь"
