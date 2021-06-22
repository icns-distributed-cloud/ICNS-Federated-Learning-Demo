#!/usr/bin/env python3

import argparse
import os
import time
import yaml
import sys
from importlib import import_module

fl_path = os.path.abspath('.')
if fl_path not in sys.path:
    sys.path.append(fl_path)

from backend.constants import GENERATE_CONFIG_DESC, NUM_PARTIES_DESC, \
    PATH_CONFIG_DESC, MODEL_CONFIG_DESC, NEW_DESC, NAME_DESC, \
    FL_EXAMPLES, FL_CONN_TYPES, CONNECTION_TYPE_DESC


def check_valid_folder_structure(p):
    """
    Checks that the folder structure is valid

    :param p: an argument parser
    :type p: argparse.ArgumentParser
    """
    for folder in FL_EXAMPLES:
        if not os.path.isfile(os.path.join("examples", folder, "README.md")) and not os.path.isfile(os.path.join(
                "examples", folder, "generate_configs.py")):
            p.error(
                "Bad folder structure: '{}' directory is missing files.".format(folder))


def setup_parser():
    """
    Sets up the parser for Python script

    :return: a command line parser
    :rtype: argparse.ArgumentParser
    """
    p = argparse.ArgumentParser(description=GENERATE_CONFIG_DESC)
    p.add_argument("--num_parties", "-n", help=NUM_PARTIES_DESC,
                   type=int, required=True)
    p.add_argument("--dataset", "-d",
                   help="Dataset code from examples", type=str, required=True)

    p.add_argument("--data_path", "-p", help=PATH_CONFIG_DESC, required=True)
    p.add_argument("--model", "-m", choices=[os.path.basename(d) for d in FL_EXAMPLES],
                   help=MODEL_CONFIG_DESC, required=True)
    p.add_argument("--create_new", "-new", action="store_true", help=NEW_DESC)
    p.add_argument("--name", help=NAME_DESC)
    p.add_argument("--connection", "-c", choices=[os.path.basename(
        d) for d in FL_CONN_TYPES], help=CONNECTION_TYPE_DESC, required=False, default="flask")
    p.add_argument("--lossfunc", "-lf",  help="loss function")
    p.add_argument("--trainround", "-tr",  help="number of aggregating party's para")
    p.add_argument("--lipaddress", "-lip",  nargs = '*', help="number of party's ip")
    
    return p


def generate_connection_config(conn_type, party_ip="", party_id=0, is_party=False):
    connection = {}
    ip_port = []

    if party_ip:
        ip_port = party_ip.split(":")

    if conn_type == 'flask':
        tls_config = {
            'enable': False
        }
        connection = {
            'name': 'FlaskConnection',
            'path': 'ibmfl.connection.flask_connection',
            'sync': False
        }
        if is_party:
            # e = party_ip.split(":")
            connection['info'] = {
                'ip': '127.0.0.1',
                'port': 8085 + party_id
                # 'ip': e[0],
                # 'port': e[1]
            }
        else:
            connection['info'] = {
                'ip': '127.0.0.1',
                'port': 5000
            }
        connection['info']['tls_config'] = tls_config
    

    return connection


def get_aggregator_info(conn_type):

    if conn_type == 'flask':
        aggregator = {
            'ip': '127.0.0.1',
            'port': 5000
        }
    else:
        aggregator = {}

    return aggregator


def generate_ph_config(conn_type, is_party=False):

    if is_party:
        protocol_handler = {
            'name': 'PartyProtocolHandler',
            'path': 'ibmfl.party.party_protocol_handler'
        }
    else:
        protocol_handler = {
            'name': 'ProtoHandler',
            'path': 'ibmfl.aggregator.protohandler.proto_handler'
        }

     
    return protocol_handler


def generate_fusion_config(module):
    gen_fusion_config = getattr(module, 'get_fusion_config')
    
    return gen_fusion_config()
    

