import requests
import json
import argparse
import os
from os import listdir
from os.path import isfile, isdir, join
from os import walk
import time
import csv
import sys

# 可以拿到file的id
def upload_file(file_path,key):
    url = "https://www.virustotal.com/api/v3/files"
    files = { "file": (file_path, open(file_path, "rb"), "application/octet-stream") }
    headers = {
        "accept": "application/json",
        "x-apikey": key
    }
    response = requests.post(url, files=files, headers=headers)
    return response.json()['data']['id']

# 從file的id拿file的hash
def get_hash(file_id,key):
    url = f'https://www.virustotal.com/api/v3/analyses/{file_id}'
    headers = {
        'x-apikey': key
    }
    response = requests.get(url, headers=headers)
    return response.json()['meta']['file_info']['md5']

# 從file的hash拿file的json report
def get_json_report(file_name,hash_value,output_dir,key):
    url = f'https://www.virustotal.com/api/v3/files/{hash_value}'
    headers = {
        "accept": "application/json",
        "x-apikey": key
    }
    response = requests.get(url, headers=headers)
    json_response = json.loads(response.text)
    with open(output_dir+file_name+".json", "w") as outfile:
        json.dump(json_response, outfile)

def write_csv(json_file_path,output_dir):
    os.system("avclass -f " + json_file_path + " -o avclassOutput.txt")
    with open('avclassOutput.txt', 'r') as text_file, open(os.path.join(output_dir,"avclassOutput.csv"), 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        for line in text_file:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                if 'SINGLETON' in parts[1]:
                    parts[1] = -1
                hash_value, family = parts
                csv_writer.writerow([hash_value, family])



def get_parser():
    parser = argparse.ArgumentParser(description = "Analysis Malware")
    parser.add_argument("-i", "--input", type = str, help = "Enter file directory path") #/home/weiren/VTandAVClass/example/
    parser.add_argument("-j", "--json_output", type = str, help = "Enter Json File path") #/home/weiren/VTandAVClass/json_dir/
    parser.add_argument("-o", "--output", type = str, help = "Enter destination path") #/home/weiren/VTandAVClass/
    parser.add_argument("-k","--key", type = str, help = "Enter Your API Key") #108695ad3a0121db1677911189d62b37388b3bb7ce51f9924a98e175e6fa51a9
    return parser

if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    files_dir = args.input
    json_file_dir = args.json_output
    output_dir = args.output
    key = args.key
    count = 0
    
    for root, dirs, files in walk(files_dir):
        for f in files:
            fullpath = join(root, f)
            f = f.split('.')[0]
            if os.path.exists(os.path.join(json_file_dir,f+'.json')):
                print(f,' is been analysed')
                continue
            print('Analysing ',f,'...')

            error_count = 0
            have_done = False
            while error_count < 10 and have_done == False:
                try:
                    file_id = upload_file(fullpath, key)
                    file_hash = get_hash(file_id, key)
                    get_json_report(f, file_hash, json_file_dir, key)
                    write_csv(os.path.join(json_file_dir, f + '.json'), output_dir)
                    have_done = True
                    time.sleep(32)
                except:
                    error_count += 1
                    if error_count >= 5:
                        print("可能已達每日使用量")
                        sys.exit()
                    else:
                        time.sleep(30)
            print(count)
            count+=1