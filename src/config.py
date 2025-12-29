"""
Конфигурация для Tinkoff Invest API.
Будет дополняться в процессе разработки.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class TinkoffConfig:
    """Базовый класс конфигурации Tinkoff Invest API"""
    
    @property
    def api_token(self) -> str:
        """Токен API Tinkoff Invest"""
        token = os.getenv('TINKOFF_API_TOKEN')
        if not token:
            raise ValueError(
                "TINKOFF_API_TOKEN не найден в переменных окружения. "
                "Добавьте его в файл .env"
            )
        return token
    
    @property
    def use_sandbox(self) -> bool:
        """Использовать песочницу для тестирования"""
        return os.getenv('USE_SANDBOX', 'true').lower() == 'true'
    
    @property
    def app_name(self) -> str:
        """Имя приложения для идентификации в API"""
        return os.getenv('APP_NAME', 'tinvest-bot')

# Создаем глобальный экземпляр конфигурации
config = TinkoffConfig()
