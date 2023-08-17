import unittest

from ui_utils import BarcodeParser


class TestBarcodeParser(unittest.TestCase):
    def setUp(self):
        self.sut = BarcodeParser

    def test_must_return_ean13_result(self):
        expect = {'BARCODE': '2000000058177', 'SCHEME': 'EAN13', 'GTIN': '2000000058177'}
        actual = self.sut(barcode='2000000058177').parse()

        self.assertEqual(expect, actual)

    def test_must_return_unknown_result(self):
        expect = {'SCHEME': 'UNKNOWN'}
        actual = self.sut(barcode='').parse()

        self.assertEqual(expect, actual)

        expect = {'BARCODE': 'fdg54454g', 'GTIN': 'fdg54454g', 'SCHEME': 'UNKNOWN'}
        actual = self.sut(barcode='fdg54454g').parse()

        self.assertEqual(expect, actual)

    def test_must_return_gs1_result(self):
        expect = {
            'BARCODE': '04012922851574EsmtWOcADvofO3q',
            'SCHEME': 'GS1',
            'CHECK': 'fO3q',
            'MRC': 'ADvo',
            'SERIAL': 'EsmtWOc',
            'GTIN': '04012922851574'
        }
        actual = self.sut(barcode='04012922851574EsmtWOcADvofO3q').parse()

        self.assertEqual(expect, actual)



