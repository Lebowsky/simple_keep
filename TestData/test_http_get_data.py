import json

import ui_models
import rs_settings
import ui_utils

with open('../HashMap.json') as f:
    hs = json.load(f)

timer = ui_models.Timer(ui_utils.HashMap(hash_map = hs), rs_settings.RSSettings())
timer.timer_on_start()