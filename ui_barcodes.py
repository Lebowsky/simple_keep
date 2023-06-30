# Модуль парсит штрихкод или датаматрикс на составляющие 11

import re
from datetime import datetime


def parse_barcode(barcode):
    #Отладочное
    return {'SCHEME': 'EAN13', 'BARCODE': barcode, 'GTIN': barcode, 'SERIAL': ''}

    if barcode:
        # Простой EAN13
        if not re.fullmatch(r'\d{13}', barcode) is None and re.fullmatch(r'\d{13}', barcode).string == barcode:

            res = {'SCHEME': 'EAN13', 'BARCODE': barcode, 'GTIN': barcode, 'SERIAL': ''}

        elif len(barcode) == 29:  # Это датаматрикс Табак, Пачка
            # res = parse_tobacco(barcode)
            res = {'SCHEME': 'GS1', 'GTIN': barcode[0:14], 'SERIAL': barcode[14:21], 'MRC': barcode[21:25],
                   'CHECK': barcode[25:29]}

        elif chr(29) in barcode:  # Datamatrix

            res = datamatrix(barcode)
            res['FullCode'] = barcode
        elif '<GS>' in barcode:
            res = datamatrix(barcode)
            res['FullCode'] = barcode
        else:  # Неизвестный тип кода
            res = {'SCHEME': 'UNKNOWN', 'BARCODE': barcode, 'GTIN': barcode, 'SERIAL': ''}

        return res
    else:
        return {'SCHEME': 'UNKNOWN', 'BARCODE': barcode, 'GTIN': '', 'SERIAL': '', 'ERROR': 'Empty barcode'}


def datamatrix(barcode: str) -> dict:
    """
    The function takes barcode string and return parsed objects in a `dict`.
    Optionally user can pass bool value to validate the barcode
    Parameters:
        barcode: string type. This is the barcode string with the <GS> seperators.

    Returns:
        dict: Returns dictionary object with SCHEME, PPN, GTIN, EXPIRY, BATCH, SERIAL & NHRN as keys for valid requests
        or relevant error strings.
    """

    if barcode[
       :3] == "]d2":  # Most barcode scanners prepend ']d2' identifier for the GS1 datamatrix. This section removes the identifier.
        barcode = barcode[3:]
        result = gs1_gtin(barcode)

    elif barcode[:2] in ['01', '21', '17', '10', '71']:
        result = gs1_gtin(barcode)

    elif barcode[0] == chr(29):  # Short GS1 barcode
        result = gs1_gtin(barcode)

    elif barcode[:6] == ('[)>' + chr(30) + '06') or ('[)>' + chr(30) + '05'):  # MACRO 06 or MACRO 05
        barcode = barcode[7:]  # Removes the leading ASCII seperator after the scheme identifier.
        result = ifa_ppn(barcode)

    else:
        result = {'ERROR': 'INVALID FORMAT', 'BARCODE': barcode}

    return result


def gtin_check(gtin: str):
    reverse_gtin = gtin[-2::-1]  # Reversing the string without the check-digit
    digit_multipler3 = []
    digit_multipler1 = []

    for i, l in enumerate(reverse_gtin):
        if i % 2 == 0:
            digit_multipler3.append(int(l))
        else:
            digit_multipler1.append(int(l))

    digit_sum = (sum(digit_multipler3) * 3) + sum(digit_multipler1)
    nearest_ten = round(digit_sum / 10) * 10
    check_sum_digit = nearest_ten - digit_sum
    if check_sum_digit < 0:
        check_sum_digit = 10 + check_sum_digit
    return check_sum_digit == int(gtin[-1])


sresult = {'SCHEME': 'GS1'}


def gs1_gtin(barcode: str) -> dict:
    if chr(29) in barcode:

        while barcode:
            if barcode[:2] == '01':
                sresult['GTIN'] = barcode[2:16]
                if len(barcode) > 16:
                    barcode = barcode[16:]
                else:
                    barcode = None

            elif barcode[:3] == chr(29) + '01':
                sresult['GTIN'] = barcode[3:17]
                if len(barcode) > 17:
                    barcode = barcode[17:]
                else:
                    barcode = None
            elif barcode[:2] == '17':
                sresult['EXPIRY'] = barcode[2:8]
                if len(barcode) > 8:
                    barcode = barcode[8:]
                else:
                    barcode = None

            elif barcode[:2] == '10':
                if chr(29) in barcode:
                    index = barcode.index(chr(29))
                    sresult['BATCH'] = barcode[2:index]
                    barcode = barcode[index + 1:]
                else:
                    sresult['BATCH'] = barcode[2:]
                    barcode = None

            elif barcode[:2] == '21':
                if chr(29) in barcode:
                    index = barcode.index(chr(29))
                    sresult['SERIAL'] = barcode[2:index]
                    barcode = barcode[index + 1:]
                else:
                    sresult['SERIAL'] = barcode[2:]
                    barcode = None

            elif barcode[:2] == '91':
                if chr(29) in barcode:
                    index = barcode.index(chr(29))
                    sresult['NHRN'] = barcode[2:index]
                    barcode = barcode[index + 1:]
                else:
                    sresult['NHRN'] = barcode[2:6]
                    barcode = None

            elif barcode[:2] == '93':  # Молочка, вода
                sresult['CHECK'] = barcode[2:6]
                barcode = barcode[7:]

            elif barcode[:2] == '92':  # Далее следует код проверки, 44 символа
                # if len(barcode[2:])==44:
                sresult['CHECK'] = barcode[2:]
                barcode = None
            elif barcode[:4] == '8005':  # Табак, Блок
                sresult['NHRN'] = barcode[5:11]
                barcode = barcode[11:]
            elif barcode[:4] == '3103':  # Молочка с Весом

                sresult['WEIGHT'] = barcode[4:]
                barcode = None

            else:
                return {'ERROR': 'INVALID BARCODE', 'BARCODE': sresult}
    else:
        sresult['ERROR'] = 'No GS Separator'
        return sresult

    # if ('GTIN' , 'BATCH' , 'EXPIRY' , 'SERIAL') in result.keys():
    #     if gtin_check(result['GTIN']) == False and expiry_date_check(result['EXPIRY']) == False:
    #         return {'ERROR': 'INVALID GTIN & EXPIRY DATE', 'BARCODE': result}
    #     elif expiry_date_check(result['EXPIRY']) == False:
    #         return {'ERROR': 'INVALID EXPIRY DATE', 'BARCODE': result}
    #     elif gtin_check(result['GTIN']) == False:
    #         return {'ERROR': 'INVALID GTIN', 'BARCODE': result}
    #     else:
    #         return result
    # else:
    #     return {'ERROR': 'INCOMPLETE DATA', 'BARCODE': result}
    return sresult


