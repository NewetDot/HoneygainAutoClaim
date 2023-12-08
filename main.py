#!/usr/bin/env python3
import configparser
import json
import logging
from colorama import just_fix_windows_console, Back, Style, Fore
import os
from configparser import ConfigParser
from getpass import getpass

import requests
from requests import Response

# path to the token file
config_folder: str = 'Config'
token_file: str = f'{config_folder}/HoneygainToken.json'
config_path: str = f'{config_folder}/HoneygainConfig.toml'

header: dict[str, str] = {'Authorization': ''}

config: ConfigParser = ConfigParser()
config.read(config_path)

is_jwt = config.get('User', 'IsJWT', fallback='0')

if is_jwt == '1':
    os.environ['IsJWT'] = '1'

# Creates a Log
if not os.path.exists('Logs'):
    os.mkdir('Logs')
logging.basicConfig(filename='Logs/HoneygainAutoClaim.log', filemode='w', encoding='utf-8', level=logging.INFO,
                    format='%(levelname)s ' '%(asctime)s ' '%(message)s', datefmt='%d/%m/%Y %H:%M:%S')

# Initialize Colorama for colored logging
just_fix_windows_console()

# Create a StreamHandler for printing logs to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Add the console handler to the root logger
logging.getLogger().addHandler(console_handler)


logging.info(Fore.LIGHTWHITE_EX + "Started HoneygainAutoClaim!")

if os.getenv('GITHUB_ACTIONS') == 'true':
    user_repo = os.getenv('GITHUB_REPOSITORY')
    original_repo = 'MrLoLf/HoneygainAutoClaim'
    user_url = f'https://api.github.com/repos/{user_repo}/commits/main'
    original_url = f'https://api.github.com/repos/{original_repo}/commits/main'
    user_response = requests.get(user_url)
    original_response = requests.get(original_url)
    if user_response.status_code == 200 and original_response.status_code == 200:
        user_commit = user_response.json()['sha']
        original_commit = original_response.json()['sha']
        if user_commit == original_commit:
            logging.info(Fore.LIGHTWHITE_EX + 'Your repo is up-to-date with the original repo')
        else:
            logging.warning(Fore.LIGHTYELLOW_EX + 'Your repo is not up-to-date with the original repo')
            logging.warning(Fore.LIGHTYELLOW_EX + 'Please update your repo to the latest commit to get new updates and '
                                                  'bug fixes')
    else:
        logging.error(Fore.LIGHTRED_EX + 'Failed to fetch commit information')


def create_config() -> None:
    """
    Creates a config with default values.
    """
    logging.warning(Fore.LIGHTYELLOW_EX + 'Generating new Config.')
    cfg: ConfigParser = ConfigParser()

    cfg.add_section('User')
    if os.getenv('GITHUB_ACTIONS') == 'true':
        if os.getenv('IsJWT') == '1':
            token = os.getenv('JWT_TOKEN')
            cfg.set('User', 'token', f"{token}")
        else:
            email = os.getenv('MAIL')
            password = os.getenv('PASS')
            cfg.set('User', 'email', f"{email}")
            cfg.set('User', 'password', f"{password}")
    else:
        logging.info(Fore.LIGHTYELLOW_EX + "Please choose authentication method:")
        logging.info(Fore.LIGHTYELLOW_EX + "1. Using Token")
        logging.info(Fore.LIGHTYELLOW_EX + "2. Using Email and Password")

        choice = input(Fore.LIGHTYELLOW_EX + "Enter your choice (1 or 2): ")
        if choice == '1':
            token = input(Fore.LIGHTYELLOW_EX + "Token: ")
            cfg.set('User', 'token', f"{token}")
            cfg.set('User', 'IsJWT', '1')
            os.environ['IsJWT'] = '1'
        elif choice == '2':
            email = input(Fore.LIGHTYELLOW_EX + "Email: ")
            password = getpass(Fore.LIGHTYELLOW_EX + "Password: ")
            cfg.set('User', 'email', f"{email}")
            cfg.set('User', 'password', f"{password}")
            cfg.set('User', 'IsJWT', '0')
        else:
            logging.error(Fore.LIGHTRED_EX + "Wrong Input could not read it correctly. Try again!")
            create_config()

    cfg.add_section('Settings')
    cfg.set('Settings', 'Lucky Pot', 'True')
    cfg.set('Settings', 'Achievements', 'True')

    cfg.add_section('Url')
    cfg.set('Url', 'login', 'https://dashboard.honeygain.com/api/v1/users/tokens')
    cfg.set('Url', 'pot', 'https://dashboard.honeygain.com/api/v1/contest_winnings')
    cfg.set('Url', 'balance', 'https://dashboard.honeygain.com/api/v1/users/balances')
    cfg.set('Url', 'achievements', 'https://dashboard.honeygain.com/api/v1/achievements/')
    cfg.set('Url', 'achievement_claim', 'https://dashboard.honeygain.com/api/v1/achievements/claim')

    with open(config_path, 'w') as configfile:
        configfile.truncate(0)
        configfile.seek(0)
        cfg.write(configfile)


