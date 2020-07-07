import requests, json, re, subprocess
from bs4 import BeautifulSoup, SoupStrainer
from html import escape
import codecs

class BoilerPlate:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=0, timeout=10000):                 #FOR GETTING UPDATES
        function = 'getUpdates'
        fieldss = {'timeout' : timeout, 'offset': offset}
        send = requests.get(self.api_url + function, fieldss)
        result_json = send.json()['result']
        return result_json

    def send_message(self, chat_id, text):                          #FOR SENDING MESSAGES
        fieldss = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        function = 'sendMessage'
        send = requests.post(self.api_url + function, fieldss)
        return send
    def send_message_two(self, chat_id, text, reply_markup, one_time_keyboard=False, resize_keyboard=True):     #FOR SENDING MESSAGES WITH A BOT KEYBOARD. PASS [['KEYBOARD BUTTON NAME']]
        reply_markup = json.dumps({'keyboard': reply_markup, 'one_time_keyboard': one_time_keyboard, 'resize_keyboard': resize_keyboard})
        fieldss = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML', 'reply_markup': reply_markup}
        function = 'sendMessage'
        send = requests.post(self.api_url + function, fieldss).json()
        return send
    
    def delete_message(self, group_id, message_id):         #FOR DELETING MESSAGES FROM GROUP
        fieldss = {'chat_id': group_id, 'message_id': message_id}
        function = 'deleteMessage'
        send = requests.post(self.api_url + function, fieldss)
        return send
    
    def deleteWebhook(self):                #CALL THIS AFTER CURRENT_UPDATE IF THERE IS A WEBHOOK ERROR
        function = 'deleteWebhook'
        send = requests.post(self.api_url + function)
        return send

token = ''
offset = 0                  #MODIFY TO -1 TO READ ONLY THE LAST MESSAGE AND IGNORE ALL PREVIOUS MESSAGE. OTHERWISE DO NOT CHANGE
bot = BoilerPlate(token)    #bot.get_updates(offset = update_id+1) IS USED TO PREVENT THE BOT FROM READING THE SAME MESSAGE

def starter():
    global offset
    while True:
        all_updates = bot.get_updates(offset)
        for current_updates in all_updates:
            print(current_updates)
            update_id = current_updates['update_id']
            group_id = current_updates['message']['chat']['id']
            sender_id = current_updates['message']['from']['id']
            dict_checker = []
            for keys in current_updates.get('message'):
                dict_checker.append(keys)
            if 'new_chat_members' in dict_checker or 'left_chat_member' in dict_checker or 'photo' in dict_checker:
                group_message_handler(current_updates, update_id, sender_id, group_id, dict_checker)
            else:
                bot_message_handler(current_updates, update_id, sender_id, group_id, dict_checker)

