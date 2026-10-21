"""Запуск примера без интерактивного ввода и изменения main.goods."""

from datetime import date
from decimal import Decimal

from main import add, add_by_note, find, get_amount, get_expired


def main():
    items = {}
    add(items, 'Яйца', Decimal('10'), date.today().isoformat())
    add_by_note(items, 'Яйца гусиные 4')
    add_by_note(items, 'Вода 1.5')
    print('Найдены продукты:', find(items, 'яйц'))
    print('Общее количество яиц:', get_amount(items, 'яйц'))
    print('Срок истёк или истекает сегодня:', get_expired(items))


if __name__ == '__main__':
    main()
