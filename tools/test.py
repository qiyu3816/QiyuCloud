import yaml
import time
import datetime
import numpy as np
import heapq
# 验证了日期触发的可行性 测试了link拼接 确定了统一使用time不再使用datetime
f = open('../config/config.yml', 'r', encoding='utf-8')
cfg = f.read()
config_dict = yaml.load(cfg, Loader=yaml.FullLoader)
f.close()

print(config_dict)
print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
print("http://" + config_dict['server'] + ":" + str(config_dict['port']))

# 验证了yaml读写列表的方式
print(config_dict['home_last_reviewed'])
home_last_reviewed_indexes = list(config_dict['home_last_reviewed'])
print(home_last_reviewed_indexes, len(home_last_reviewed_indexes), type(home_last_reviewed_indexes[0]))
home_last_reviewed_indexes.append(6)
print(home_last_reviewed_indexes)
config_dict['home_last_reviewed'] = home_last_reviewed_indexes

# if time.strftime("%Y-%m-%d", time.localtime()) > config_dict['home_last_review_date']:
#     print("Yes")
# else:
#     print("No")
# config_dict['home_last_review_date'] = time.strftime("%Y-%m-%d", time.localtime())

f = open('../config/config.yml', 'w+', encoding='utf-8')
yaml.dump(config_dict, stream=f, allow_unicode=True)
f.close()