def expiry_date_check(e: str):
    my_year = e[:2]
    my_month = e[2:4]
    my_date = e[4:]

    if int(my_month) not in range(1, 13):
        return False
    elif int(my_date) not in range(32):
        return False

    if my_date == '00':
        if my_month == '02' and int(my_year) % 4 == 0:
            my_date = '29'
        elif my_month == '02' and int(my_year) % 4 != 0:
            my_date = '28'
        elif my_month in ['01', '03', '05', '07', '08', '10', '12']:
            my_date = '31'
        else:
            my_date = '30'

    if my_month == '02' and int(my_year) % 4 == 0 and my_date <= '29':
        pass
    elif my_month == '02' and int(my_year) % 4 != 0 and my_date <= '28':
        pass
    elif my_month in ['01', '03', '05', '07', '08', '10', '12'] and my_date <= '31':
        pass
    elif my_month in ['04', '06', '09', '11'] and my_date <= '30':
        pass
    else:
        return False

    actual_date = my_year + my_month + my_date
    if actual_date > datetime.today().strftime('%y%m%d'):
        return True
    else:
        return False


def ifa_ppn(barcode: str) -> dict:
    sresult = {'SCHEME': 'IFA'}
    while barcode:

        if barcode[:2] == '9N':
            sresult['PPN'] = barcode[2:14]
            if len(barcode) > 14:
                barcode = barcode[15:]
            else:
                barcode = None

        elif barcode[:1] == 'D':
            sresult['EXPIRY'] = barcode[1:7]
            if len(barcode) > 7:
                barcode = barcode[8:]
            else:
                barcode = None

        elif barcode[:2] == '1T':
            if chr(29) in barcode:
                index = barcode.index(chr(29))
                sresult['BATCH'] = barcode[2:index]
                barcode = barcode[index + 1:]
            else:
                index = barcode.index(chr(30))
                sresult['BATCH'] = barcode[2:index]
                barcode = None

        elif barcode[:1] == 'S':
            if chr(29) in barcode:
                index = barcode.index(chr(29))
                sresult['SERIAL'] = barcode[1:index]
                barcode = barcode[index + 1:]
            else:
                index = barcode.index(chr(30))
                sresult['SERIAL'] = barcode[1:index]
                barcode = None

        elif barcode[:2] == '8P':
            sresult['GTIN'] = barcode[2:16]
            if len(barcode) > 16:
                barcode = barcode[17:]
            else:
                barcode = None

        else:
            return {'ERROR': 'INVALID BARCODE', 'BARCODE': sresult}

    if 'PPN' and 'BATCH' and 'EXPIRY' and 'SERIAL' in sresult.keys():
        if ppn_check(sresult['PPN']) is False and expiry_date_check(sresult['EXPIRY']) is False:
            return {'ERROR': 'INVALID PPN & EXPIRY DATE', 'BARCODE': sresult}
        elif expiry_date_check(sresult['EXPIRY']) is False:
            return {'ERROR': 'INVALID EXPIRY DATE', 'BARCODE': sresult}
        elif not ppn_check(sresult['PPN']):
            return {'ERROR': 'INVALID PPN', 'BARCODE': sresult}
        else:
            return sresult
    else:
        return {'ERROR': 'INCOMPLETE DATA', 'BARCODE': sresult}


def ppn_check(ppn: str) -> bool:
    # i = 0
    weight = 2
    digit_sum = 0
    for i in range(10):
        digit_sum += (ord(ppn[i]) * weight)
        weight += 1
    check_digit = digit_sum % 97
    return check_digit == int(ppn[-2:])  # PPN last two chars are converted to int to remove any leading zero.

# parse_barcode('0103041094787443215Qbag!<GS>93Zjqw')
