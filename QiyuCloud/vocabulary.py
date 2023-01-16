import sys
import time
import datetime
import yaml
import pymysql.cursors
import numpy as np

class vocabulary_sql:

    def __init__(self, config_abs_path, password='1039lrh'):
        """
        默认host='localhost', user='root', db='qiyucloud', table='qiyu_vocabulary'
        :param password:
        """
        self.config_abs_path = config_abs_path
        self.connection = pymysql.connect(host='localhost',
                                          user='root',
                                          password=password,
                                          db='qiyucloud',
                                          charset='utf8')
        print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
              "Connection to db opening.")


    def insert_one(self, data):
        try:
            with self.connection.cursor() as cursor:
                # 重复en_word直接覆盖chi_val
                sql = "INSERT INTO qiyu_vocabulary (`en_word`, `chi_val`) " \
                      "VALUES(%s, %s) ON DUPLICATE KEY UPDATE chi_val=%s"
                cursor.execute(sql, data)
        except pymysql.Error as e:
            print(e)
            self.connection.rollback()
            self.connection.close()
        finally:
            self.connection.commit()
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "Insert one finished.")


    def insert_batch(self, tuple_data):
        try:
            with self.connection.cursor() as cursor:
                sql = "INSERT INTO qiyu_vocabulary (`en_word`, `chi_val`) " \
                      "VALUES(%s, %s) ON DUPLICATE KEY UPDATE chi_val=%s"
                for item in tuple_data:
                    cursor.execute(sql, item)
        except pymysql.Error as e:
            print(e)
            self.connection.rollback()
            self.connection.close()
        finally:
            self.connection.commit()
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "Insert batch finished.")


    def select_batch(self):
        f = open(self.config_abs_path, 'r', encoding='utf-8')
        cfg = f.read()
        config_dict = yaml.load(cfg, Loader=yaml.FullLoader)
        f.close()

        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT `word_id`, `en_word`, `chi_val` FROM qiyu_vocabulary"
                cursor.execute(sql)
                result = cursor.fetchall()
        except pymysql.Error as e:
            print(e)
            self.connection.rollback()
            self.connection.close()
        finally:
            self.connection.commit()
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "Data got.")

        np_data = np.asarray(result, dtype=(np.str_, np.str_))
        home_arrived_pos = config_dict['home_arrived_pos']

        if datetime.date.today() > config_dict['home_last_review_date']:  # 基于home_step返回新数据
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "No review today, return new words.")
            home_step = config_dict['home_step']
            if home_step < len(np_data):
                if home_arrived_pos + home_step < len(np_data):
                    np_data[home_arrived_pos:home_arrived_pos + home_step, 0] = np.arange(1, home_step + 1, 1)
                    return np_data[home_arrived_pos:home_arrived_pos + home_step]
                else:
                    rt_data = np.reshape(np.append(np_data[home_arrived_pos:],
                                                   np_data[:(home_arrived_pos + home_step) % len(np_data)]),
                                         newshape=(home_step, np_data.shape[1]))
                    rt_data[:, 0] = np.arange(1, home_step + 1, 1)
                    return rt_data
            else:
                return np_data
        else:  # 基于home_review_twice_range返回已复习的数据
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "Already reviewed today, return the reviewed words.")
            home_review_twice_range = config_dict['home_review_twice_range']
            if home_arrived_pos - home_review_twice_range < 0:
                rt_data = np.reshape(np.append(np_data[home_arrived_pos - home_review_twice_range:],
                                               np_data[:home_arrived_pos]),
                                     newshape=(home_review_twice_range, np_data.shape[1]))
            else:
                rt_data = np_data[home_arrived_pos - home_review_twice_range:home_arrived_pos]
            rt_data[:, 0] = np.arange(1, home_review_twice_range + 1, 1)
            return rt_data


    def close_connection(self):
        try:
            self.connection.close()
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "SQL connection closing.")
        except pymysql.Error as e:
            print(e)
