"""
This flask service is responsible for fetching the articles from the database, make the file containing the articles
for the chatbot's required format and train the chatbot according to the file. After the chatbot gets trained
successfully, it will be able to provide articles in response to the related question.
/fetch and train: This endpoint will fetch articles from database and will train the bot according to them.
/ask: This endpoint is responsible for providing the articles in response to the question asked.
"""
import logging
import re

import bleach
from chatterbot import ChatBot
from chatterbot.response_selection import get_multiple_response
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)

import url_marker

import pymssql
host = '10.113.9.207'
username = 'SA'
password = '!rata2009derp!'
database = 'PredatarV2'

FETCH_QUESTIONS_QUERY = 'SELECT question FROM Inc_Article_TrainingQuestion'
FETCH_ANSWERS_QUERY = 'SELECT answer FROM Inc_Article_TrainingAnswer'


FILEPATH = '/usr/local/lib/python2.7/dist-packages/chatterbot_corpus/data/english/tickets.yml'

app = Flask(__name__)

chatbot = ChatBot(
    'Test ChatBot',
    trainer='chatterbot.trainers.ChatterBotCorpusTrainer',
    response_selection_method=get_multiple_response)


@app.route('/')
def home():
    return 'Welcome to chatbot flask service'


@app.route('/reset')
def reset_bot():
    """
    This method is responsible for cleaning the chatbot's database.
    :return: Json containing status and success message.
    """
    chatbot.storage.drop()
    return jsonify({'status': 'OK', 'message': 'Database cleanup successful'})


@app.route("/train")
def train():
    chatbot.train(
        "chatterbot.corpus.english.bot_tickets")
    return jsonify({'status': 'OK', 'message': 'Training Completed'})


def connect_to_db():
    """
    This function is responsible for the database connection and fetching the articles from the mssql database
    :return: List of answers and list of questions.
    """
    conn = pymssql.connect(host, username, password, database)
    cursor = conn.cursor()
    cursor.execute(FETCH_QUESTIONS_QUERY)

    list_of_questions = []
    for row in cursor.fetchall():
        if row[0]:
            list_of_questions.append(row[0])
    cursor = conn.cursor()
    cursor.execute(FETCH_ANSWERS_QUERY)
    list_of_answer = []
    for row in cursor.fetchall():
        if row[0]:
            list_of_answer.append(row[0])
    return list_of_answer, list_of_questions


@app.route("/fetch and train")
def fetch_articles_from_db_and_make_file():
    """
    Calls the function responsible for the database connection and will make a file containing questions and answers
    which the chatbot will use as training data and will get trained according to them.
    :return: Json response containing status and message.
    """
    list_of_answers, list_of_questions = connect_to_db()
    f = open(FILEPATH, "w+")
    f.write('categories:'+'\n')
    f.write('- tickets'+'\n\n')
    f.write('conversations:'+'\n')
    for ques in range(len(list_of_questions)):
        f.write('- - '+str(list_of_questions[ques])+'\n')
        f.write('  - '+str(list_of_answers[ques])+'\n\n')
    f.close()
    chatbot.train(
        "chatterbot.corpus.english.bot_tickets")
    return jsonify({'status': 'OK', 'message': 'Training Completed'})


@app.route("/ask", methods=['POST'])
def ask():
    """
    This function is responsible for receiving a POST request containing question and provide the related article in
    response to that question.
    :return:Json response containing status and answer.
    """
    message = request.args.get('message')
    # kernel now ready for use
    while True:
        if message == "quit":
            exit()
        else:
            bot_response = str(chatbot.get_response(message))
            url = re.findall(url_marker.WEB_URL_REGEX, bot_response)
            if url:
                Response = bot_response.replace('(' + url[0] + ')', '')
                url = bleach.linkify(url[0])
                Response = Response.split('%%')

                final_response = Response[0] + '<br>' + ''.join(
                    Response[1:]) + '<br>' + "For more information, checkout the link: " + url
            else:
                final_response = bot_response
            # print bot_response
            return jsonify({'status': 'OK', 'answer': final_response})


if __name__ == "__main__":
    app.run(host='192.168.101.51', port=5000)
