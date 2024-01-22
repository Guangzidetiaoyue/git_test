import os,json
import gzip,argparse
from collections import defaultdict
import pandas as pd

if __name__ == '__main__':
    file_path = 'sources/CDS.tsv'
    file_path0 = 'sources/verbs.tsv'
    cds_words = []
    verbs_words = []
    with open(file_path, 'r',encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if ":" not in line:
                words_temp = line.strip().split(', ')
                for item in words_temp:
                    if len(item.split(' ')) < 4 and len(item) > 0:
                        cds_words.append(item)
    cds_count = len(cds_words)

    with open(file_path0, 'r',encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if ":" not in line:
                words_temp = line.strip().split(', ')
                for item in words_temp:
                    if len(item.split(' ')) < 4 and len(item) > 0:
                        verbs_words.append(item)
    verbs_count = len(verbs_words)


    print('words done')
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument("--file",default='/data/photonic/reddit_raw_comments/day_ngrams/every_day_ngrams/', help="path")
    cli_parser.add_argument("--language",default='en')
    cli_parser.add_argument("--ngrams",default='3', help="path")
    cli_args = cli_parser.parse_args()
    # language = cli_args.language
    # ngrams = cli_args.ngrams
    words_dict = defaultdict(list)
    for language in ['en']: #, 'ar', 'de', 'fr', 'it', 'ja', 'pt', 'ru'
        for ngrams in ['1', '2', '3']:
            file_path = os.path.join(os.path.join(cli_args.file,language),ngrams+'gramc')
            files = sorted(os.listdir(file_path)) #,reverse=True
            for idx,f in enumerate(files):
                # print(f"开始执行{f}个任务...")
                filepath=os.path.join(file_path,f)
                date_flag = filepath.split('/')[-1].split('.tsv')[0].split('_')[1]
                data_res_temp = {}
                with gzip.open(filepath,'r') as fin:
                    while True:
                        line_b = fin.readline()
                        line = line_b.decode()
                        if not line:
                            break
                        if line.strip().split('\t')[0] == "ngram" and line.strip().split('\t')[1] == 'count' and line.strip().split('\t')[2] == 'rank' and line.strip().split('\t')[3] == 'freq':
                            continue
                        data_original = line.strip().split('\t')
                        word_flag = data_original[0]
                        data_original.append(date_flag)
                        data_res_temp[word_flag] = data_original[1:]
                for cds_item in cds_words:
                    if cds_item in list(data_res_temp.keys()):
                        words_dict[cds_item].append(data_res_temp[cds_item])
                for verb_item in verbs_words:
                    if verb_item in list(data_res_temp.keys()):
                        words_dict[verb_item].append(data_res_temp[verb_item])
                if idx % 100 == 0:
                    print(ngrams+' '+f)
    data_res_str = json.dumps(words_dict, indent=4)
    res_file = 'ngrams_res/ngrams_res.json'
    with open(res_file, 'w') as fr:
        fr.write(data_res_str)