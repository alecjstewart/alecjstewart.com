import config
from datetime import datetime

def build_feed(env, sorted_notes):
    template = env.get_template('feed.xml')

    now = datetime.utcnow()
    date_string = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    xml = template.render(feed=sorted_notes, updated=date_string)

    with open(f'{config.BUILD_DIR}/feed.xml', 'w') as build_file:
        build_file.write(xml)