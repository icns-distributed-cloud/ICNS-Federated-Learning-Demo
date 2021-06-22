from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import time
import pexpect
import sys
import json
import re

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route('/api/fl_process')
def fl_process():
    args = request.args
    fl_path = os.path.abspath('.')

    model = "keras_classifier" if args.get('model') == "CNN" \
            else "sklearn_logclassification"

    num_parties = args.get('client_num')
    dataset = args.get('dataset')
    loss_func = args.get('loss_func')
    train_round = args.get('train_round')
    list_ipaddress = json.loads(args.get('list_ipaddr'))
    data_path = fl_path + f"/backend/data/{dataset}/random"

    # create configs
    ips = " ".join(list_ipaddress['lipaddr'])
    pexpect.run(f"python {fl_path}/backend/generate_configs.py -m {model} \
                -n {num_parties} -d {dataset} -p {data_path} -lf {loss_func} \
                -tr {train_round} -lip {ips}")
                
    

    # start aggregator
    p_agg = pexpect.spawn(f"python -m ibmfl.aggregator.aggregator {fl_path}/backend/configs/{model}/config_agg.yml", 
                            encoding='utf-8')
    p_agg.logfile = sys.stdout
    p_agg.expect(".*Aggregator initialization.*", timeout=3600)
    p_agg.sendline("\nSTART \n")
    p_agg.expect(".*Aggregator start successful.*", timeout=3600)
    print(p_agg.before)

    p_parties = [pexpect.spawn(f'python -m ibmfl.party.party {fl_path}/backend/configs/{model}/config_party{i}.yml', 
                                encoding='utf-8') for i in range(int(num_parties))]
    # start a party and register
    for i in range(int(num_parties)):
        p_parties[i].logfile = sys.stdout
        p_parties[i].logfile = open(f"/tmp/mylog{i}", "w")
        p_parties[i].expect(".*Party initialization successful.*", timeout=3600)
        p_parties[i].sendline("\nSTART\n")
        p_parties[i].expect(".*Running on.*", timeout=3600)
        p_parties[i].sendline("\nREGISTER\n")
        p_parties[i].expect(".*Registration Successful.*", timeout=3600)
        print(p_parties[i].before)
    
    # start train
    p_agg.expect(".*200 -.*")
    p_agg.sendline("\nTRAIN\n")
    p_agg.expect(".*Finished Global Training.*", timeout=3600)

    # sync global model to parties
    p_agg.sendline("\nSYNC\n")
    p_agg.expect(".*Finished sync model requests.*", timeout=3600)

    # party eval result
    for i in range(int(num_parties)):
        if model == "keras_classifier":
            # p_parties[i].logfile = sys.stdout
            p_parties[i].logfile = open(f"/tmp/mylog{i}", "w")
            p_parties[i].expect(".*200 -.*", timeout=3600)
            p_parties[i].sendline("\nEVAL\n")
            p_parties[i].expect(".*recall.*", timeout=3600)
            p_parties[i].sendline("\n")
            p_parties[i].expect(".*loss.*", timeout=3600)
        else:
            # p_parties[i].logfile = sys.stdout
            p_parties[i].logfile = open(f"/tmp/mylog{i}", "w")
            p_parties[i].expect(".*200 -.*", timeout=3600)
            p_parties[i].sendline("\nEVAL\n")
            p_parties[i].expect(".*negative log.*", timeout=3600)
            # p_parties[i].sendline("\n")
            # p_parties[i].expect(".*loss.*", timeout=3600)

    # save model to parties
    p_agg.sendline("\nSAVE\n")
    p_agg.expect(".*Finished save requests.*", timeout=3600)

    # close aggregator and parties
    for i in range(int(num_parties)):
        p_parties[i].close()
    p_agg.close()


    response = {}
    for i in range(int(num_parties)):
        with open(f'/tmp/mylog{i}', 'r') as f:
            content = f.read()
            match_acc = re.search('acc(.+?)\,', content)
            match_loss = re.search('loss(.+?)\,', content) if model == "keras_classifier" \
                        else re.search('negative log(.+?)\}', content)
            fs_acc = match_acc.group(1) if match_acc else ""
            fs_loss = match_loss.group(1) if match_loss else ""
            loss = fs_loss.split(":")[1]
            acc = fs_acc.split(":")[1]
            f_loss = loss.split(".")[0] + "." + loss.split(".")[1][:3]
            f_acc = acc.split(".")[0] + "." + acc.split(".")[1][:3]
            response[i] = [f_loss, f_acc]
    print("result ", response)

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5050)

    




    











    

    


    
        
    
    
    
    
    