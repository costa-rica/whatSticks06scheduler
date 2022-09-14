from apscheduler.schedulers.background import BackgroundScheduler
import json
import requests
from datetime import datetime, timedelta
import os
from wsh_config import ConfigDev


config = ConfigDev()


def scheduler_funct():
    print('* Started Scheduler *')
    scheduler = BackgroundScheduler()
    # job_call_wsh_oura_tokens = scheduler.add_job( get_oura_tokens, 'cron', minute = '*', second='35')
    # job_call_oura_api = scheduler.add_job( call_oura_api, 'cron', minute = '*', second='45')
    job_call_get_locations = scheduler.add_job(get_locations, 'cron', minute = '*', second = '25')

    scheduler.start()

    while True:
        pass



#1) scheduler sends call to wsh06 api to get oura ring user tokens
def get_oura_tokens():
    print('sending wsh call for all users oura tokens')
    base_url = 'http://localhost:5000'
    headers = { 'Content-Type': 'application/json'}
    payload = {}
    payload['password'] = config.MAIL_PASSWORD
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
    
    base_url = 'http://localhost:5000'
    headers = { 'Content-Type': 'application/json'}
    payload = {}
    payload['password'] = config.MAIL_PASSWORD
    payload['oura_response_dict'] = oura_response_dict
    response_oura_tokens = requests.request('GET',base_url + '/receive_oura_data', headers=headers, data=str(json.dumps(payload)))
    oura_tokens_dict = json.loads(response_oura_tokens.content.decode('utf-8'))
    response_oura_tokens.status_code

    print('oura_tokens_dict: ')
    print(oura_tokens_dict)


#4) send call to wsh06 api to get locations
def get_locations():
    print('sending wsh call for all locations')
    base_url = 'http://localhost:5000'
    headers = { 'Content-Type': 'application/json'}
    payload = {}
    payload['password'] = config.MAIL_PASSWORD
    response_oura_tokens = requests.request('GET',base_url + '/get_locations',
        headers=headers, data=str(json.dumps(payload)))
    oura_tokens_dict = json.loads(response_oura_tokens.content.decode('utf-8'))
    
    print('API call response code: ', response_oura_tokens.status_code)

    if response_oura_tokens.status_code == 200:
        try:
            # now we get the response... let's save it somewhere
            oura_tokens = json.dumps(oura_tokens_dict)

            with open(os.path.join(os.getcwd(), '_locations1_get_locations.json'), 'w') as outfile:
                json.dump(oura_tokens, outfile)
        
            print(f'Locations succesfully saved in {os.path.join(os.getcwd(), "_locations1_get_locations.json")}')
        except:
            print('There was a problem with the response')
    else:
        print(f'Call not succesful. Status code: ', response_oura_tokens.status_code)
    
    call_weather_api()

#3) call weather Api every evning 9pm
def call_weather_api():
    print('--- In call_weather_api() of scheduler.py----')
    with open(os.path.join(os.getcwd(), '_locations1_get_locations.json')) as json_file:
        locations_dict = json.loads(json.load(json_file))
        #locatinos_dict = {loc_id: [lat, lon]}

    # weather_dict = {}
    # #1) Loop through dictionary
    # for loc_id, coords in locations_dict.items():
    #     location_coords = f"{coords[0]}, {coords[1]}"
    #     api_token = config.WEATHER_API_KEY
    #     base_url = 'http://api.weatherapi.com/v1'
    #     history = '/history.json'
    #     payload = {}
    #     payload['q'] = location_coords
    #     payload['key'] = api_token
    #     yesterday = datetime.today() - timedelta(days=1)
    #     payload['dt'] = yesterday.strftime('%Y-%m-%d')
    #     payload['hour'] = 0
    #     try:
    #         r_history = requests.get(base_url + history, params = payload)
            
    #         if r_history.status_code == 200:
            
    #             #2) for each id call weather api
    #             weather_dict[loc_id] = r_history.json()
    #         else:
    #             weather_dict[loc_id] = f'Problem connecting with Weather API. Response code: {r_history.status_code}'
    #     except:
    #         weather_dict[loc_id] = 'Error making call to Weather API. No response.'
    
    # #3) put response in  a json
    # weather_dict_json = json.dumps(weather_dict)
    # with open(os.path.join(os.getcwd(), '_locations2_call_weather_api.json'), 'w') as outfile:
    #     json.dump(weather_dict_json, outfile)
    # print('---> json file with oura data successfully written.')

    send_weather_data_to_wsh()
    

#4) send weather data to wsh06 api
def send_weather_data_to_wsh():
    print('--- In send_weather_data_to_wsh() of scheduler.py----')
    # get oura response data from os.path.join(os.getcwd(), 'get_oura_tokens.json')
    with open(os.path.join(os.getcwd(), '_locations2_call_weather_api.json')) as json_file:
        weather_response_dict = json.loads(json.load(json_file))
    
    base_url = 'http://localhost:5000'
    headers = { 'Content-Type': 'application/json'}
    payload = {}
    payload['password'] = config.MAIL_PASSWORD
    payload['weather_response_dict'] = weather_response_dict
    response_wsh_weather = requests.request('GET',base_url + '/receive_weather_data', 
        headers=headers, data=str(json.dumps(payload)))
    # oura_tokens_dict = json.loads(response_oura_tokens.content.decode('utf-8'))
    response_wsh_weather.status_code

    # print('oura_tokens_dict: ')
    # print(oura_tokens_dict)



if __name__ == '__main__':  
    scheduler_funct()