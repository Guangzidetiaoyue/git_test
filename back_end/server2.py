import pymongo

from flask import Flask, render_template, request
from flask_caching import Cache
from utils import rank_turbulence_divergence, get_date_index

config={     
    "CACHE_TYPE": "FileSystemCache",    # 缓存类型
    "CACHE_DIR": "./cache"
}

# app
app = Flask(__name__)

# cache
cache=Cache(app=app,config=config)

# db
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["zoujj"]
collection = db['ngrams0815']

# find collection
def find_by_date(date):
    words = {}
    result = collection.find({ f"data.count.{date}": {"$exists": True} }, {"words": 1, f"data.count.{date}": 1, "_id": 0})
    for item in result:
        words[item['words']] = int(item["data"]["count"][str(date)])
    return words

def find_by_word(word):
    data_temp = collection.find_one({'words': word}, {"words": 1, "data.count": 1, "data.dates": 1, "data.rank":1, "_id": 0})
    if data_temp is None:
        return None, None
    dates = list(data_temp['data']['dates'].values())
    count = list(data_temp['data']['count'].values())
    rank = list(data_temp['data']['rank'].values())
    # freq = list(data_temp['data']['freq'].values())
    
    count_test = [[dates[i],count[i]] for i in range(len(data_temp['data']['dates']))]
    rank_test = [[dates[i],int(float(rank[i]))] for i in range(len(data_temp['data']['dates']))]
    # freq_test = [[dates[i],freq[i]] for i in range(len(data_temp['data']['dates']))]
    
    return count_test, rank_test

def get_hot_words(start, end, alpha=1/3, topK=30):
    words1 = find_by_date(start)
    words2 = find_by_date(end)
    hot1, hot2 = rank_turbulence_divergence(words1, words2, alpha, topK)
    
    return hot1, hot2


def get_render_data(start_date, end_date):
    start = get_date_index(start_date)
    end = get_date_index(end_date)

    # hot words
    start_hot, end_hot = get_hot_words(start, end)

    # words
    start_series = []
    end_seris = []
    for i in range(3):
        start_word = start_hot[i]['name']
        end_word = end_hot[i]['name']
        start_count, start_rank = find_by_word(start_word)
        end_count, end_rank = find_by_word(end_word)
        # start_words.append(start_word)
        # end_words.append(end_word)
        # start_counts.append(start_count)
        # end_counts.append(end_count)
        start_series.append({
            'name': start_word,
            'type': 'line',
            'smooth': True,
            'symbol': 'none',
            'data': start_rank
        })
        end_seris.append({
            'name': end_word,
            'type': 'line',
            'smooth': True,
            'symbol': 'none',
            'data': end_rank
        })
    context = {
        'startDate': start_date,
        'endDate': end_date,
        'startHot': start_hot,
        'endHot': end_hot,
        'startData': start_series,
        'endData': end_seris
    }

    cache.set("startDate", start_date, timeout=None)
    cache.set("endDate", end_date, timeout=None)
    cache.set("startHot", start_hot, timeout=None)
    cache.set("endHot", end_hot, timeout=None)

    return context

# 按日期查看热点词
@app.route("/", methods=['POST','GET'])
def echart_show():
    if request.method == "GET":
        # date
        start_date = "2008-01-01"
        end_date = "2008-01-08"
        context = get_render_data(start_date, end_date)
        
        return render_template("index.html", **context)
    else:
        if 'keyword' in request.form:
            keywords = request.form.get('keyword')
            keywords = keywords.split()

            count_series = []
            rank_series = []
            for word in keywords:
                word_count, word_rank = find_by_word(word)
                if word_count is None and word_rank is None:
                    continue
                count_series.append({
                    'name': word,
                    'type': 'line',
                    'smooth': True,
                    'symbol': 'none',
                    'data': word_count
                })
                rank_series.append({
                    'name': word,
                    'type': 'line',
                    'smooth': True,
                    'symbol': 'none',
                    'data': word_rank
                })
            context = {
                'startDate': cache.get('startDate'),
                'endDate': cache.get('endDate'),
                'startHot': cache.get('startHot'),
                'endHot': cache.get('endHot'),
                'wordCount': count_series,
                'wordRank': rank_series
            }
            return render_template("search.html", **context)
        else:
            daterange = request.form.get('daterange')
            start_date, end_date = daterange.split(" - ")
            context = get_render_data(start_date, end_date)
            return render_template("index.html", **context)

if __name__ == '__main__':
    # app.run(debug=True)#启用调试模式
    app.run(host='0.0.0.0', port=5050)