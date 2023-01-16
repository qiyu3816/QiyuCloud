import yaml
import datetime
import numpy as np
# 验证了日期触发的可行性
f = open('../config/config.yml', 'r', encoding='utf-8')
cfg = f.read()
config_dict = yaml.load(cfg, Loader=yaml.FullLoader)
f.close()

print(config_dict)
print("http://" + config_dict['server'] + ":" + str(config_dict['port']))
if datetime.date.today() > config_dict['home_last_review_date']:
    print("Yes")
else:
    print("No")
config_dict['home_last_review_date'] = datetime.date.today()
f = open('../config/config.yml', 'w+', encoding='utf-8')
yaml.dump(config_dict, stream=f, allow_unicode=True)
f.close()