def get_urls(cfg: ConfigParser) -> dict[str, str]:
    """
    :param cfg: config object that contains the config
    :return: a dictionary with all urls of the config
    """
    urls_conf: dict[str, str] = {}
    try:
        urls_conf: dict[str, str] = {'login': cfg.get('Url', 'login'),
                                     'pot': cfg.get('Url', 'pot'),
                                     'balance': cfg.get('Url', 'balance'),
                                     'achievements': cfg.get('Url', 'achievements'),
                                     'achievement_claim': cfg.get('Url', 'achievement_claim')}
    except configparser.NoOptionError or configparser.NoSectionError:
        create_config()
    return urls_conf


def get_login(cfg: ConfigParser) -> dict[str, str]:
    """
        :param cfg: config object that contains the config
        :return: a dictionary with all user information of the config
        """
    user: dict[str, str] = {}
    try:
        if os.getenv('IsJWT') == '1':
            token = cfg.get('User', 'token')
            user: dict[str, str] = {'token': token}
        else:
            user: dict[str, str] = {'email': cfg.get('User', 'email'),
                                    'password': cfg.get('User', 'password')}
    except configparser.NoOptionError or configparser.NoSectionError:
        create_config()
    return user


def get_settings(cfg: ConfigParser) -> dict[str, bool]:
    """
        :param cfg: config object that contains the config
        :return: a dictionary with all settings of the config
        """
    settings_dict: dict[str, bool] = {}
    try:
        settings_dict: dict[str, bool] = {'lucky_pot': cfg.getboolean('Settings', 'Lucky Pot'),
                                          'achievements_bool': cfg.getboolean('Settings', 'Achievements')}
    except configparser.NoOptionError or configparser.NoSectionError:
        create_config()
    return settings_dict


if not os.path.exists(config_folder):
    logging.warning(Fore.LIGHTYELLOW_EX + 'Creating config folder!')
    os.mkdir(config_folder)

if not os.path.isfile(config_path) or os.stat(config_path).st_size == 0:
    create_config()

config: ConfigParser = ConfigParser()
config.read(config_path)

if not config.has_section('User') or not config.has_section('Settings') or not config.has_section('Url'):
    create_config()

try:
    # settings
    settings: dict[str, bool] = get_settings(config)
    # urls
    urls: dict[str, str] = get_urls(config)
    # user credentials
    payload: dict[str, str] = get_login(config)
except configparser.NoOptionError or configparser.NoSectionError:
    """
    creating a new config if the there were some changes in the config file
    """
    create_config()
    # settings
    settings: dict[str, bool] = get_settings(config)
    # urls
    urls: dict[str, str] = get_urls(config)
    # user credentials
    payload: dict[str, str] = get_login(config)


def login(s: requests.session) -> json.loads:
    """
    Gets the new token with login data.
    :param s: currently used session
    :return: json containing the new token
    """
    logging.warning(Fore.LIGHTYELLOW_EX + 'Logging in to Honeygain!')

    if os.getenv('IsJWT') == '1':
        return {'data': {'access_token': payload['token']}}
    token: Response = s.post(urls['login'], json=payload)
    try:
        return json.loads(token.text)
    except json.decoder.JSONDecodeError:
        logging.error(Fore.LIGHTRED_EX + 'You have exceeded your login tries.\n\nPlease wait a few hours or return '
                                         'tomorrow.')
        exit(-1)


