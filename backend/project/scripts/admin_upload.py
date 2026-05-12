import re
import requests
import sys
import subprocess
from pathlib import Path

BASE = 'http://127.0.0.1:8000'
LOGIN = BASE + '/admin/login/?next=/admin/'
UPLOAD = BASE + '/admin/app/connection/upload-csv/'
USERNAME = 'sneha_kalluru'
PASSWORD = 'sneha@5183409'
CSV_PATH = Path('electricity_board_case_study.csv')

if not CSV_PATH.exists():
    print('CSV not found at', CSV_PATH.resolve())
    sys.exit(2)

session = requests.Session()
# get login page
r = session.get(LOGIN, timeout=10)
if r.status_code != 200:
    print('Login page returned', r.status_code)
    sys.exit(2)

m = re.search(r"name=['\"]csrfmiddlewaretoken['\"] value=['\"]([^'\"]+)['\"]", r.text)
if not m:
    print('Could not find CSRF token on login page')
    sys.exit(2)

token = m.group(1)
payload = {'username': USERNAME, 'password': PASSWORD, 'csrfmiddlewaretoken': token, 'next': '/admin/'}
headers = {'Referer': LOGIN}

r2 = session.post(LOGIN, data=payload, headers=headers, timeout=20)
if r2.status_code not in (200, 302):
    print('Login POST failed:', r2.status_code)
    sys.exit(2)

# verify login by checking presence of 'Log out' or admin index
r_index = session.get(BASE + '/admin/')
if 'Log out' not in r_index.text and 'site administration' not in r_index.text.lower():
    print('Login appears to have failed; admin index did not show. Status:', r_index.status_code)
    sys.exit(2)

# get upload page to fetch CSRF
r3 = session.get(UPLOAD)
if r3.status_code != 200:
    print('Upload page GET returned', r3.status_code)
    print('Response length:', len(r3.text))
    sys.exit(2)

m2 = re.search(r"name=['\"]csrfmiddlewaretoken['\"] value=['\"]([^'\"]+)['\"]", r3.text)
if not m2:
    # try to get token from cookies
    token = session.cookies.get('csrftoken') or session.cookies.get('csrfmiddlewaretoken')
else:
    token = m2.group(1)

files = {'csv_file': (CSV_PATH.name, open(CSV_PATH, 'rb'), 'text/csv')}
data = {'csrfmiddlewaretoken': token}
headers = {'Referer': UPLOAD}

post = session.post(UPLOAD, data=data, files=files, headers=headers, timeout=120)
print('UPLOAD STATUS:', post.status_code)
print('UPLOAD REDIRECT:', post.headers.get('Location'))
print('UPLOAD LEN:', len(post.content))

# report counts via manage.py
try:
    out = subprocess.check_output(['python', 'manage.py', 'shell', '-c', "from app.models import Applicant,Connection; print('APPLICANTS:', Applicant.objects.count()); print('CONNECTIONS:', Connection.objects.count())"], cwd='.', text=True)
    print('\nDB COUNTS:\n', out)
except Exception as e:
    print('Could not run manage.py shell to get counts:', e)

print('Done')
