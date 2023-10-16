import json
import os
from typing import Any


def jclass(cls_name):
    if cls_name == 'ru.travelfood.simple_ui.NoSQL':
        return NoSQL


class NoSQL:
    def __init__(self, database: str):
        if database:
            self.database = database
            self.database_path = f'{database}.json'
            if not os.path.exists(self.database_path):
                with open(self.database_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=4)
        else:
            raise ValueError('Database name must be specified ')

    def get(self, key: str):
        with open(self.database_path, encoding='utf-8') as f:
            return json.load(f).get(key)

    def put(self, key: str, value, queue):
        with open(self.database_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        data[key] = value

        with open(self.database_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def getallkeys(self) -> str:
        with open(self.database_path, encoding='utf-8') as f:
            res = [key for key in json.load(f)]
            return json.dumps(res, separators=(',', ', '))

    def delete(self, key):
        with open(self.database_path, encoding='utf-8') as f:
            data = json.load(f)
        data.pop(key, None)
        with open(self.database_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def destroy(self):
        with open(self.database_path, encoding='utf-8', mode='w') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

    def findJSON(self, field: str, value: Any) -> Any:
        with open(self.database_path, encoding='utf-8') as f:
            data = json.load(f)
        res = []
        for elem in data:
            try:
                dict_elem = json.loads(data[elem])
                if dict_elem[field] == value:
                    res.append(json.dumps(
                        {"key": elem, "value": data[elem]},
                        ensure_ascii=False)
                    )
            except Exception as e:
                pass

        return '[' + ','.join(res) + ']'

    def findJSON_index(self, index_name: str, field: str, value: Any) -> Any:
        self.findJSON(field, value)

    def run_index(self, index: str, field: str):
        pass
