from datetime import date, datetime, timedelta
from decimal import Decimal

DATE_FORMAT = '%Y-%m-%d'
goods = {}

def add(items, title, amount, expiration_date=None):
    if expiration_date is not None:
        expiration_date = datetime.strptime(expiration_date, DATE_FORMAT).date()
    amount = Decimal(str(amount))
    items.setdefault(title, []).append({
        'amount': amount,
        'expiration_date': expiration_date,
    })


def add_by_note(items, note):
    parts = note.split()
    if len(parts) < 2:
        raise ValueError('Заметка должна содержать название и количество.')

    expiration_date = None
    try:
        datetime.strptime(parts[-1], DATE_FORMAT)
    except ValueError:
        pass
    else:
        expiration_date = parts.pop()

    if len(parts) < 2:
        raise ValueError('Заметка должна содержать название и количество.')
    amount = Decimal(parts.pop())
    title = ' '.join(parts)
    add(items, title, amount, expiration_date)


def find(items, needle):
    needle = needle.lower()
    return [title for title in items if needle in title.lower()]


def get_amount(items, needle):
    product_amount = Decimal('0')
    for title in find(items, needle):
        for part in items[title]:
            product_amount += part['amount']
    return product_amount


def get_expired(items, in_advance_days=0):
    expiration_threshold = date.today() + timedelta(days=in_advance_days)
    result = []
    for title, parts in items.items():
        amount = Decimal('0')
        for part in parts:
            expiration_date = part['expiration_date']
            if expiration_date is not None and expiration_date <= expiration_threshold:
                amount += part['amount']
        if amount > 0:
            result.append((title, amount))
    return result


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
