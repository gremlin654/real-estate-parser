"""
Тест WebSocket endpoint для прогресса сканирования.
Запуск: python test_ws.py
"""
import asyncio
import websockets
import json


async def test_websocket():
    """Подключиться к WebSocket и получать обновления прогресса."""
    uri = "ws://localhost:8000/ws/scan/progress"
    
    print(f"Подключение к {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Подключено к WebSocket")
            
            # Ждем сообщения в течение 30 секунд
            for i in range(30):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    print(f"📊 Прогресс: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except asyncio.TimeoutError:
                    print("⏳ Ожидание обновлений...")
            
            print("Тест завершен")
            
    except websockets.exceptions.ConnectionClosed:
        print("❌ Соединение закрыто")
    except ConnectionRefusedError:
        print("❌ Не удалось подключиться. Убедитесь, что backend запущен на порту 8000")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
