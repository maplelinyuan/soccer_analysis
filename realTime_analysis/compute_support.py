# 计算当天比赛推荐

from pymongo import MongoClient
import datetime
import time
import regex
import json
import pdb
import numpy
from collections import Counter

# 一些参数
need_company_id = '156'  # 必须含有的公司ID
need_company_number = 35    # 开赔率公司必须达到的数量
first_limit_mktime = 198000     # 初盘限制时间
first_limit_min_mktime = 165600     # 初盘最小时间
limit_mktime = 15600     # 临场N小时
limit_change_prob = 0.035     # 限制概率变化
limit_draw_odd_differ = 0.01     # 限制平局赔率差
# 参数结束

current_hour = time.localtime()[3]  # 获取当前的小时数，如果小于12则应该选择yesterday
nowadays = datetime.datetime.now().strftime("%Y-%m-%d")  # 获取当前日期 格式2018-01-01
yesterdy = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d")  # 获取昨天日期
if current_hour < 12:
    current_search_date = yesterdy  # str
else:
    current_search_date = nowadays  # str

# 链接数据库
client = MongoClient(host='localhost', port=27017)
# client.admin.authenticate(settings['MINGO_USER'], settings['MONGO_PSW'])     #如果有账户密码
# 先找到当前正在爬取的matchId_list
# db = client['realTime_info']
# info_coll = db['realTime_crawling']
# crawling_match_id_list = [data for data in info_coll.findOne({"crawling": 1})['matchId_list']]
db = client['realTime_info']
info_coll = db['realTime_crawling']
crawling_match_id_list = []
if 'matchId_list' in info_coll.find_one({"crawling": 1}).keys():
    for item in info_coll.find_one({"crawling": 1})['matchId_list']:
        crawling_match_id_list.append(str(item).strip())

db_name = 'realTime_matchs'
db = client[db_name]  # 获得数据库的句柄
coll_name = 'matchs_' + current_search_date
coll = db[coll_name]  # 获得collection的句柄