def generate_hp_config(module, num_parties, train_round):
    gen_hp_config = getattr(module, 'get_hyperparams')
    hp = gen_hp_config()
    hp['global']['parties'] = num_parties
    hp['global']['round'] = train_round

    return hp


def generate_model_config(module, folder_configs, dataset, loss_func, is_agg=False, party_id=0):
    get_model_config = getattr(module, 'get_model_config')
    model = get_model_config(folder_configs, dataset, loss_func, is_agg, party_id)

    return model


def generate_lt_config(module,  keys, party_id=None):
    get_local_training_config = getattr(module, 'get_local_training_config')
    lt = get_local_training_config()

    return lt


def generate_datahandler_config(module, party_id, dataset, folder_data, is_agg=False):

    get_data_handler_config = getattr(module, 'get_data_handler_config')
    dh = get_data_handler_config(party_id, dataset, folder_data, is_agg)

    return dh


def generate_agg_config(module, ips, num_parties, conn_type, dataset, folder_data, 
                        folder_configs, train_round, loss_func, keys):

    if not os.path.exists(folder_configs):
        os.makedirs(folder_configs)
    config_file = os.path.join(folder_configs, 'config_agg.yml')

    content = {
        'connection': generate_connection_config(conn_type),
        'fusion': generate_fusion_config(module),
        'hyperparams': generate_hp_config(module, num_parties, train_round),
        'protocol_handler': generate_ph_config(conn_type)
    }

    model = generate_model_config(module, folder_configs, dataset, loss_func, True)
    data = generate_datahandler_config(
        module, 0, dataset, folder_data, True)
    if model:
        content['model'] = model
    if data:
        content['data'] = data
    with open(config_file, 'w') as outfile:
        yaml.dump(content, outfile)

    print('Finished generating config file for aggregator. Files can be found in: ',
          os.path.abspath(os.path.join(folder_configs, 'config_agg.yml')))


def generate_party_config(module, ips, num_parties, conn_type, dataset, folder_data, 
                            folder_configs, loss_func, keys):

    for i in range(num_parties):
        config_file = os.path.join(
            folder_configs, 'config_party' + str(i) + '.yml')


        lh = generate_lt_config(module, None, party_id=i)
        

        content = {
            'connection': generate_connection_config(conn_type, ips[i], i, True),
            'data': generate_datahandler_config(module, i, dataset, folder_data),
            'model': generate_model_config(module, folder_configs, dataset, loss_func, party_id=i),
            'protocol_handler': generate_ph_config(conn_type, True),
            'local_training': lh,
            'aggregator': get_aggregator_info(conn_type)
        }

        with open(config_file, 'w') as outfile:
            yaml.dump(content, outfile)

    print('Finished generating config file for parties. Files can be found in: ',
          os.path.abspath(os.path.join(folder_configs, 'config_party*.yml')))


if __name__ == '__main__':
    # Parse command line options
    parser = setup_parser()
    args = parser.parse_args()
    # check_valid_folder_structure(parser)

    # Collect arguments
    num_parties = args.num_parties
    dataset = args.dataset
    party_data_path = args.data_path
    model = args.model
    create_new = args.create_new
    exp_name = args.name
    conn_type = args.connection
    loss_func = args.lossfunc
    train_round = args.trainround
    ips = args.lipaddress
    

    # Create folder to save configs
    folder_configs = os.path.join("backend", "configs")

    if create_new:
        folder_configs = os.path.join(
            folder_configs, exp_name if exp_name else str(int(time.time())))
    else:
        folder_configs = os.path.join(folder_configs, model)

    # Import and run generate_configs.py
    config_model = import_module('backend.{}.generate_configs'.format(model))

    


    generate_agg_config(config_model, ips, num_parties, conn_type,
                        dataset, party_data_path, folder_configs, train_round, loss_func,
                        None)
    generate_party_config(config_model, ips, num_parties, conn_type,
                          dataset, party_data_path, folder_configs, loss_func,
                          None)

