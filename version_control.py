import db_services
import  re
#from
def is_valid_version(version):
    # Regular expression to check if the version has the correct format (x.x.x.x)
    if not isinstance(version, str):
        return False

    pattern = r'^\d{1,2}(\.\d{1,2}){4}'

    return bool(re.match(pattern, version))


#Перебираем релизы по одному. Функция пытается найти в модуле функцию с именем,
# соответствующим номеру релиза и если нашла - выполнить её
def run_releases(_start_version:str, _end_version:str):
    return_list = []
    if not is_valid_version(_start_version) or not is_valid_version(_end_version):
        return_list.append({'result': False, 'details': 'Неверный формат версии конфигурации. Формат конфигурации должен быть x.x.x.x'})
        return return_list


    version = _start_version
    while compare_versions(version, _end_version) <= 0:
        release_function_name = 'r' + version.replace('.', '_')
        release_function = globals().get(release_function_name)
        if release_function and callable(release_function):

            res = release_function()
            return_list.append(res)
        # else:
        #     print(f"Release function '{release_function_name}' not found.")

        version = increment_version(version)

    return return_list


#Сравниваем номера версии. Возвращает -1 Последняя версия все ещё больше,
# 0 если равны и 1 если текущая версия больше последней
def compare_versions(version1, version2):
    parts1 = list(map(int, version1.split('.')))
    parts2 = list(map(int, version2.split('.')))

    for p1, p2 in zip(parts1, parts2):
        if p1 < p2:
            return -1
        elif p1 > p2:
            return 1

    return 0


#Прибавляем 1 к номеру текущей версии (по группам,
# максимум 99 в одной группе) Например 1.1.1.1.99 + 1 даст нам 1.1.1.2.0
def increment_version(version):
    parts = list(map(int, version.split('.')))
    parts[-1] += 1
    for i in range(len(parts) - 1, 0, -1):
        if parts[i] == 100:
            parts[i] = 0
            parts[i - 1] += 1
    return '.'.join(map(str, parts))



def r0_1_0_12_3(hash_map):
    # Code for release 0.1.0.12.3
    qtext = '''
    PRAGMA foreign_keys = 0;

    CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                              FROM RS_barcodes;
    
    DROP TABLE RS_barcodes;
    
    CREATE TABLE RS_barcodes (
        barcode     TEXT    NOT NULL
                            PRIMARY KEY,
        id_good     TEXT    NOT NULL,
        id_property TEXT,
        id_series   TEXT,
        id_unit     TEXT,
        ratio       INTEGER DEFAULT (1) 
                            NOT NULL
    );
    
    INSERT INTO RS_barcodes (
                                barcode,
                                id_good,
                                id_property,
                                id_series,
                                id_unit,
                                ratio
                            )
                            SELECT barcode,
                                   id_good,
                                   id_property,
                                   id_series,
                                   id_unit,
                                   ratio
                              FROM sqlitestudio_temp_table;
    
        
    UPDATE
    RS_barcodes
    SET
    ratio = COALESCE((
        SELECT RS_units.nominator/RS_units.denominator
    FROM RS_units
    WHERE RS_units.id = RS_barcodes.id_unit
    ), 1);
    
        
    DROP TABLE sqlitestudio_temp_table;
    
    PRAGMA foreign_keys = 1;
    '''

    try:
        r = db_services.SqlQueryProvider()
        r.sql_exec(qtext,'')
        return_value = {'result':True}
    except:
        return_value = {'result':False, 'details':f'Ошибка в запросе: {qtext}'}


def r0_1_0_13_7(hash_map):

    q = '''
    PRAGMA foreign_keys = 0;

    CREATE
    TABLE
    sqlitestudio_temp_table
    AS
    SELECT * FROM RS_docs_table;

    DROP TABLE RS_docs_table;
    
    CREATE TABLE RS_docs_table(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_doc TEXT NOT NULL REFERENCES RS_docs(id_doc)
    ON DELETE CASCADE ON UPDATE SET DEFAULT,
    id_good TEXT NOT NULL REFERENCES RS_goods(id),
    id_properties TEXT REFERENCES RS_properties(id),
    id_series TEXT REFERENCES RS_series(id),
    id_unit TEXT NOT NULL REFERENCES RS_units(id),
    qtty REAL, 
    qtty_plan REAL,
    price REAL,
    id_price TEXT REFERENCES  RS_price_types(id),
    sent INTEGER,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_plan TEXT DEFAULT True,
    id_cell TEXT REFERENCES RS_cells(id),
    use_series    INT      NOT NULL
                           DEFAULT (0)
    );

    INSERT INTO RS_docs_table(
        id, id_doc, id_good, id_properties, id_series, id_unit, qtty,
        qtty_plan, price, id_price, sent, last_updated, is_plan, id_cell
    )
    SELECT
    id, id_doc, id_good, id_properties, id_series, id_unit, qtty, qtty_plan,
    price, id_price, sent, last_updated, is_plan, id_cell FROM sqlitestudio_temp_table;
    
    DROP TABLE sqlitestudio_temp_table;
    
    PRAGMA foreign_keys = 1;

    '''
    try:
        r = db_services.SqlQueryProvider()
        r.sql_exec(q,'')
        return_value = {'result':True}
    except:
        return_value = {'result':False, 'details':f'Ошибка в запросе: {q}'}


# if __name__ == "__main__":
#     # Replace these versions with your actual version numbers
#     start_version = "0.1.0.11.7"
#     start_version = ("s")
#     end_version = "0.1.0.12.3"
#
#     print(run_releases(start_version, end_version))
#print(is_valid_version("01.1.0.11.26"))