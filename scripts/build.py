import os

import aws
import feed
import notes
import config

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = f'{config.ROOT}/templates'
SKIP = ['base.html', 'feed.xml', 'note.html']

def build_root(env, sorted_notes, html_tweets, read, reading):
    for f in os.listdir(TEMPLATE_DIR):
        if f not in SKIP:
            template = env.get_template(f)

            if f == 'index.html' or f == 'notes.html':
                html = template.render(notes=sorted_notes)
            elif f == 'tweets.html':
                html = template.render(tweets=html_tweets)
            elif f == 'books.html':
                html = template.render(books_read=read, books_reading=reading)
            else:
                html = template.render()

            with open(f'{config.BUILD_DIR}/{f}', 'w') as build_file:
                build_file.write(html)


if __name__ == '__main__':
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    # Get tweets and add anchors appropriately
    tweets = aws.get_tweets()
    html_tweets = aws.url_to_anchor(tweets)

    # Get currently reading and read books
    read = aws.get_books('read')
    reading = aws.get_books('reading')

    # Get notes (sorted by created date)
    sorted_notes = notes.get_notes()

    # Build HTML website
    build_root(env, sorted_notes, html_tweets, read, reading)
    notes.build_notes(env, sorted_notes)
    feed.build_feed(env, sorted_notes)