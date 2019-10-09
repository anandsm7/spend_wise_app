# handle dataset
import numpy as np
import pandas as pd
# Text preprocessing
import re
import string
import ast 
import random
import logging
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
from datetime import date
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from spendwell_app import app, db, bcrypt
from flask_login import login_required,login_user, current_user, logout_user
import pandasql as psql
# Model Persist
from sklearn.externals import joblib

response_df = pd.read_csv('spendwell_app/response.csv')

#global
month_lst = ['jan','feb','mar','apr','may','june','july','aug','sep','oct','nov','dec']
year_lst = ['2015','2016','2017','2018','2019','2020','2021']
cat_lst = ['food','transport','bills','shopping']
month_dict = {'jan':'01','feb':'02','mar':'03','apr':'04','may':'05','june':'06','july':'07','aug':'08','sep':'09','oct':'10','nov':'11','dec':'12'}


def clean_text(*, user_log) -> str:

    text = user_log.translate(string.punctuation)
    text = text.lower().split()
    stops = set(stopwords.words('english'))
    text = [w for w in text if not w in stops and len(w) >= 3]
    text = " ".join(text)
    # Clean the text
    text = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", text)
    text = re.sub(r"what's", "what is ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r",", " ", text)
    text = re.sub(r"\.", " ", text)
    text = re.sub(r"!", " ! ", text)
    text = re.sub(r"\/", " ", text)
    text = re.sub(r"\^", " ^ ", text)
    text = re.sub(r"\+", " + ", text)
    text = re.sub(r"\-", " - ", text)
    text = re.sub(r"\=", " = ", text)
    text = re.sub(r"'", " ", text)
    text = re.sub(r"(\d+)(k)", r"\g<1>000", text)
    text = re.sub(r":", " : ", text)
    text = re.sub(r" e g ", " eg ", text)
    text = re.sub(r" b g ", " bg ", text)
    text = re.sub(r" u s ", " american ", text)
    text = re.sub(r"\0s", "0", text)
    text = re.sub(r" 9 11 ", "911", text)
    text = re.sub(r"e - mail", "email", text)
    text = re.sub(r"j k", "jk", text)
    text = re.sub(r"\s{2,}", " ", text)
    
    text = text.split()
    text = " ".join(text)
    
    return text

def predictor(*, user_log):
    logging.info('Inside Predict Function')

    classifier_model = joblib.load(filename = 'spendwell_app/nb_finance_model_v2.pkl')
    logging.info('Model loaded')
    confidence = classifier_model.predict_proba([clean_text(user_log = user_log)])
    logging.info(f'confidence-->{confidence}')
    if (confidence[0][np.argmax(confidence)] > 0.6):
        category = classifier_model.classes_[np.argmax(confidence)]
    else:
        category = 'others'
    logging.info(f'category-->{category}')
    logging.error('This is an error message')
    return category

def chatbot_intent_predict(*,user_query):

    logging.info('Inside Chatbot Intent Function')
    logging.info('loading response file')
    intent_classifier = joblib.load(filename = 'spendwell_app/NB_Cbot.pkl')
    logging.info('Model loaded')
    rank = intent_classifier.predict_proba([user_query])
    arg = np.argmax(rank)
    confidence = rank[0][arg]
    intent = intent_classifier.classes_[arg]
    logging.info(f'Intent {intent}')
    print("intetnt-----------------------",intent)
    response = response_gen(con = confidence ,intent = intent, u_query = user_query)

    return str(response)

def response_gen(*,con,intent,u_query):
    print("confidende----------->",con)
    if con < 0.8:
        response = "Oops i don't know the answer for that boss forgive me 😭"
    elif intent.startswith('s_talk.'):
        logging.info('Small talk intent')
        ans = ast.literal_eval(psql.sqldf(f"SELECT Response FROM response_df WHERE Intent = '{intent}'")['Response'][0])
        response = random.choice(ans)
    elif intent.startswith('buss.spend'):
        logging.info('Bussiness intent')
        ans_month,ans_year,ans_cat = find_year_month(query = u_query)
        print(ans_month)
        print(ans_year)
        print(ans_cat)
        if ans_month is not None:
            ans_month = month_dict[ans_month]
        if ans_month and ans_year and ans_cat:
            info = db.engine.execute(f"""SELECT user_log,amount,DATE(transaction_date) FROM log WHERE category = '{ans_cat}' AND user_id = {current_user.id} AND extract(year from transaction_date) = {ans_year} AND extract(month from transaction_date) = {ans_month};""")
        elif ans_month and ans_year :
            info = db.engine.execute(f"""SELECT user_log,amount,DATE(transaction_date) FROM log WHERE user_id = {current_user.id} AND extract(year from transaction_date) = {ans_year} AND extract(month from transaction_date) = {ans_month};""")
        elif ans_month and ans_cat:
            info = db.engine.execute(f"""SELECT user_log,amount,DATE(transaction_date) FROM log WHERE category = '{ans_cat}' AND user_id = {current_user.id} AND extract(month from transaction_date) = {ans_month};""")
        elif ans_year and ans_cat:
            info = db.engine.execute(f"""SELECT user_log,amount,DATE(transaction_date) FROM log WHERE category = '{ans_cat}' AND user_id = {current_user.id} AND extract(year from transaction_date) = {ans_year};""")
        elif ans_cat:
            print((f"""SELECT user_log,amount,DATE(transaction_date) FROM log WHERE category = '{ans_cat}' AND user_id = {current_user.id};"""))
            info = db.engine.execute(f"""SELECT user_log,amount,DATE(transaction_date) FROM log WHERE category = '{ans_cat}' AND user_id = {current_user.id};""")
        elif ans_month:
            info = db.engine.execute(f"""SELECT user_log,amount,DATE(transaction_date) FROM log WHERE user_id = {current_user.id} AND extract(month from transaction_date) = {ans_month};""")
        elif ans_year:
            info = db.engine.execute(f"""SELECT user_log,amount,DATE(transaction_date) FROM log WHERE user_id = {current_user.id} AND extract(year from transaction_date) = {ans_year};""")
        else:
            info = db.engine.execute(f"""SELECT user_log,amount,DATE(transaction_date) FROM log WHERE user_id = {current_user.id};""")
        res = [i for i in info]
        print(res)
        str_table = "This is all i could find boss<br><table border =1 bgcolor ='#3071a9' color = '#ffffff'><tr><th>Log</th><th>Amount</th><th>Date</th></tr>"
        for r in res:
            strRW = "<tr><td >"+str(r[0])+ "</td><td>"+str(r[1])+"</td>" + "<td>"+str(r[2])+"</td></tr>"
            str_table = str_table+strRW
        str_table = str_table+"</table></html>"
        print(str_table)
        response = str_table

    elif intent.startswith('buss.recommd'):
        amount = []
        category = []
        print(f"SELECT SUM(amount),category FROM log WHERE user_id = {current_user.id} AND extract(month from transaction_date) = {date.today().month} GROUP BY category;")
        info = db.engine.execute(f"SELECT SUM(amount),category FROM log WHERE user_id = {current_user.id} AND extract(month from transaction_date) = {date.today().month} GROUP BY category;")
        res = [i for i in info]
        for val in res:
            amount.append(int(val[0]))
            category.append(val[1])
        h_cat = category[np.argmax(amount)]
        response = f"Your are spending too much on {h_cat} with a total of {max(amount)} "


    return str(response)


def find_year_month(*,query):
    for month in month_lst:
        month_ans = re.search(month,query.lower())
        if month_ans is not None:
            final_month = month_ans.group(0)
            break
        else:
            final_month = None
    for year in year_lst:
        year_ans = re.search(year,query.lower())
        if year_ans is not None:
            final_year = year_ans.group(0)
            break
        else:
            final_year = None
    for cat in cat_lst:
        cat_ans = re.search(cat,query.lower())
        if cat_ans is not None:
            final_cat = cat_ans.group(0)
            break
        else:
            final_cat = None
            
    return final_month,final_year,final_cat




