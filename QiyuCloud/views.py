from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

import json
import yaml
import os
import time
import datetime

from .vocabulary import vocabulary_sql

config_path = './config/config.yml'
user_name = 'qiyu3816'

def global_set(context):
    context['name'] = user_name
    f = open(config_path, 'r', encoding='utf-8')
    cfg = f.read()
    config_dict = yaml.load(cfg, Loader=yaml.FullLoader)
    f.close()
    context['copyright_link'] = "http://" + config_dict['server'] + ":" + str(config_dict['port']) + "/index/"
    return config_dict

def index(request):
    request.encoding = 'utf-8'
    context = {}
    config_dict = global_set(context)

    if request.method == 'POST':
        password = request.POST.get('password')
        real_login_password = config_dict['password_login']
        if password == real_login_password:
            return redirect('/home/')
        else:
            context['result'] = 'failed'
            return render(request, 'index.html', context)
    else:
        context['result'] = 'doing'
        return render(request, 'index.html', context)

def verify_admin(request):
    request.encoding = 'utf-8'
    context = {}
    config_dict = global_set(context)

    if request.method == 'POST':
        password = request.POST.get('password')

        real_admin_password = config_dict['password_admin']
        if password == real_admin_password:
            return redirect('/resetpassword/')
        else:
            context['result'] = 'failed'
            return render(request, 'verifyadmin.html', context)
    else:
        context['result'] = 'doing'
        return render(request, 'verifyadmin.html', context)

def reset_password(request):
    request.encoding = 'utf-8'
    context = {}
    config_dict = global_set(context)

    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 == password2:
            config_dict['password_login'] = password1

            f = open(config_path, 'w', encoding='utf-8')
            yaml.dump(data=config_dict, stream=f, allow_unicode=True)
            f.close()
            return redirect('/index/')
        else:
            context['result'] = 'failed'
            return render(request, 'resetpassword.html', context)
    else:
        context['result'] = 'doing'
        return render(request, 'resetpassword.html', context)

@csrf_exempt
def home(request):
    request.encoding = 'utf-8'
    context = {}
    config_dict = global_set(context)
    context['data_url'] = "http://" + config_dict['server'] + ":" + str(config_dict['port']) + "/data"
    context['review_finish_button_url'] = "http://" + config_dict['server'] + ":" + str(config_dict['port']) + "/home/"

    # 处理review_finish
    review_finish_button_click = False
    if request.method == 'POST':
        if request.POST.get('review_finish', True):
            review_finish_button_click = True

    already_finished = False
    if datetime.date.today() == config_dict['home_last_review_date']:
        already_finished = True

    if review_finish_button_click or already_finished:
        context['review_finish_button'] = True
        if review_finish_button_click and not already_finished:
            config_dict['home_last_review_date'] = datetime.date.today()
            config_dict['home_review_twice_range'] = config_dict['home_step']
            config_dict['home_arrived_pos'] += config_dict['home_step']
            f = open(config_path, 'w+', encoding='utf-8')
            yaml.dump(config_dict, stream=f, allow_unicode=True)
            f.close()
            print("[home_page]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "`review_finish_button_click` is True and related change has been set.")
    else:
        context['review_finish_button'] = False


    # 处理home_step设置
    context['home_step_set_state'] = '当前每日学{}个'.format(config_dict['home_step'])
    if request.method == 'POST':
        if request.POST.get('home_step'):
            new_home_step = request.POST.get('home_step')
            config_dict['home_step'] = int(new_home_step)
            f = open(config_path, 'w+', encoding='utf-8')
            yaml.dump(config_dict, stream=f, allow_unicode=True)
            f.close()
            context['home_step_set_state'] = '当前每日学{}个'.format(config_dict['home_step'])
            print("[home_page]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "`home_step` is reset to {}.".format(config_dict['home_step']))


    # 处理新数据输入
    context['insert_state'] = '等待填写'
    if request.method == 'POST':
        if request.POST.get('insert_data'):
            insert_data = request.POST.get('insert_data')
            insert_processed_data = insert_data.split()
            sign = True
            for i in range(0, len(insert_processed_data), 2):
                if not insert_processed_data[i].encode('utf-8').isalpha():
                    context['insert_state'] = '格式错误'
                    sign = False
                    print("[home_page]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                          "Insert data's format is wrong.")
                    break
            if sign:  # 如果每个单数行都是全英文则格式合法
                tuple_list = []
                for i in range(0, len(insert_processed_data), 2):
                    tuple_list.append((insert_processed_data[i], insert_processed_data[i + 1], insert_processed_data[i + 1]))

                vocabulary_op = vocabulary_sql(os.path.abspath(config_path))
                if len(tuple_list) > 1:
                    vocabulary_op.insert_batch(tuple_list)
                else:
                    vocabulary_op.insert_one(tuple_list[0])

                context['insert_state'] = '插入完成'
                print("[home_page]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                      "New data insert finished.")

    return render(request, 'home.html', context)

def data(request):
    vocabulary_op = vocabulary_sql(os.path.abspath(config_path))
    data_array = vocabulary_op.select_batch()
    vocabulary_op.close_connection()

    sql_data_dict = {"total": data_array.shape[0], "rows": []}
    for item in data_array:
        sql_data_dict["rows"].append({'word_id': item[0], 'en_word': item[1], 'chi_val': item[2]})

    return HttpResponse(json.dumps(sql_data_dict))