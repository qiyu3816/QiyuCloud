"""
.xlsx文件批量导入与导出工具脚本
默认host='localhost', user='root', db='qiyucloud', table='qiyu_vocabulary'
python vocabulary_tool.py <password> <mode:input|output> <input_path|output_path>
"""

import sys
import time
import datetime
import pandas as pd
import numpy as np
import pymysql.cursors

def output2xlsx(connection, path):
    """
    读取数据库中所有字段并输出到指定文件
    :param connection:
    :param path:
    :return:
    """
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `en_word`, `chi_val`, `create_time`, `review_time` FROM qiyu_vocabulary"
            cursor.execute(sql)
            result = cursor.fetchall()
    except pymysql.Error as e:
        print(e)
        connection.rollback()
        connection.close()
        sys.exit(1)
    finally:
        connection.commit()
        print("Data got, connection will be closed and file will be written.")
        connection.close()

    np_data = np.asarray(result, dtype=np.str_)

    data_frame = pd.DataFrame({'en_word': np_data[:, 0],
                               'chi_val': np_data[:, 1],
                               'create_time': np_data[:, 2],
                               'review_time': np_data[:, 3]})
    writer = pd.ExcelWriter(path)
    data_frame.to_excel(writer, index=False)
    writer.save()
    print("Output finished.")


def input_from_xlsx(connection, path):
    """
    从指定文件批量导入字段
    :param connection:
    :param path:
    :return:
    """
    data_frame = pd.read_excel(path)
    values = np.array(data_frame.values)
    print("Read {} items.".format(values.shape[0]))
    tuple_data = []
    for i in range(len(values)):
        tuple_data.append((values[i, 0], values[i, 1], time.strftime("%Y-%m-%d", time.localtime()), values[i, 1]))

    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO qiyu_vocabulary (`en_word`, `chi_val`, `create_time`) " \
                  "VALUES(%s, %s, %s) ON DUPLICATE KEY UPDATE chi_val=%s"
            for item in tuple_data:
                cursor.execute(sql, item)
    except pymysql.Error as e:
        print(e)
        connection.rollback()
        connection.close()
        sys.exit(1)
    finally:
        connection.commit()
        print("Insert finished, connection will be closed.")
        connection.close()


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Invalid parameters. Follow this: \npython vocabulary_tool.py <password> <mode:input|output> <input_path|output_path>")
        exit()

    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password=sys.argv[1],
                                 db='qiyucloud',
                                 charset='utf8')

    if sys.argv[2] == 'output':
        output2xlsx(connection, sys.argv[3])
    else:
        input_from_xlsx(connection, sys.argv[3])

