class hashMap:
    def __init__(self):
        self.d = {}

    def put(self, key, val):
        if key == 'toast':
            print(val)
        self.d[key] = val

    def get(self, key):
        return self.d.get(key)

    def remove(self, key):
        if key in self.d:
            self.d.pop(key)

    def delete(self, key):
        if key in self.d:
            self.d.pop(key)

    def containsKey(self, key):
        return key in self.d

    def export(self):
        ex_hashMap = []
        for key in self.d.keys():
            ex_hashMap.append({"key": key, "value": self.d[key]})
        return ex_hashMap

