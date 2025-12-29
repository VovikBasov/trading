import asyncio
import sys
import os

# Добавляем корень проекта в путь Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def run_stream():
    """Основная функция запуска."""
    from src.api.market_stream import main as stream_main
    await stream_main()

if __name__ == "__main__":
    # Проверка конфигурации
    from src.config import config
    print("=== Конфигурация бота ===")
    print(f"Токен: {'*' * min(10, len(config.api_token))}...")
    print(f"Режим: {'ПРОДАКШЕН (боевой)' if not config.use_sandbox else 'ПЕСОЧНИЦА (тестовый)'}")
    print(f"Имя приложения: {config.app_name}")
    print("=" * 30)
    print("Запуск стрима... (Ctrl+C для остановки)")
    
    # Запуск стрима
    asyncio.run(run_stream())
