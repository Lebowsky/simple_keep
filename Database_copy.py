import requests
from flask import Flask
from flask import request
import os
import json

app = Flask(__name__)

## переносим таблицы с телефона локально
def get_remote_table():

   r = requests.post(url = "http://192.168.0.72:8095/?mode=SQLQueryText&query=SELECT * FROM RS_barcodes&params=",   #SELECT name FROM sqlite_master WHERE type='table'
                     headers={'Content-Type': 'Application/json; charset=utf-8'})  #

   if r.status_code == 200:
        r.encoding = 'utf-8'
        #jdata = json.loads(r.text.encode("utf-8"))
        print(r.text)
#get_remote_table()

@app.route('/post', methods=['POST'])
def post():
    path = os.getcwd()

    for filename in request.files:
        file = request.files[filename] #rightscan
        if file:
            file.save(path + '\\'+ filename)
            print(f'file {filename} uploaded')
            file.close()
    return '200'


@app.route('/unload_log', methods=['POST'])
def unload_log():
    path = os.getcwd()
    data = request.get_json()
    if data:
        with open(os.path.join(path, 'rs_log.json'), 'w', encoding='utf-8') as f:
            json.dump(json.loads(data), f, ensure_ascii=False, indent=2)
            print('file uploaded')
        return '200'

if __name__ == '__main__':
    #ui_global.init()
    app.run(host='0.0.0.0', port=2444, debug=True)