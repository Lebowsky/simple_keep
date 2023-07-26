import db_services
#from

#Перебираем релизы по одному. Функция пытается найти в модуле функцию с именем,
# соответствующим номеру релиза и если нашла - выполнить её
def run_releases(_start_version, _end_version, hash_map):
    version = _start_version
    while compare_versions(version, _end_version) <= 0:
        release_function_name = 'r' + version.replace('.', '_')
        release_function = globals().get(release_function_name)
        if release_function and callable(release_function):
            release_function(hash_map)
        # else:
        #     print(f"Release function '{release_function_name}' not found.")

        version = increment_version(version)


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
    except:
        pass




# if __name__ == "__main__":
#     # Replace these versions with your actual version numbers
#     start_version = "0.1.0.11.7"
#     end_version = "0.1.0.12.3"
#
#     run_releases(start_version, end_version)
