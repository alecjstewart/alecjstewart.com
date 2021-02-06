import os
import markdown
import config
from datetime import datetime

def build_notes(env, sorted_notes):
    template = env.get_template('note.html')

    for note in sorted_notes:
        html = template.render(note=note)

        file_name = f'{note["slug"][0]}.html'
        with open(f'{config.BUILD_DIR}/{file_name}', 'w') as build_file:
            build_file.write(html)


def get_notes():
    notes = []
    notes_dir = f'{config.ROOT}/notes/'

    for markdown_note in os.listdir(notes_dir):
        file_path = os.path.join(notes_dir, markdown_note)

        with open(file_path, 'r') as f:
            md = markdown.Markdown(extensions = ['meta'])
            html = md.convert(f.read())
            
            posted = datetime.strptime(md.Meta['posted_date'][0], '%Y-%m-%dT%H:%M:%SZ')
            md.Meta['posted_date_str'] = [posted.strftime('%B %d, %Y')]
            md.Meta['posted_date_time'] = [posted.strftime('%H:%M')]

            if 'updated_date' in md.Meta:
                updated = datetime.strptime(md.Meta['updated_date'][0], '%Y-%m-%dT%H:%M:%SZ')
                md.Meta['updated_date_str'] = [updated.strftime('%B %d, %Y')]
                md.Meta['updated_date_time'] = [updated.strftime('%H:%M')]

            md.Meta['filename'] = [markdown_note]
            md.Meta['content'] = [html]
            notes.append(md.Meta)

    sorted_notes = sorted(notes, reverse=True, key=lambda i: i['posted_date'])
    return sorted_notes