import os
import re
import boto3
import shutil
import markdown

from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from boto3.dynamodb.conditions import Key, Attr

from dotenv import load_dotenv
load_dotenv()

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
BUILD_DIR = '{}/_site'.format(PROJECT_DIR)
if os.path.isdir(BUILD_DIR):
    shutil.rmtree(BUILD_DIR)
os.mkdir(BUILD_DIR)

def tweets_from_aws():
    dynamodb = boto3.resource('dynamodb')
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


def copy_static_assets():
    shutil.copy2('{}/stylesheet.css'.format(PROJECT_DIR), BUILD_DIR)
    shutil.copy2('{}/favicon.png'.format(PROJECT_DIR), BUILD_DIR)
    shutil.copy2('{}/ajs_pubkey.asc'.format(PROJECT_DIR), BUILD_DIR)
    shutil.copytree('{}/images'.format(PROJECT_DIR), '{}/images'.format(BUILD_DIR))


def get_notes():
    notes = []
    notes_dir = '{}/notes/'.format(PROJECT_DIR)

    for markdown_note in os.listdir(notes_dir):
        file_path = os.path.join(notes_dir, markdown_note)

        with open(file_path, 'r') as f:
            md = markdown.Markdown(extensions = ['meta'])
            html = md.convert(f.read())
            
            posted = datetime.strptime(md.Meta['posted_date'][0], '%Y-%m-%dT%H:%M:%SZ')
            md.Meta['posted_date_str'] = [posted.strftime('%d %B %Y')]
            md.Meta['posted_date_time'] = [posted.strftime('%H:%M')]

            if 'updated_date' in md.Meta:
                updated = datetime.strptime(md.Meta['updated_date'][0], '%Y-%m-%dT%H:%M:%SZ')
                md.Meta['updated_date_str'] = [updated.strftime('%d %B %Y')]
                md.Meta['updated_date_time'] = [updated.strftime('%H:%M')]

            md.Meta['filename'] = [markdown_note]
            md.Meta['content'] = [html]
            notes.append(md.Meta)

    sorted_notes = sorted(notes, reverse=True, key=lambda i: i['posted_date'])
    return sorted_notes


def generate_feed(env, sorted_notes):
    template = env.get_template('feed.xml')

    now = datetime.utcnow()
    date_string = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    xml = template.render(feed=sorted_notes, updated=date_string)

    with open('{}/feed.xml'.format(BUILD_DIR), 'w') as build_file:
        build_file.write(xml)


def generate_notes(env, sorted_notes):
    template = env.get_template('templates/note.html')

    for note in sorted_notes:
        html = template.render(note=note)

        file_name = '{}.html'.format(note['slug'][0])
        with open('{}/{}'.format(BUILD_DIR, file_name), 'w') as build_file:
            build_file.write(html)


def generate_root(env, sorted_notes, html_tweets):
    for f in os.listdir(PROJECT_DIR):
        if f.endswith('.html'):
            template = env.get_template(f)

            if f == 'index.html' or f == 'notes.html':
                html = template.render(notes=sorted_notes)
            elif f == 'tweets.html':
                html = template.render(tweets=html_tweets)
            else:
                html = template.render()

            with open('{}/{}'.format(BUILD_DIR, f), 'w') as build_file:
                build_file.write(html)


if __name__ == '__main__':
    env = Environment(loader=FileSystemLoader(PROJECT_DIR))

    copy_static_assets()

    sorted_tweets = tweets_from_aws()
    html_tweets = url_to_anchor(sorted_tweets)

    sorted_notes = get_notes()

    generate_root(env, sorted_notes, html_tweets)
    generate_notes(env, sorted_notes)
    generate_feed(env, sorted_notes)