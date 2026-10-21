"""Проверки контрактов функций и примеров из задания Практикума."""

import copy
from datetime import date
from decimal import Decimal, InvalidOperation
import unittest
from unittest.mock import patch

import main as refrigerator


class AddTests(unittest.TestCase):
    def test_add_dated_batch(self):
        items = {}
        result = refrigerator.add(items, 'Яйца', Decimal('10'), '2023-9-30')
        self.assertIsNone(result)
        self.assertEqual(items, {'Яйца': [
            {'amount': Decimal('10'), 'expiration_date': date(2023, 9, 30)},
        ]})

    def test_batches_are_kept_separately(self):
        items = {}
        refrigerator.add(items, 'Яйца', Decimal('10'), '2023-09-30')
        refrigerator.add(items, 'Яйца', Decimal('3'), '2023-10-15')
        self.assertEqual(len(items['Яйца']), 2)
        self.assertEqual(items['Яйца'][1]['expiration_date'], date(2023, 10, 15))

    def test_no_expiration(self):
        items = {}
        refrigerator.add(items, 'Вода', Decimal('2.5'))
        self.assertEqual(items['Вода'], [
            {'amount': Decimal('2.5'), 'expiration_date': None},
        ])

    def test_quantity_conversion(self):
        for amount in (2, '2', Decimal('2'), 2.0):
            with self.subTest(amount=amount):
                items = {}
                refrigerator.add(items, 'Продукт', amount)
                self.assertIsInstance(items['Продукт'][0]['amount'], Decimal)
                self.assertEqual(items['Продукт'][0]['amount'], Decimal('2'))

    def test_invalid_date_does_not_modify_items(self):
        items = {}
        with self.assertRaises(ValueError):
            refrigerator.add(items, 'Яйца', Decimal('1'), '2023-02-29')
        self.assertEqual(items, {})

    def test_invalid_quantity_does_not_modify_items(self):
        items = {}
        with self.assertRaises(InvalidOperation):
            refrigerator.add(items, 'Яйца', 'много')
        self.assertEqual(items, {})

    def test_leap_day_and_far_future(self):
        items = {}
        refrigerator.add(items, 'Яйца', Decimal('1'), '2024-02-29')
        refrigerator.add(items, 'Яйца', Decimal('1'), '2126-10-21')
        self.assertEqual(items['Яйца'][1]['expiration_date'], date(2126, 10, 21))


class NoteTests(unittest.TestCase):
    def test_course_example(self):
        items = {}
        result = refrigerator.add_by_note(items, 'Яйца гусиные 4 2023-07-15')
        self.assertIsNone(result)
        self.assertEqual(items, {'Яйца гусиные': [
            {'amount': Decimal('4'), 'expiration_date': date(2023, 7, 15)},
        ]})

    def test_fraction_without_date(self):
        items = {}
        refrigerator.add_by_note(items, 'Вода питьевая 0.1')
        self.assertEqual(items['Вода питьевая'][0]['amount'], Decimal('0.1'))
        self.assertIsNone(items['Вода питьевая'][0]['expiration_date'])

    def test_non_padded_date(self):
        items = {}
        refrigerator.add_by_note(items, 'Яйца 3 2023-9-30')
        self.assertEqual(items['Яйца'][0]['expiration_date'], date(2023, 9, 30))

    def test_whitespace_and_repeated_product(self):
        items = {}
        refrigerator.add_by_note(items, '  Вода   питьевая\t1.5  ')
        refrigerator.add_by_note(items, 'Вода питьевая 2')
        self.assertEqual(refrigerator.get_amount(items, 'Вода'), Decimal('3.5'))

    def test_numbers_in_title(self):
        items = {}
        refrigerator.add_by_note(items, 'Молоко 3.2 процента 1 2026-10-22')
        self.assertIn('Молоко 3.2 процента', items)

    def test_malformed_notes(self):
        for note in ('', 'Яйца', '3 2023-09-30', 'Яйца много',
                     'Яйца 3 2023-02-30'):
            with self.subTest(note=note):
                items = {}
                with self.assertRaises((ValueError, InvalidOperation)):
                    refrigerator.add_by_note(items, note)
                self.assertEqual(items, {})


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.items = {}
        refrigerator.add_by_note(self.items, 'Яйца 1')
        refrigerator.add_by_note(self.items, 'Яйца гусиные 4')
        refrigerator.add_by_note(self.items, 'Морковь 2 2023-8-1')
        refrigerator.add_by_note(self.items, 'Морковь 3 2023-8-6')

    def test_case_insensitive_search(self):
        self.assertEqual(refrigerator.find(self.items, 'яЙц'),
                         ['Яйца', 'Яйца гусиные'])

    def test_no_match(self):
        self.assertEqual(refrigerator.find(self.items, 'Сыр'), [])

    def test_empty_search(self):
        self.assertEqual(refrigerator.find(self.items, ''), list(self.items))

    def test_amount_all_matching_titles(self):
        result = refrigerator.get_amount(self.items, 'ЯЙЦ')
        self.assertIsInstance(result, Decimal)
        self.assertEqual(result, Decimal('5'))

    def test_amount_multiple_batches(self):
        self.assertEqual(refrigerator.get_amount(self.items, 'морковь'), Decimal('5'))

    def test_missing_amount_is_decimal_zero(self):
        result = refrigerator.get_amount(self.items, 'Сыр')
        self.assertIsInstance(result, Decimal)
        self.assertEqual(result, Decimal('0'))

    def test_exact_decimal_sum(self):
        items = {}
        refrigerator.add_by_note(items, 'Вода 0.1')
        refrigerator.add_by_note(items, 'Вода 0.2')
        self.assertEqual(refrigerator.get_amount(items, 'вода'), Decimal('0.3'))


class ExpirationTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2023, 12, 10)
        self.date_patch = patch('main.date')
        mocked_date = self.date_patch.start()
        self.addCleanup(self.date_patch.stop)
        mocked_date.today.return_value = self.today
        self.items = {}
        for note in ('Хлеб 1', 'Хлеб 1 2023-12-9', 'Яйца 2 2023-12-12',
                     'Яйца 3 2023-12-11', 'Вода 100'):
            refrigerator.add_by_note(self.items, note)

    def test_course_examples(self):
        for days, expected in (
            (0, [('Хлеб', Decimal('1'))]),
            (1, [('Хлеб', Decimal('1')), ('Яйца', Decimal('3'))]),
            (2, [('Хлеб', Decimal('1')), ('Яйца', Decimal('5'))]),
        ):
            with self.subTest(days=days):
                self.assertEqual(refrigerator.get_expired(self.items, days), expected)

    def test_today_is_included(self):
        refrigerator.add(self.items, 'Молоко', Decimal('0.5'), '2023-12-10')
        self.assertEqual(refrigerator.get_expired(self.items),
                         [('Хлеб', Decimal('1')), ('Молоко', Decimal('0.5'))])

    def test_default_horizon(self):
        self.assertEqual(refrigerator.get_expired(self.items),
                         refrigerator.get_expired(self.items, 0))

    def test_no_expiration_is_never_included(self):
        self.assertNotIn('Вода', dict(refrigerator.get_expired(self.items, 36500)))

    def test_zero_amount_is_omitted(self):
        refrigerator.add(self.items, 'Сыр', Decimal('0'), '2023-01-01')
        self.assertNotIn('Сыр', dict(refrigerator.get_expired(self.items)))

    def test_year_boundary(self):
        days = (date(2024, 1, 1) - self.today).days
        refrigerator.add(self.items, 'Сыр', Decimal('1'), '2024-01-01')
        self.assertIn(('Сыр', Decimal('1')), refrigerator.get_expired(self.items, days))
        self.assertNotIn('Сыр', dict(refrigerator.get_expired(self.items, days - 1)))

    def test_queries_do_not_change_storage(self):
        original = copy.deepcopy(self.items)
        refrigerator.find(self.items, '')
        refrigerator.get_amount(self.items, '')
        refrigerator.get_expired(self.items, 2)
        self.assertEqual(self.items, original)

    def test_empty_storage(self):
        self.assertEqual(refrigerator.find({}, 'яйц'), [])
        self.assertEqual(refrigerator.get_amount({}, 'яйц'), Decimal('0'))
        self.assertEqual(refrigerator.get_expired({}), [])


if __name__ == '__main__':
    unittest.main()
