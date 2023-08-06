import time
import datetime
import yaml
import pymysql.cursors
import numpy as np
import heapq

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
        full_data = (data[0], data[1], time.strftime("%Y-%m-%d", time.localtime()), data[2])

        try:
            with self.connection.cursor() as cursor:
                # 重复en_word直接覆盖chi_val
                sql = "INSERT INTO qiyu_vocabulary (`en_word`, `chi_val`, `create_time`) " \
                      "VALUES(%s, %s, %s) ON DUPLICATE KEY UPDATE chi_val=%s"
                cursor.execute(sql, full_data)
        except pymysql.Error as e:
            print(e)
            self.connection.rollback()
            self.connection.close()
        finally:
            self.connection.commit()
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "Insert one finished.")


    def insert_batch(self, tuple_data):
        full_tuple_data = []
        for item in tuple_data:
            full_tuple_data.append((item[0], item[1], time.strftime("%Y-%m-%d", time.localtime()), item[2]))

        try:
            with self.connection.cursor() as cursor:
                sql = "INSERT INTO qiyu_vocabulary (`en_word`, `chi_val`, `create_time`) " \
                      "VALUES(%s, %s, %s) ON DUPLICATE KEY UPDATE chi_val=%s"
                for item in full_tuple_data:
                    cursor.execute(sql, item)
        except pymysql.Error as e:
            print(e)
            self.connection.rollback()
            self.connection.close()
        finally:
            self.connection.commit()
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "Insert batch finished.")


    def selected_date_process(self, np_data):
        """
        根据词条的review_time计算score review_time旧的score大
        :param np_data:
        :return:
        """
        scores = np.array([])  # 热度 越高被选中概率越大
        today_date = datetime.datetime.strptime(time.strftime("%Y-%m-%d", time.localtime()), "%Y-%m-%d").date()
        for item in np_data:
            if item[4] == 'None':
                # 如果review_time为空 直接用create_time替代
                review_dis = (today_date - datetime.datetime.strptime(item[3], "%Y-%m-%d").date()).days
            else:
                review_dis = (today_date - datetime.datetime.strptime(item[4], "%Y-%m-%d").date()).days
            scores = np.append(scores, min(np.exp(int(review_dis)), 100))
        return scores


    def select_batch(self):
        f = open(self.config_abs_path, 'r', encoding='utf-8')
        cfg = f.read()
        config_dict = yaml.load(cfg, Loader=yaml.FullLoader)
        f.close()

        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT `word_id`, `en_word`, `chi_val`, `create_time`, `review_time` FROM qiyu_vocabulary"
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

        np_data = np.asarray(result, dtype=np.str_)

        if time.strftime("%Y-%m-%d", time.localtime()) > str(config_dict['home_last_review_date']):  # 基于home_step返回新数据
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "No review today, return new words.")
            home_step = config_dict['home_step']
            if home_step < len(np_data):
                scores = self.selected_date_process(np_data)
                target_indexes = heapq.nlargest(home_step, range(len(scores)), scores.__getitem__)
                rt_data = np.array([])
                for k, index in enumerate(target_indexes):
                    rt_data = np.append(rt_data, (k + 1, np_data[index, 1], np_data[index, 2]))
                rt_data = np.reshape(rt_data, newshape=(len(target_indexes), 3))
                rt_data = np.random.shuffle(rt_data)
                return rt_data
            else:
                np_data[:, 0] = range(1, len(np_data) + 1, 1)
                np_data = np.random.shuffle(np_data)
                return np_data[:, :3]
        else:  # 基于home_last_reviewed返回已复习的数据
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "Already reviewed today, return the reviewed words.")
            home_last_reviewed_indexes = list(config_dict['home_last_reviewed'])
            rt_data = np.array([])
            for k, index in enumerate(home_last_reviewed_indexes):
                rt_data = np.append(rt_data, (k + 1, np_data[index, 1], np_data[index, 2]))
            rt_data = np.reshape(rt_data, newshape=(len(home_last_reviewed_indexes), 3))
            rt_data = np.random.shuffle(rt_data)
            return rt_data


    def update_config_home_last_reviewed(self, config_dict):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT `word_id`, `en_word`, `chi_val`, `create_time`, `review_time` FROM qiyu_vocabulary"
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

        np_data = np.asarray(result, dtype=np.str_)

        home_step = config_dict['home_step']
        if home_step < len(np_data):
            scores = self.selected_date_process(np_data)
            target_indexes = heapq.nlargest(home_step, range(len(scores)), scores.__getitem__)
        else:
            target_indexes = range(len(np_data))

        config_dict['home_last_reviewed'] = target_indexes
        f = open(self.config_abs_path, 'w+', encoding='utf-8')
        yaml.dump(config_dict, stream=f, allow_unicode=True)
        f.close()

        try:
            with self.connection.cursor() as cursor:
                sql = "UPDATE qiyu_vocabulary SET review_time=%s where en_word=%s"
                for i in target_indexes:
                    cursor.execute(sql, (time.strftime("%Y-%m-%d", time.localtime()), np_data[i, 1]))
        except pymysql.Error as e:
            print(e)
            self.connection.rollback()
            self.connection.close()
        finally:
            self.connection.commit()
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "Review time updating finished.")


    def close_connection(self):
        try:
            self.connection.close()
            print("[vocabulary_sql]:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                  "SQL connection closing.")
        except pymysql.Error as e:
            print(e)