for single_match_dict in coll.find():
    match_id = single_match_dict['match_id']
    # 如果当前match_id是正在爬取的比赛，则跳过
    if match_id in crawling_match_id_list:
        continue
    # 遍历当天所有比赛
    league_name = single_match_dict['league_name']
    home_name = single_match_dict['home_name']
    away_name = single_match_dict['away_name']
    start_time = single_match_dict['start_time']  # 如：2018-01-12 18:00
    start_timestamp = time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M"))  # 开赛时间戳
    match_company_id_list = single_match_dict['company_id_list']
    # 单场比赛信息字典
    single_match_info_dict = {
        'start_time': start_time,
    }
    original_home_prob_list = []  # 初主赔列表
    original_draw_prob_list = []  # 初平赔列表
    original_away_prob_list = []  # 初客赔列表

    last_home_prob_list = []  # 平均限制时间终主赔列表
    last_draw_prob_list = []  # 平均限制时间终平赔列表
    last_away_prob_list = []  # 平均限制时间终客赔列表
    if len(match_company_id_list) < need_company_number:
        continue  # 该场比赛开盘公司数目小于10就跳过

    # 如果某公司ID不在该场比赛中就跳过
    if need_company_id != '' and not need_company_id in [item.split('_')[-1] for item in match_company_id_list]:
        print('%s 不含有必要开赔公司ID' % match_id)
        continue
    company_coll = db["match_" + match_id]
    for single_company_id in match_company_id_list:
        # 遍历单场比赛所有赔率公司列表, 为了求限制时间前的平均概率
        company_coll_cursor = company_coll.find({"company_id": single_company_id})  # 查询赔率信息
        # current_company_odd_num = company_coll_cursor.count()  # 当前比赛当前公司赔率数目
        original_home_odd = company_coll_cursor['home_odd']
        original_draw_odd = company_coll_cursor['draw_odd']
        original_away_odd = company_coll_cursor['away_odd']
        last_home_odd = company_coll_cursor['last_home_odd']
        last_draw_odd = company_coll_cursor['last_draw_odd']
        last_away_odd = company_coll_cursor['last_away_odd']
        original_home_probability = round(
            (original_draw_odd * original_away_odd) / (original_home_odd * original_draw_odd + original_home_odd * original_away_odd + original_draw_odd * original_away_odd), 3)
        original_draw_probability = round(
            (original_home_odd * original_away_odd) / (original_home_odd * original_draw_odd + original_home_odd * original_away_odd + original_draw_odd * original_away_odd), 3)
        original_away_probability = round(
            (original_home_odd * original_draw_odd) / (original_home_odd * original_draw_odd + original_home_odd * original_away_odd + original_draw_odd * original_away_odd), 3)
        original_home_prob_list.append(original_home_probability)
        original_draw_prob_list.append(original_draw_probability)
        original_away_prob_list.append(original_away_probability)
        last_home_probability = round(
            (last_draw_odd * last_away_odd) / (
                    last_home_odd * last_draw_odd + last_home_odd * last_away_odd + last_draw_odd * last_away_odd),
            3)
        last_draw_probability = round(
            (last_home_odd * last_away_odd) / (
                    last_home_odd * last_draw_odd + last_home_odd * last_away_odd + last_draw_odd * last_away_odd),
            3)
        last_away_probability = round(
            (last_home_odd * last_draw_odd) / (
                    last_home_odd * last_draw_odd + last_home_odd * last_away_odd + last_draw_odd * last_away_odd),
            3)
        last_home_prob_list.append(last_home_probability)
        last_draw_prob_list.append(last_draw_probability)
        last_away_prob_list.append(last_away_probability)
    if len(last_home_prob_list) == 0:
        continue
    last_home_prob_average = round(sum(last_home_prob_list) / len(last_home_prob_list), 3)
    last_draw_prob_average = round(sum(last_draw_prob_list) / len(last_draw_prob_list), 3)
    last_away_prob_average = round(sum(last_away_prob_list) / len(last_away_prob_list), 3)
    original_home_prob_average = round(sum(original_home_prob_list) / len(original_home_prob_list), 3)
    original_draw_prob_average = round(sum(original_draw_prob_list) / len(original_draw_prob_list), 3)
    original_away_prob_average = round(sum(original_away_prob_list) / len(original_away_prob_list), 3)

    home_pro_diff = (last_home_prob_average - original_home_prob_average) - limit_change_prob
    draw_pro_diff = (last_draw_prob_average - original_draw_prob_average) - (
            limit_change_prob - limit_draw_odd_differ)  # 平局限制赔率有所降低
    away_pro_diff = (last_away_prob_average - original_away_prob_average) - limit_change_prob
    if home_pro_diff > 0 or draw_pro_diff > 0 or away_pro_diff > 0:
        single_match_info_dict['support_direction'] = ''
        if home_pro_diff > 0:
            # 如果初始该方向概率不是最大就跳过
            if original_home_prob_average <= original_draw_prob_average or original_home_prob_average <= original_away_prob_average:
                continue
            # 跳过选择方向赔率小于1.5的比赛
            if (0.95 / last_home_prob_average) < 1.5:
                continue
            single_match_info_dict['support_direction'] += '3'
        if draw_pro_diff > 0:
            # 跳过选择方向赔率小于1.5的比赛
            if (0.95 / last_draw_prob_average) < 1.5:
                continue
            single_match_info_dict['support_direction'] += '1'

            if (0.95 / last_draw_prob_average) >= 3.8:
                # 如果支持方向是平局，且平局赔率大于等于3.8，则同时也支持低概率方向
                if last_home_prob_average < 0.30 and home_pro_diff <= 0:
                    # 同时支持主胜
                    single_match_info_dict['support_direction'] += '3'
                elif last_away_prob_average < 0.30 and away_pro_diff <= 0:
                    # 同时支持客胜
                    single_match_info_dict['support_direction'] += '0'
        if away_pro_diff > 0:
            # 如果初始该方向概率不是最大就跳过
            if original_away_prob_average <= original_home_prob_average or original_away_prob_average <= original_draw_prob_average:
                continue
            # 跳过选择方向赔率小于1.5的比赛
            if (0.95 / last_away_prob_average) < 1.5:
                continue
            single_match_info_dict['support_direction'] += '0'
        print('%s 有支持方向' % match_id)
        coll.update({"match_id": match_id}, {"support_direction": single_match_info_dict['support_direction']})
    else:
        print('%s 的diff都小于0' % match_id)