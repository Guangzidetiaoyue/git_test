from flask import Flask, render_template, request, jsonify
import pymysql,pymongo
app = Flask(__name__)
@app.route("/")
def my_echart():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    dblist = myclient.list_database_names()
    mydb = myclient["zoujj"]
    my_collection = mydb['ngrams0815']
    
    word_query = 'cs'
    
    data_temp = my_collection.find_one({'words':word_query})
    dates = list(data_temp['data']['dates'].values())
    # dates = [i for i in range(len(data_temp['data']['dates']))]
    count = list(data_temp['data']['count'].values())
    rank = list(data_temp['data']['rank'].values())
    freq = list(data_temp['data']['freq'].values())
    count_test = [[dates[i],count[i]] for i in range(len(data_temp['data']['dates']))]
    rank_test = [[dates[i],int(float(rank[i]))] for i in range(len(data_temp['data']['dates']))]
    freq_test = [[dates[i],freq[i]] for i in range(len(data_temp['data']['dates']))]
#     data_test = [
#   ['2006-01-01', '4'],
#   ['2007-01-01', '100'],
#   ['2007-01-09', '110'],
#   ['2008-01-01', '200']
#   ]
    return render_template('test.html',word_query = word_query,dates=dates,count_test=count_test,rank_test=rank_test,freq_test=freq_test) #先引入bar.html，同时根据后面传入的参数，对html进行修改渲染
    # return render_template('area-time-axis.html')
# @app.route("/ajax", methods=["POST"])
# def ajax():
#     data = request.get_json()
#     result = data["number"] * 2
#     return jsonify(result=result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)#启用调试模式
