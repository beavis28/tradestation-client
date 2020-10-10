import json
import os.path
import pyotp
import time

from oauthlib.common import to_unicode
from requests_oauthlib import OAuth2Session
from requests import Session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait



class Tradestation:
    
    def __init__(self, username, password, client_id, client_secret, otp_secret=None, headless=True):
        self.username = username
        self.password = password
        self.session = Session()
        self.otp_secret = otp_secret
        self.headless = headless

        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = 'https://api.tradestation.com/v2'
        self.authorisation_url = self.api_url + '/authorize'
        self.token_endpoint = self.api_url + '/Security/Authorize'
        self.redirect_uri = 'https://127.0.0.1/'
        self.oauth = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri)
        self.token_filename =  os.path.join(os.path.dirname(__file__), 'tradestation-token.json')
        
        if os.path.exists(self.token_filename):
            with open(self.token_filename) as token:
                self.token = json.load(token)
        else:
            self.authorise()
        
        self.oauth = OAuth2Session(
            client_id=self.client_id,
            token=self.token,
            auto_refresh_url=self.token_endpoint,
            token_updater=self.save_token,
            auto_refresh_kwargs={
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        )

        self.oauth.register_compliance_hook('access_token_response', self.non_compliant_token)
        self.oauth.register_compliance_hook('refresh_token_response', self.non_compliant_token)

        self.accounts = self.get_user_accounts()

    def authorise(self):
        authorization_url, _ = self.oauth.authorization_url(self.authorisation_url)
        print(f'Please go to {authorization_url} and authorize access.')

        authorization_response = input('Enter the full callback URL: ')

        self.token = self.oauth.fetch_token(
            self.token_endpoint, 
            authorization_response=authorization_response, 
            client_secret=self.client_secret
        )
    
    def generate_otp(self):
        try:
            pyotp.TOTP(self.otp_secret).now()                
            time_to_refresh = (30 - time.gmtime().tm_sec % 30) + 1
            time.sleep(min(time_to_refresh, 5))
            return pyotp.TOTP(self.otp_secret).now()
        except TypeError:
            return input("Enter 2FA code from your authenticator app: ").upper()

    def get_cash_transactions(self, account, date):
        # Get Cash Transactions (Platform Fees, Transfers etc)
        transactions = []
        cash_transactions_url = f'https://clientcenter.tradestation.com/api/v1/Account/{account["Name"]}/{account["TypeDescription"]}/Trades/Cash/{date}/{date}'
        cash_transactions_params = '?page=1&pageSize=1000&orderBy=TradeDate&sortOrder=Ascending'
        
        cash_transactions = self.session.get(cash_transactions_url + cash_transactions_params).json()['Results']
        
        for cash_transaction in cash_transactions:
            if self.include_transaction(cash_transaction):
                cash_transaction['AccountId'] = account['Name']
                cash_transaction['TradeDate'] = date
                cash_transaction['Type'] = 'CASH JOURNAL'
                cash_transaction['Description'] = cash_transaction['Description'].rstrip()
                transactions.append(cash_transaction)
        return transactions
    
    def get_fees(self, account, date):
        # Get Fees Summary Per Contract
        transactions = []
        contracts_url = f'https://clientcenter.tradestation.com/api/v1/Account/{account["Name"]}/{account["TypeDescription"]}/Trades/Trades/{date}/{date}'
        contracts_params = '?page=1&pageSize=100&orderBy=ContractDescription&sortOrder=Ascending'
        
        contracts_traded = self.session.get(contracts_url + contracts_params).json()['Results']

        for contract in contracts_traded:
            contract['AccountId'] = contract['AccountNo']
            contract['TradeDate'] = date
            contract['Type'] = 'FEES'
            contract['Description'] = contract['Contract'].rstrip()
            transactions.append(contract)
        return transactions

    def get_orders(self, account_id):
        return self.oauth.get(self.api_url + '/accounts/' + str(account_id) + '/orders').json()

    def get_positions(self, account_id):
        return self.oauth.get(self.api_url + '/accounts/' + str(account_id) + '/positions').json()

    def get_purchase_sales(self, account, date):
        # Get Purchase/Sale Information (Positions that were closed within the specified time period)
        transactions = []
        purchase_sale_url = f'https://clientcenter.tradestation.com/api/v1/Account/{account["Name"]}/{account["TypeDescription"]}/Trades/PS/{date}/{date}'
        purchase_sale_params = '?page=1&pageSize=1000&orderBy=ContractDescription&sortOrder=Ascending'
        
        closed_positions = self.session.get(purchase_sale_url + purchase_sale_params).json()['Results']

        for closed_position in closed_positions:
            closed_position['TradeDate'] = date
            closed_position['Type'] = 'PURCHASE & SALE'
            closed_position['Description'] = closed_position['Contract'].rstrip()
            transactions.append(closed_position)
        return transactions

    def get_quotes(self, symbols):
        if isinstance(symbols, list):
            symbols = ','.join(symbols)
        
        return self.oauth.get(self.api_url + '/data/quote/' + symbols).json()
    
    def get_transactions(self, date):
        date_formatted = date.strftime(f"%Y-%m-%d")
        print(f'Getting transactions for: {date_formatted}')
        transactions = []

        for account in self.accounts:
            cash_transactions = self.get_cash_transactions(account, date_formatted)
            purchase_sales = self.get_purchase_sales(account, date_formatted)
            fees = self.get_fees(account, date_formatted)
            transactions.extend(cash_transactions + purchase_sales + fees)
        return transactions
    
    def get_user_accounts(self):
        return self.oauth.get(self.api_url + '/users/' + self.username + '/accounts').json()

    def include_transaction(self, transaction):
        exclusions = ['TRANSFER', 'CURRENCY CONVERSION', 'WIRE IN']
        description = transaction['Description'].upper()
        return not any(substr in description for substr in exclusions)

    def login(self):
        options = webdriver.ChromeOptions()
        options.headless = self.headless
        browser = webdriver.Chrome(options=options)
        client_center = 'https://clientcenter.tradestation.com/'
        timeout = 30

        browser.get(client_center)
        uname_input = WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located((By.ID, 'username'))
        )
        uname_input.send_keys(self.username)
        
        pwd_input = WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located((By.ID, 'password'))
        )
        pwd_input.send_keys(self.password, Keys.RETURN)

        otp_input = WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located((By.NAME, 'code'))
        )
        otp_input.send_keys(self.generate_otp(), Keys.RETURN)

        WebDriverWait(browser, timeout*2).until(
            EC.url_contains(client_center)
        )

        cookies = browser.get_cookies()
        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])
        
        browser.quit()
    
    def non_compliant_token(self, response):
        token = json.loads(response.text)
        token["token_type"] = "Bearer"
        fixed_token = json.dumps(token)
        response._content = to_unicode(fixed_token).encode("utf-8")
        return response

    def save_token(self, token):
        with open(self.token_filename, 'w') as output:
            json.dump(token, output, sort_keys=True, indent=4)
