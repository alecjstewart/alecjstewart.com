import os
import re
import boto3
import shutil
import markdown
from jinja2 import Environment, FileSystemLoader
from boto3.dynamodb.conditions import Key, Attr

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


def get_essays():
  essays = {}
  essays_dir = '{}/essays/'.format(PROJECT_DIR)

  for markdown_essay in os.listdir(essays_dir):
    file_path = os.path.join(essays_dir, markdown_essay)

    with open(file_path, 'r') as f:
      md = markdown.Markdown(extensions = ['meta'])
      html = md.convert(f.read())
      essays[markdown_essay] = [md.Meta, html]

  # dict = {'title.md': [metadata, content]}
  # t[1] is the value (i.e. [metadata, content])
  # t[1][0] is the first item in the list (i.e. metadata)
  # t[1][0]['date_str'] is the sort key we want in the metadata dict
  sorted_essays = sorted(essays.items(), reverse=True, key=lambda i: i[1][0]['date_str'])
  return sorted_essays


def url_to_anchor(tweets):
  for tweet in tweets:
    links = re.findall(r'(https?://[^\s]+)', tweet['text'])
    for link in links:
      tweet['text'] = tweet['text'].replace(link, '<a href="{0}" target="_blank">{0}</a>'.format(link))

  return tweets


def copy_static_assets():
  shutil.copy2('{}/stylesheet.css'.format(PROJECT_DIR), BUILD_DIR)
  shutil.copy2('{}/favicon.png'.format(PROJECT_DIR), BUILD_DIR)
  shutil.copytree('{}/images'.format(PROJECT_DIR), '{}/images'.format(BUILD_DIR))


if __name__ == '__main__':
  copy_static_assets()

  sorted_tweets = tweets_from_aws()
  html_tweets = url_to_anchor(sorted_tweets)

  sorted_essays = get_essays()
  essays_metadata = [essay[1][0] for essay in sorted_essays]

  env = Environment(loader=FileSystemLoader(PROJECT_DIR))

  for f in os.listdir(PROJECT_DIR):
    if f.endswith('.html'):
      template = env.get_template(f)

      if f == 'index.html':
        html = template.render(essays=essays_metadata)
      elif f == 'essays.html':
        html = template.render(essays=essays_metadata)
      elif f == 'tweets.html':
        html = template.render(tweets=html_tweets)
      else:
        html = template.render()

      with open('{}/{}'.format(BUILD_DIR, f), 'w') as build_file:
        build_file.write(html)

  template = env.get_template('templates/essay.html')
  for essay in sorted_essays:
    html = template.render(essay=essay[1][0], content=essay[1][1])

    file_name = '{}.html'.format(essay[1][0]['slug'][0])
    with open('{}/{}'.format(BUILD_DIR, file_name), 'w') as build_file:
      build_file.write(html)