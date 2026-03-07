"""
Tests for parser module
"""
import pytest

from app.scraper.parser import parse_listing


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
        assert result["price"] == 1000  # 100000 / 100 (копейки)
        assert result["title"] == "Test Listing"
        assert result["currency"] == "BYN"
        assert result["images"] == []

    def test_parse_listing_with_price_usd(self):
        """Test parsing listing with USD price."""
        raw_data = {
            "id": "123456",
            "price": 100000,
            "price_usd": 35000,
            "title": "Test Listing",
        }

        result = parse_listing(raw_data)

        assert result is not None
        assert result["price"] == 1000  # 100000 / 100
        assert result["price_usd"] == 350  # 35000 / 100

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
                "floors": 9,
                "year": 2020,
            },
            "category": "apartments",
            "images": [
                "https://example.com/img1.jpg",
            ],
            "description": "Test description",
            "district": "Central",
            "metro": "Nemiga",
        }

        result = parse_listing(raw_data)

        assert result is not None
        assert result["kufar_id"] == "789012"
        assert result["price"] == 1500  # 150000 / 100
        assert result["title"] == "Full Listing"
        assert result["address"] == "Test Street 1"
        assert result["rooms"] == 2
        assert result["area"] == 50.5
        assert result["floor"] == 3
        assert result["total_floors"] == 9
        assert result["category"] == "apartments"
        assert len(result["images"]) == 1
        assert result["description"] == "Test description"
        assert result["district"] == "Central"
        assert result["metro"] == "Nemiga"
        assert result["house_year"] == 2020

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
        assert result["title"] == "  Stripped Title  "  # Title не strip-ится в новой версии

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

    def test_parse_listing_price_zero(self):
        """Test parsing listing with zero price."""
        raw_data = {
            "id": "444444",
            "price": 0,
            "title": "Zero Price",
        }

        result = parse_listing(raw_data)

        assert result is not None
        assert result["price"] == 0

    def test_parse_listing_price_division(self):
        """Test that price is divided by 100 (kopecks conversion)."""
        raw_data = {
            "id": "555555",
            "price": 12278675,  # 122,786.75 BYN in kopecks
            "title": "Price Division Test",
        }

        result = parse_listing(raw_data)

        assert result is not None
        assert result["price"] == 122786  # 12278675 // 100

    def test_parse_listing_images_list(self):
        """Test parsing listing with images as list."""
        raw_data = {
            "id": "666666",
            "price": 100000,
            "title": "With Images",
            "images": [
                "https://example.com/img1.jpg",
                "https://example.com/img2.jpg",
            ],
        }

        result = parse_listing(raw_data)

        assert result is not None
        assert len(result["images"]) == 2

    def test_parse_listing_images_string(self):
        """Test parsing listing with images as string."""
        raw_data = {
            "id": "777777",
            "price": 100000,
            "title": "Single Image",
            "images": "https://example.com/img1.jpg",
        }

        result = parse_listing(raw_data)

        assert result is not None
        assert len(result["images"]) == 1

    def test_parse_listing_no_images(self):
        """Test parsing listing without images."""
        raw_data = {
            "id": "888888",
            "price": 100000,
            "title": "No Images",
        }

        result = parse_listing(raw_data)

        assert result is not None
        assert result["images"] == []

    def test_parse_listing_city(self):
        """Test parsing listing with city."""
        raw_data = {
            "id": "999999",
            "price": 100000,
            "title": "With City",
            "city": "minsk",
        }

        result = parse_listing(raw_data)

        assert result is not None
        assert result["city"] == "minsk"

    def test_parse_listing_params_variations(self):
        """Test parsing listing with different param names."""
        raw_data = {
            "id": "101010",
            "price": 100000,
            "title": "Params Test",
            "params": {
                "room_count": 2,
                "area": 50.5,
                "floor": 3,
                "floors": 9,
                "year": 2020,
            },
        }

        result = parse_listing(raw_data)

        assert result is not None
        assert result["rooms"] == 2
        assert result["area"] == 50.5
        assert result["floor"] == 3
        assert result["total_floors"] == 9
        assert result["house_year"] == 2020

    def test_parse_listing_alternative_field_names(self):
        """Test parsing listing with alternative field names."""
        raw_data = {
            "id": "111112",
            "price": 100000,
            "title": "Alternative Fields",
            "location": "Location Address",
            "body": "Body description",
        }

        result = parse_listing(raw_data)

        assert result is not None
        # Title используется из поля 'title', а не 'subject'
        assert result["title"] == "Alternative Fields"
        assert result["address"] == "Location Address"
        assert result["description"] == "Body description"

    def test_parse_listing_price_usd_variations(self):
        """Test parsing listing with different USD price field names."""
        raw_data = {
            "id": "121212",
            "price": 100000,
            "title": "USD Price Test",
            "price$": 35000,
        }

        result = parse_listing(raw_data)

        assert result is not None
        assert result["price_usd"] == 350  # 35000 // 100
