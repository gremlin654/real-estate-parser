"""
WebSocket endpoint для real-time прогресса сканирования.
"""
import asyncio
import json
from typing import Set, Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Менеджер WebSocket подключений для рассылки прогресса сканирования."""

    def __init__(self):
        # Активные WebSocket подключения
        self.active_connections: Set[WebSocket] = set()
        # Блокировка для потокобезопасной работы
        self._lock = asyncio.Lock()
        # Текущий прогресс сканирования (для отправки новым подключениям)
        self.current_progress: Dict = {
            "is_scanning": False,
            "city": None,
            "city_name": None,
            "stage": "idle",
            "pages_scraped": 0,
            "listings_fetched": 0,
            "listings_processed": 0,
            "elapsed_seconds": 0,
            "is_stable": True,
        }
        # Список активных сканирований по городам
        self.scanning_cities: List[Dict] = []

    async def connect(self, websocket: WebSocket):
        """Принять новое WebSocket подключение."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
            logger.debug(f"WebSocket connected. Total connections: {len(self.active_connections)}")

            # Отправить текущий прогресс новому подключению
            await self._send_progress(websocket, self._get_current_message())

    async def disconnect(self, websocket: WebSocket):
        """Закрыть WebSocket подключение."""
        async with self._lock:
            self.active_connections.discard(websocket)
            logger.debug(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    def _get_current_message(self) -> Dict:
        """Сформировать текущее сообщение с прогрессом."""
        return {
            "scanning_cities": self.scanning_cities,
        }

    async def broadcast_progress(self, progress: Dict):
        """Отправить прогресс всем подключенным клиентам.
        
        Args:
            progress: Прогресс для конкретного города из scheduler.scan_progress
        """
        # Сохранить текущий прогресс для обратой совместимости
        self.current_progress = progress

        # Отправить всем подключениям список всех активных сканирований
        async with self._lock:
            disconnected = set()
            message = self._get_current_message()
            
            for connection in self.active_connections:
                try:
                    await self._send_progress(connection, message)
                except Exception as e:
                    logger.warning(f"Failed to send progress to WebSocket: {e}")
                    disconnected.add(connection)

            # Удалить отключенные подключения
            for connection in disconnected:
                self.active_connections.discard(connection)

    async def update_scanning_cities(self, scanning_cities: List[Dict]):
        """Обновить список активных сканирований.
        
        Args:
            scanning_cities: Список сканируемых городов из scheduler._get_scanning_cities()
        """
        async with self._lock:
            self.scanning_cities = scanning_cities

    async def _send_progress(self, websocket: WebSocket, progress: Dict):
        """Отправить прогресс конкретному подключению."""
        await websocket.send_json(progress)


# Глобальный менеджер подключений
manager = ConnectionManager()


@router.websocket("/ws/scan/progress")
async def scan_progress_websocket(websocket: WebSocket):
    """
    WebSocket endpoint для получения real-time прогресса сканирования.
    
    Клиент получает обновления при:
    - Изменении стадии сканирования
    - Обновлении количества обработанных страниц/объявлений
    - Завершении сканирования
    
    Пример подключения:
        const ws = new WebSocket('ws://localhost:8000/ws/scan/progress')
        ws.onmessage = (event) => {
            const progress = JSON.parse(event.data)
            console.log(progress)
        }
    """
    await manager.connect(websocket)
    try:
        # Держать соединение открытым, пока клиент не отключится
        while True:
            # Ждем сообщения от клиента (например, ping для keepalive)
            try:
                await websocket.receive_text()
                # Можно добавить обработку команд от клиента
            except WebSocketDisconnect:
                break
            except Exception:
                # Игнорировать ошибки получения (клиент может только слушать)
                await asyncio.sleep(1)
    finally:
        await manager.disconnect(websocket)


def get_scan_manager() -> ConnectionManager:
    """Получить менеджер WebSocket подключений."""
    return manager
