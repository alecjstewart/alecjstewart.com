import os
import re
import boto3

from boto3.dynamodb.conditions import Key, Attr
from dotenv import load_dotenv

load_dotenv()
dynamodb = boto3.resource('dynamodb')

def get_books(status):
    table = dynamodb.Table(os.environ.get('BOOKS_TABLENAME'))

    response = table.scan(FilterExpression=Attr('status').eq(status))
    books = response['Items']

    while response.get('LastEvaluatedKey'):
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        books.extend(response['Items'])

    sorted_books = sorted(books, key=lambda i: i['title'])
    return sorted_books


def get_tweets():
    table = dynamodb.Table(os.environ.get('TWEETS_TABLENAME'))

    response = table.scan(FilterExpression=Attr('deleted').eq(False) & Attr('other_reply').eq(False))
    tweets = response['Items']

    sorted_tweets = sorted(tweets, reverse=True, key = lambda i: i['created_at'])
    return sorted_tweets


def url_to_anchor(tweets):
    for tweet in tweets:
        links = re.findall(r'(https?://[^\s]+)', tweet['text'])
        for link in links:
            tweet['text'] = tweet['text'].replace(link, '<a href="{0}" target="_blank">{0}</a>'.format(link))

    return tweets