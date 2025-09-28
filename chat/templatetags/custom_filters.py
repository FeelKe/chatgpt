# custom_filters.py

from django import template
import logging

logger = logging.getLogger(__name__)

# Создаем экземпляр библиотеки шаблонов
register = template.Library()

@register.filter
def escape_special_chars(value):
    logger.debug(f"Обработка сообщения: {value}")  # Логируем входящие данные
    return value.replace('#', '&#35;').replace('`', '&#126;')
