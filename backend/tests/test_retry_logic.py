"""Tests for retry logic in KufarJSONScraper."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from app.scraper.kufar_json_scraper import KufarJSONScraper


class TestRetryConfiguration:
    """Test retry configuration and initialization."""

    def test_default_retry_config(self):
        """Test default retry configuration."""
        scraper = KufarJSONScraper()
        
        assert scraper.timeout == 30.0
        assert scraper.max_retries == 3
        assert scraper.base_delay == 1.0
        assert scraper.max_delay == 60.0
        assert scraper.exponential_base == 2.0

    def test_custom_retry_config(self):
        """Test custom retry configuration."""
        scraper = KufarJSONScraper(
            timeout=60.0,
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
        )
        
        assert scraper.timeout == 60.0
        assert scraper.max_retries == 5
        assert scraper.base_delay == 2.0
        assert scraper.max_delay == 120.0
        assert scraper.exponential_base == 3.0


class TestCalculateDelay:
    """Test exponential backoff delay calculation."""

    def test_delay_increases_exponentially(self):
        """Test that delay increases exponentially."""
        scraper = KufarJSONScraper(base_delay=1.0, exponential_base=2.0, max_delay=60.0)
        
        # Delays should approximately double each attempt
        delay_0 = scraper._calculate_delay(0)  # ~1s
        delay_1 = scraper._calculate_delay(1)  # ~2s
        delay_2 = scraper._calculate_delay(2)  # ~4s
        
        assert delay_0 < delay_1 < delay_2

    def test_delay_respects_max_delay(self):
        """Test that delay doesn't exceed max_delay."""
        scraper = KufarJSONScraper(base_delay=1.0, max_delay=5.0)
        
        # Even with high attempt number, should not exceed max_delay
        delay = scraper._calculate_delay(10)  # Would be 1024s without cap
        assert delay <= 5.0

    def test_delay_has_jitter(self):
        """Test that jitter is added to prevent thundering herd."""
        scraper = KufarJSONScraper(base_delay=1.0)
        
        # Multiple calls should have slight variations due to jitter
        delays = [scraper._calculate_delay(0) for _ in range(10)]
        # At least some variation should exist
        assert len(set(delays)) > 1


class TestRetryableStatus:
    """Test retryable status code detection."""

    def test_retryable_status_codes(self):
        """Test that retryable status codes are detected."""
        scraper = KufarJSONScraper()
        
        retryable_codes = [408, 425, 429, 500, 502, 503, 504]
        for code in retryable_codes:
            assert scraper._is_retryable_status(code) is True

    def test_non_retryable_status_codes(self):
        """Test that non-retryable status codes are not retried."""
        scraper = KufarJSONScraper()
        
        non_retryable_codes = [200, 201, 301, 302, 400, 401, 403, 404, 405]
        for code in non_retryable_codes:
            assert scraper._is_retryable_status(code) is False


class TestFetchWithRetry:
    """Test fetch with retry logic."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """Test successful fetch on first attempt."""
        scraper = KufarJSONScraper()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>content</html>"
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        
        success, content, status = await scraper._fetch_with_retry(
            "http://test.com", mock_client
        )
        
        assert success is True
        assert content == "<html>content</html>"
        assert status == 200
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Test retry on timeout exception."""
        scraper = KufarJSONScraper(max_retries=3, base_delay=0.01)
        
        mock_client = AsyncMock()
        # Fail twice, succeed on third attempt
        mock_client.get = AsyncMock(
            side_effect=[
                httpx.TimeoutException("Timeout"),
                httpx.TimeoutException("Timeout"),
                MagicMock(status_code=200, text="success"),
            ]
        )
        
        success, content, status = await scraper._fetch_with_retry(
            "http://test.com", mock_client
        )
        
        assert success is True
        assert content == "success"
        assert status == 200
        assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_on_503_status(self):
        """Test retry on 503 Service Unavailable."""
        scraper = KufarJSONScraper(max_retries=3, base_delay=0.01)
        
        mock_response_503 = MagicMock()
        mock_response_503.status_code = 503
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.text = "success"
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[mock_response_503, mock_response_503, mock_response_200]
        )
        
        success, content, status = await scraper._fetch_with_retry(
            "http://test.com", mock_client
        )
        
        assert success is True
        assert content == "success"
        assert status == 200
        assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self):
        """Test failure when all retries are exhausted."""
        scraper = KufarJSONScraper(max_retries=3, base_delay=0.01)
        
        mock_client = AsyncMock()
        # Always fail
        mock_client.get = AsyncMock(
            side_effect=[httpx.TimeoutException("Timeout")] * 3
        )
        
        success, content, status = await scraper._fetch_with_retry(
            "http://test.com", mock_client
        )
        
        assert success is False
        assert content is None
        assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_non_retryable_status_does_not_retry(self):
        """Test that non-retryable status codes don't trigger retries."""
        scraper = KufarJSONScraper(max_retries=3)
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        
        success, content, status = await scraper._fetch_with_retry(
            "http://test.com", mock_client
        )
        
        assert success is False
        assert status == 404
        mock_client.get.assert_called_once()  # Only one call, no retries


class TestScrapePageWithRetry:
    """Test scrape_page method with retry logic."""

    @pytest.mark.asyncio
    async def test_scrape_page_success(self):
        """Test successful scrape_page."""
        scraper = KufarJSONScraper()
        
        # Mock the entire HTTP client context manager
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <script id="__NEXT_DATA__" type="application/json">
        {"props":{"initialState":{"listing":{"ads":[{"ad_id":"123","price_byn":100000,"ad_parameters":[]}]}}}}
        </script>
        </html>
        """
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            
            mock_client_class.return_value = mock_context_manager
            
            listings = await scraper.scrape_page("http://test.com")
            
            assert len(listings) == 1
            assert listings[0]["kufar_id"] == "123"

    @pytest.mark.asyncio
    async def test_scrape_page_returns_empty_on_failure(self):
        """Test scrape_page returns empty list on failure."""
        scraper = KufarJSONScraper(max_retries=2, base_delay=0.01)
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            
            mock_client_class.return_value = mock_context_manager
            
            listings = await scraper.scrape_page("http://test.com")
            
            assert listings == []


class TestRetryableExceptions:
    """Test that correct exceptions trigger retries."""

    def test_retryable_exceptions_tuple(self):
        """Test that retryable exceptions are properly defined."""
        scraper = KufarJSONScraper()
        
        assert httpx.TimeoutException in scraper.RETRYABLE_EXCEPTIONS
        assert httpx.ConnectError in scraper.RETRYABLE_EXCEPTIONS
        assert httpx.ReadTimeout in scraper.RETRYABLE_EXCEPTIONS
        assert httpx.WriteTimeout in scraper.RETRYABLE_EXCEPTIONS
        assert httpx.RemoteProtocolError in scraper.RETRYABLE_EXCEPTIONS

    @pytest.mark.asyncio
    async def test_connect_error_triggers_retry(self):
        """Test that ConnectError triggers retry."""
        scraper = KufarJSONScraper(max_retries=2, base_delay=0.01)
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[
                httpx.ConnectError("Connection failed"),
                MagicMock(status_code=200, text="success"),
            ]
        )
        
        success, content, status = await scraper._fetch_with_retry(
            "http://test.com", mock_client
        )
        
        assert success is True
        assert content == "success"
        assert mock_client.get.call_count == 2
