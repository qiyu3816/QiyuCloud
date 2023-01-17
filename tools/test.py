import yaml
import time
import datetime
import numpy as np
# 验证了日期触发的可行性 测试了link拼接 确定了统一使用time不再使用datetime
f = open('../config/config.yml', 'r', encoding='utf-8')
cfg = f.read()
config_dict = yaml.load(cfg, Loader=yaml.FullLoader)
f.close()

print(config_dict)
print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
print("http://" + config_dict['server'] + ":" + str(config_dict['port']))
if time.strftime("%Y-%m-%d", time.localtime()) > config_dict['home_last_review_date']:
    print("Yes")
else:
    print("No")
config_dict['home_last_review_date'] = time.strftime("%Y-%m-%d", time.localtime())
f = open('../config/config.yml', 'w+', encoding='utf-8')
yaml.dump(config_dict, stream=f, allow_unicode=True)
f.close()