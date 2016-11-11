
_config_dict = {}

def set_config(**kargs):
    global _config_dict
    _config_dict = kargs

def get_value(param, default=""):
    global _config_dict
    return _config_dict.get(param, default)

