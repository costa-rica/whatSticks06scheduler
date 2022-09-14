from apscheduler.schedulers.background import BackgroundScheduler
import json
import requests
from datetime import datetime
import os


def scheduler_funct():
    print('* Started Scheduler *')
    scheduler = BackgroundScheduler()
    job_call_wsh_oura_tokens = scheduler.add_job( get_oura_tokens, 'cron', minute = '*', second='35')
    job_call_oura_api = scheduler.add_job( call_oura_api, 'cron', minute = '*', second='45')

    scheduler.start()

    while True:
        pass



#1) scheduler sends call to wsh06 api to get oura ring user tokens
def get_oura_tokens():
    print('sending wsh call for all users oura tokens')
    base_url = 'http://localhost:5000'
    headers = { 'Content-Type': 'application/json'}
    payload = {}
    payload['password'] = 'I<3shoes!m'
    response_oura_tokens = requests.request('GET',base_url + '/oura_tokens', headers=headers, data=str(json.dumps(payload)))
    oura_tokens_dict = json.loads(response_oura_tokens.content.decode('utf-8'))
    response_oura_tokens.status_code

    # now we get the response... let's save it somewhere
    oura_tokens = json.dumps(oura_tokens_dict)

    with open(os.path.join(os.getcwd(), '_oura1_get_oura_tokens.json'), 'w') as outfile:
        json.dump(oura_tokens, outfile)
    
    #once finished call oura api
    call_oura_api()


#2) call Oura Ring api every evening 10pm
def call_oura_api():

    # get oura tokens from os.path.join(os.getcwd(), 'get_oura_tokens.json')
    with open(os.path.join(os.getcwd(), '_oura1_get_oura_tokens.json')) as json_file:
        oura_tokens_dict = json.loads(json.load(json_file))
    
    oura_response_dict = {}
    for user_id, oura_token_list in oura_tokens_dict.get('content').items():
        if len(oura_token_list)==2:# this means there is a token_id and token, otherwise we just received ['User has no Oura token']
            url_sleep='https://api.ouraring.com/v1/sleep?start=2020-03-11&end=2020-03-21?'
            response_sleep = requests.get(url_sleep, headers={"Authorization": "Bearer " + oura_token_list[1]})
            print('--> response_sleep.status_code: ', response_sleep.status_code)
            if response_sleep.status_code ==200:
                sleep_dict = response_sleep.json()
                #add whatSticks token id to dict
                sleep_dict['wsh_oura_token_id'] = oura_token_list[0]
            else:
                sleep_dict = {}
                sleep_dict['wsh_oura_token_id'] = oura_token_list[0]
                sleep_dict['No Oura data reason'] = f'API Status Code: {response_sleep.status_code}'
        else:
            sleep_dict = {}
            sleep_dict['wsh_oura_token_id'] = oura_token_list[0]
            sleep_dict['No Oura data reason'] = 'User has no Oura Ring Token'
        oura_response_dict[user_id] = sleep_dict
    
    oura_sleep_json = json.dumps(oura_response_dict)
    with open(os.path.join(os.getcwd(), '_oura2_call_oura_api.json'), 'w') as outfile:
        json.dump(oura_sleep_json, outfile)
    print('---> json file with oura data successfully written.')

    # send wsh api oura response data
    send_oura_data_to_wsh()


#3) send data to wsh06 api
def send_oura_data_to_wsh():
    
    # get oura response data from os.path.join(os.getcwd(), 'get_oura_tokens.json')
    with open(os.path.join(os.getcwd(), '_oura2_call_oura_api.json')) as json_file:
        oura_response_dict = json.loads(json.load(json_file))
    



#4) send call to wsh06 api to get locations

#3) call weather Api every evning 9pm
#4) send weather data to wsh06 api




if __name__ == '__main__':  
    scheduler_funct()