#!/usr/bin/env python3

import re
import os
import json
import requests
import datetime
import argparse

from string import Template
from logger import log
from testscenarios  import TestScenarios
from eosrpcexecutor import EOSRPCExecutor

args        = None

def prepare_scenario_from_pattern_file(_pattern_file):
  try:
    values = prepare_keys_for_test(_pattern_file)
    values.update(prepare_user_for_test(_pattern_file))

    with open(_pattern_file) as pattern_file:
      src = Template(pattern_file.read())
      prepared_scenarios = src.substitute(values)
      with open(os.getcwd()+"/"+"scenarios_continues.json","w") as scenarios:
        scenarios.write(prepared_scenarios)
    return "scenarios_continues.json"
  except Exception as _ex:
    log.error("Exception `%s` occured while preparing scenario file."%_ex)
    return None

def prepare_user_for_test(_pattern_file):
    all_users=[]
    with open(_pattern_file) as pattern_file:
      lines = pattern_file.readlines()
      for line in lines:
        users = re.findall('\$\{(user_.*?)\}', line)
        if users:
          for user in users:
            all_users.append(user)
    all_users = list(set(all_users))
    all_users.sort()
    testers = find_valid_testers_name(all_users)
    log.info("Testers found :%s"%testers)
    return testers

def prepare_keys_for_test(_pattern_file):
    all_keys=[]
    with open(_pattern_file) as pattern_file:
      lines = pattern_file.readlines()
      for line in lines:
        keys = re.findall('\$\{(key.*?)\}', line)
        if keys:
          for key in keys:
            all_keys.append(key)
    all_keys = list(set(all_keys))
    all_keys.sort()
    eos = EOSRPCExecutor(args.nodeos_ip, args.nodeos_port, args.keosd_ip, args.keosd_port, args.master_wallet_name)
    keys = {}
    for key in all_keys:
      keys[key] = eos.create_key()
    log.info("Keys found :%s"%keys)
    return keys 

def find_valid_testers_name(_users):
  accounts      = {}
  base          = "beos"
  separator     = "."
  function      = "tst"
  suffix_base_1 = "a"
  suffix_base_2 = "a"
  suffix_base_3 = "a"
  for user in _users:
    valid = True
    while valid:
      name = base+separator+function+separator+suffix_base_1+suffix_base_2+suffix_base_3
      req = {"account_name":name}
      valid = is_account_valid(req)
      if not valid:
        accounts[user] = name
      if ord(suffix_base_3) == ord('z'): 
        if ord(suffix_base_2)  == ord('z'):
          if ord(suffix_base_1)  == ord('z'):
            log.error("So many test accounts?")
            exit(1)
          else:
            suffix_base_3 = "a"
            suffix_base_2 = "a"
            suffix_base_1 = chr(ord(suffix_base_1)+1)  
        else:
          suffix_base_3 = "a"
          suffix_base_2 = chr(ord(suffix_base_2)+1)
      else:
        suffix_base_3 = chr(ord(suffix_base_3)+1)
  return accounts


def is_account_valid(_request) :
    try:
        request=json.dumps(_request)
        server = "http://%s:%s/v1/beos/address_validator" % (args.nodeos_ip, args.nodeos_port)
        json_rpc_headers = {"content-type": "application/json"}
        response = requests.post( server, data=request, headers=json_rpc_headers )
        response_json = response.json()
        return response_json['is_valid']
    except Exception as _ex:
        log.error("Something goes wrong during account validation.")
        return False


parser = argparse.ArgumentParser()
parser.add_argument('--nodeos-ip', metavar='', help="Ip address of nodeos ", default='127.0.0.1', dest="nodeos_ip")
parser.add_argument('--keosd-ip', metavar='', help="Ip address of keosd", default='127.0.0.1', dest="keosd_ip")
parser.add_argument('--nodeos-port', metavar='', help="Port", default='8888')
parser.add_argument('--keosd-port', metavar='', help="Port", default='8900')
parser.add_argument('--scenario-file-name-pattern', metavar='', help="Path to to scenarios.", default="scenarios_continues.in" )
parser.add_argument('--master-wallet-name', metavar='', help="Name of main wallet.", default="beos_master_wallet" )
parser.add_argument('--add-block-number', action="store_true", help="", default=False )
parser.add_argument('--restore-node-params', action="store_true", help="", default=False )
parser.add_argument('--starting-block-for-initial-witness-election', default=100)
parser.add_argument('--distribution-params', default=[ [7 * 24 * 3600 * 2, 0, 98 * 24 * 3600 * 2, 1 * 3600 * 2, 0], [7 * 24 * 3600 * 2, 0, 280 * 24 * 3600 * 2, 1 * 3600 * 2, 0], 0] )

if __name__ == "__main__":
  args = parser.parse_args()
  try:
    error = False
    scenario_file_name = prepare_scenario_from_pattern_file( os.getcwd()+"/"+args.scenario_file_name_pattern)
    if not scenario_file_name:
      log.error("Wrong scenario generated.")
      exit(1)
    log.info("scenario_file_name %s"%scenario_file_name)
    scenarios = TestScenarios(args.nodeos_ip, args.nodeos_port, args.keosd_ip, args.keosd_port, os.getcwd()+"/"+scenario_file_name, args.add_block_number, args.master_wallet_name)
    log.info("scenarios %s"%scenarios)
    
    for scenario in scenarios:
      scenario.prepare_data()
      scenario.make_scenario_actions()
      scenario.wait_for_end()
      scnenario_error = scenario.get_scenario_summary()
      if scnenario_error:
        error = scnenario_error
  except Exception as _ex:
    log.error("[ERROR] Exeption `%s` occured while executing scenario `%s`."%(str(_ex), scenario.get_current_scenario()))
    error = True
  finally:
    scenarios.stop_scenarios()
    scenarios.add_scenario_status_to_summary_file()
    if args.restore_node_params :
      scenario.restore_node_params(
                args.starting_block_for_initial_witness_election,
                args.distribution_params)

  if error:
    exit(1)
  else:
    exit(0)