def gen_token(s: requests.session, invalid: bool = False) -> str | None:
    """
    Gets the token from the HoneygainToken.json if existent and valid, if not generates a new one.
    :param s: currently used session
    :param invalid: true if the token read before was invalid
    :return: string containing the token
    """
    # creating token.json if not existent
    if not os.path.isfile(token_file) or os.stat(token_file).st_size == 0 or invalid:
        logging.warning(Fore.LIGHTYELLOW_EX + 'Generating new Token!')

        # generating new token if the file is empty or is invalid
        with open(token_file, 'w') as f:
            # remove what ever was in the file and jump to the beginning
            f.truncate(0)
            f.seek(0)

            # get json and write it to the file
            token: dict = login(s)

            # check if token is valid and doesn't have false credentials in it.
            if "title" in token:
                logging.error(Fore.LIGHTRED_EX + "Wrong Login Credentials. Please enter the right ones.")
                return None
            json.dump(token, f)

    # reading the token from the file
    with open(token_file, 'r+') as f:
        token: dict = json.load(f)

    # get the token
    return token["data"]["access_token"]


def achievements_claim(s: requests.session) -> bool:
    """
    function to claim achievements
    """
    # to use the same header as defined earlier
    global header
    if settings['achievements_bool']:

        # get all achievements
        achievements: Response = s.get(urls['achievements'], headers=header)
        achievements: dict = achievements.json()

        # Loop over all achievements and claim them, if completed.
        try:
            for achievement in achievements['data']:
                try:
                    if not achievement['is_claimed'] and achievement['progresses'][0]['current_progress'] == \
                            achievement['progresses'][0]['total_progress']:
                        s.post(urls['achievement_claim'], json={"user_achievement_id": achievement['id']},
                               headers=header)
                        logging.info(Fore.LIGHTWHITE_EX + f'Claimed {achievement["title"]}.')
                except IndexError:
                    if not achievement['is_claimed']:
                        s.post(urls['achievement_claim'], json={"user_achievement_id": achievement['id']},
                               headers=header)
                        logging.info(Fore.LIGHTWHITE_EX + f'Claimed {achievement["title"]}.')
        except KeyError:
            if 'message' in achievements:
                token: str = gen_token(s, True)

                if token is None:
                    logging.info(Fore.LIGHTWHITE_EX + "Closing HoneygainAutoClaim! Due to false login Credentials.")
                    exit(-1)

                # header for all further requests
                header = {'Authorization': f'Bearer {token}'}
            return False
        return True


def main() -> None:
    """
    Automatically claims the Lucky pot and prints out current stats.
    """
    global header
    # starting a new session
    with requests.session() as s:
        token: str = gen_token(s)

        if token is None:
            logging.info(Fore.LIGHTWHITE_EX + "Closing HoneygainAutoClaim! Due to false login Credentials.")
            exit(-1)

        # header for all further requests
        header = {'Authorization': f'Bearer {token}'}

        if not achievements_claim(s):
            logging.error(Fore.LIGHTRED_EX + 'Failed to claim achievements.')

        # check if the token is valid by trying to get the current balance with it
        dashboard: Response = s.get(urls['balance'], headers=header)
        dashboard: dict = dashboard.json()
        if 'code' in dashboard and dashboard['code'] == 401:
            logging.error(Fore.LIGHTRED_EX + 'Invalid token generating new one.')
            token: str = gen_token(s, True)
            header['Authorization'] = f'Bearer {token}'

        # gets the pot winning credits
        pot_winning: Response = s.get(urls['pot'], headers=header)
        pot_winning: dict = pot_winning.json()

        if settings['lucky_pot'] and pot_winning['data']['winning_credits'] is None:
            # The post below sends the request, so that the pot claim gets made
            pot_claim: Response = s.post(urls['pot'], headers=header)
            pot_claim: dict = pot_claim.json()
            if 'type' in pot_claim and pot_claim['type'] == 400:
                logging.error(Fore.LIGHTRED_EX + 'You don\'t have enough traffic shared yet to claim you reward. '
                                                 'Please try again later.')
                return

            logging.info(Fore.LIGHTWHITE_EX + f'Claimed {pot_claim["data"]["credits"]} Credits.')

        # gets the pot winning credits
        pot_winning: Response = s.get(urls['pot'], headers=header)
        pot_winning: dict = pot_winning.json()
        logging.info(Fore.LIGHTWHITE_EX + f'Won today {pot_winning["data"]["winning_credits"]} Credits.')

        # gets the current balance
        balance: Response = s.get(urls['balance'], headers=header)
        balance: dict = balance.json()
        logging.info(Fore.LIGHTWHITE_EX + f'You currently have {balance["data"]["payout"]["credits"]} Credits.')


if __name__ == '__main__':
    main()
    logging.info(Fore.LIGHTWHITE_EX + 'Closing HoneygainAutoClaim!')
