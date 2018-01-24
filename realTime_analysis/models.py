from django.db import models
import time, datetime
from mongoengine import *

current_hour = time.localtime()[3]  # 获取当前的小时数，如果小于12则应该选择yesterday
nowadays = datetime.datetime.now().strftime("%Y-%m-%d")  # 获取当前日期 格式2018-01-01
yesterdy = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d")  # 获取昨天日期
if current_hour < 12:
    current_search_date = yesterdy  # str
else:
    current_search_date = nowadays  # str
DBNAME = 'realTime_' + current_search_date

# 链接MongoDB
connect(DBNAME, host='127.0.0.1', port=27017)
# Create your models here.
class single_match(Document):
    name = StringField(max_length=16)
    age = IntField(default=1)

    meta = {'collection': 'sample'}  # 指明连接数据库的哪张表