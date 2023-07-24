import ui_global

#Перебираем релизы по одному. Функция пытается найти в модуле функцию с именем,
# соответствующим номеру релиза и если нашла - выполнить её
def run_releases(_start_version, _end_version):
    version = _start_version
    while compare_versions(version, _end_version) <= 0:
        release_function_name = 'r' + version.replace('.', '_')
        release_function = globals().get(release_function_name)
        if release_function and callable(release_function):
            release_function()
        else:
            print(f"Release function '{release_function_name}' not found.")

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



def r0_1_0_12_3():
    # Code for release 0.1.0.12.3
    print('Выполнено r0_1_0_12_3')
    pass


def r0_1_0_11_17():
    # Code for release 0.1.0.11.7
    print('Выполнено r0_1_0_11_7')
    pass

def r0_1_0_11_7():
    # Code for release 0.1.0.11.7
    print('Выполнено r0_1_0_11_7')
    pass


if __name__ == "__main__":
    # Replace these versions with your actual version numbers
    start_version = "0.1.0.11.7"
    end_version = "0.1.0.12.3"

    run_releases(start_version, end_version)