def bot_message_handler(current_updates, update_id, sender_id, group_id, dict_checker):
    global offset
    text = current_updates['message']['text']
    try:
        if text == '/start' or text == '/help' or text == '/help@zcointipbot':
            bot.send_message(group_id, ("The following commands are at your disposal:\n/hi\n/moon\n/help\n/commands\n/price\n/marketcap\n/balance\n/deposit\n/withdraw\n/tip"))
            bot.get_updates(offset = update_id+1)

        if  text == '/hi' or text == '/hi@zcointipbot':
            first = current_updates['message']['from']['first_name']
            bot.send_message(group_id, f'Hello {first}, How are you doing today?')
            bot.get_updates(offset = update_id+1)

        if  text == '/price' or text == '/price@zcointipbot':
            quote_page = requests.get('https://www.worldcoinindex.com/coin/zcoin')
            strainer = SoupStrainer('div', attrs={'class': 'row mob-coin-table'})
            soup = BeautifulSoup(quote_page.content, 'html.parser', parse_only=strainer)
            name_box = soup.find('div', attrs={'class':'col-md-6 col-xs-6 coinprice'})
            name = name_box.text.replace("\n","")
            price = re.sub(r'\n\s*\n', r'\n\n', name.strip(), flags=re.M)
            fiat = soup.find('span', attrs={'class': ''})
            kkz = fiat.text.replace("\n","")
            percent = re.sub(r'\n\s*\n', r'\n\n', kkz.strip(), flags=re.M)
            #quote_page = requests.get('https://bittrex.com/api/v1.1/public/getticker?market=btc-rdd')
            #soup = BeautifulSoup(quote_page.content, 'html.parser').text
            #btc = soup[80:]
            #sats = btc[:-2]
            bot.send_message(group_id, f'zcoin is valued at {price} Δ {percent}')
            bot.get_updates(offset = update_id+1)
        

        if  text == '/deposit' or text == '/deposit@zcointipbot':
            if 'username' in current_updates['message']['from']:
                user = current_updates['message']['from']['username']
                address = "/usr/bin/zcoin-cli"
                result = subprocess.run([address,"getaccountaddress",user],stdout=subprocess.PIPE)
                clean = (result.stdout.strip()).decode("utf-8")
                bot.send_message(group_id, f'@{user} your depositing address is: {clean}')
                bot.get_updates(offset = update_id+1)
            else:
                bot.send_message(group_id, 'Please set a username from the Telegram Settings')
                bot.get_updates(offset = update_id+1)

        if  text == '/withdraw' or text == '/withdraw@zcointipbot':
            bot.send_message(group_id, 'Wrong Format. Check /commands Send a Message Like this Please:\n\n/withdraw (your wallet address) (amount)\n\nexample:\n\n/withdraw a8ULhhDgfdSiXJhSZVdhb8EuDc6R3ogsaM 5')
            bot.get_updates(offset = update_id+1)


        if '/withdraw' in text and len(text) > 9 or '/withdraw@zcointipbot' in text and len(text) > 21:
            if 'username' in current_updates['message']['from']:
                user = current_updates['message']['from']['username']
                try:
                    target = text[21:]
                    address = target[:47]
                except:
                    target = text[9:]
                    address = target[:35]
                address = ''.join(str(e) for e in address)
                target = target.replace(target[:35], '')
                amount = float(target)
                core = "/usr/bin/zcoin-cli"
                result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
                clean = (result.stdout.strip()).decode("utf-8")
                balance = float(clean)
                if balance < amount:
                    bot.send_message(group_id, f'@{user} you have insufficent funds.')
                    bot.get_updates(offset = update_id+1)
                else:
                    amount = str(amount)
                    tx = subprocess.run([core,"sendfrom",user,address,amount],stdout=subprocess.PIPE)
                    bot.send_message(group_id, f'@{user} has successfully withdrew to address: {address} of {amount} RDD')
                    bot.get_updates(offset = update_id+1)
            else:
                bot.send_message(group_id, 'Please set a username from the Telegram Settings')
                bot.get_updates(offset = update_id+1)
        
        if  text == '/balance' or text == '/balance@zcointipbot':
            if 'username' in current_updates['message']['from']:
                quote_page = requests.get('https://www.worldcoinindex.com/coin/zcoin')
                strainer = SoupStrainer('div', attrs={'class': 'row mob-coin-table'})
                soup = BeautifulSoup(quote_page.content, 'html.parser', parse_only=strainer)
                name_box = soup.find('div', attrs={'class':'col-md-6 col-xs-6 coinprice'})
                name = name_box.text.replace("\n","")
                price = re.sub(r'\n\s*\n', r'\n\n', name.strip(), flags=re.M)
                price = re.sub("[^0-9^.]", "", price)
                price = float(price)
                user = current_updates['message']['from']['username']
                core = "/usr/bin/zcoin-cli"
                result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
                clean = (result.stdout.strip()).decode("utf-8")
                balance  = float(clean)
                fiat_balance = balance * price
                fiat_balance = str(round(fiat_balance,3))
                balance =  str(round(balance,3))
                bot.send_message(group_id, f'@{user} your current balance is: {balance} zcoin ≈  ${fiat_balance}')
                bot.get_updates(offset = update_id+1)
            else:
                bot.send_message(group_id, 'Please set a username from the Telegram Settings')
                bot.get_updates(offset = update_id+1)

        if  text == '/moon' or text == '/moon@zcointipbot':
            bot.send_message(group_id, "Moon mission inbound!")
            bot.get_updates(offset = update_id+1)

        if  text == '/marketcap' or text == '/marketcap@zcointipbot':
            quote_page = requests.get('https://www.worldcoinindex.com/coin/zcoin')
            strainer = SoupStrainer('div', attrs={'class': 'row mob-coin-table'})
            soup = BeautifulSoup(quote_page.content, 'html.parser', parse_only=strainer)
            name_box = soup.find('div', attrs={'class':'col-md-6 col-xs-6 coin-marketcap'})
            name = name_box.text.replace("\n","")
            mc = re.sub(r'\n\s*\n', r'\n\n', name.strip(), flags=re.M)
            bot.send_message(group_id, f"The current market cap of zcoin is valued at {mc}")
            bot.get_updates(offset = update_id+1)


        if text == '/tip' or text == '/tip@zcointipbot':
            bot.send_message(group_id, 'Wrong Format. Check /commands. Send the command like this\n\n /tip (username) (amount)\n\nexample\n\n /tip @Sakib0194 10')
            bot.get_updates(offset = update_id+1)

        if '/tip' in text and len(text) > 4 or '/tip@zcointipbot' in text and len(text) > 16:
            if 'username' in current_updates['message']['from']:
                user = current_updates['message']['from']['username']
                if '/tip@zcointipbot' in text:
                    target = text[16:]
                else:
                    target = text[5:]
                bot.send_message(group_id, target)
                amount =  target.split(" ")[1]
                target =  target.split(" ")[0]
                machine = "@Reddcoin_bot"
                bot.send_message(group_id, target)
                bot.send_message(group_id, amount)
                if target == machine:
                    bot.send_message(group_id, "HODL.")
                    bot.get_updates(offset = update_id+1)
                elif "@" in target:
                    target = target[1:]
                    user = current_updates['message']['from']['username']
                    core = "/usr/bin/zcoin-cli"
                    result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
                    balance = float((result.stdout.strip()).decode("utf-8"))
                    amount = float(amount)
                    if balance < amount:
                        bot.send_message(group_id, f"@{user} you have insufficent funds.")
                        bot.get_updates(offset = update_id+1)
                    elif target == user:
                        bot.send_message(group_id, text="You can't tip yourself silly.")
                        bot.get_updates(offset = update_id+1)
                    else:
                        balance = str(balance)
                        amount = str(amount) 
                        tx = subprocess.run([core,"move",user,target,amount],stdout=subprocess.PIPE)
                        bot.send_message(group_id, f"@{user} tipped @{target} of {amount} zcoin")
                        bot.get_updates(offset = update_id+1)
                else: 
                    bot.send_message(group_id, "Error that user is not applicable.")
                    bot.get_updates(offset = update_id+1)
            else:
                bot.send_message(group_id, 'Please set a username from the Telegram Settings')
                bot.get_updates(offset = update_id+1)

        if text == '/commands' or text == '/commands@zcointipbot':
            if 'username' in current_updates['message']['from']:
                user = current_updates['message']['from']['username']
                bot.send_message(group_id, "Initiating commands /tip & /withdraw have a specfic format,\n use them like so:" + "\n \n Parameters: \n user = target user to tip \n amount = amount of zcoin to utilise \n address = zcoin address to withdraw to \n \n Tipping format: \n /tip user amount \n \n Withdrawing format: \n /withdraw address amount")
                bot.get_updates(offset = update_id+1)
            else:
                bot.send_message(group_id, 'Please set a username from the Telegram Settings')
                bot.get_updates(offset = update_id+1)
    except:
        print('Some kind of error on', text)
        bot.get_updates(offset = update_id+1)

def group_message_handler(current_updates, update_id, sender_id, group_id, dict_checker):
    message_id = current_updates['message']['message_id']

    if 'text' not in dict_checker and sender_id != group_id:
        if 'photo' in dict_checker:
            pass
        else:
            print('new member joined or left')
            bot.delete_message(group_id, message_id)
            bot.get_updates(offset = update_id+1)

if __name__ == "__main__":
    starter()


'''MUST BE ADDED'''

'''FOR BOT FATHER -> SELECT BOT -> EDIT BOT -> EDIT COMMAND 

balance - shows balance
moon - to the moon
help - available commands
deposit - get deposit address
price - shows zcoin price
marketcap - shows zcoin marketcap
hi - welcome message
commands - shows how to use commands

EDIT DESCRIPTION AS NEEDED
'''
