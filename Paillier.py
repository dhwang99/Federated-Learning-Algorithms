#!/usr/bin/env python
# from  http://blog.b3ale.cn/2019/10/24/Python%E5%AE%9E%E7%8E%B0Paillier%E5%8A%A0%E5%AF%86%E8%A7%A3%E5%AF%86%E7%AE%97%E6%B3%95/
import gmpy2
import random
import time
import libnum
def get_prime(rs):
    p = gmpy2.mpz_urandomb(rs, 1024)
    while not gmpy2.is_prime(p):
        p = p + 1
    return p
def L(x, n):
    return (x - 1) / n
def keygen():
    rs = gmpy2.random_state(int(time.time()))
    p = get_prime(rs)
    q = get_prime(rs)
    n = p * q
    lmd = (p - 1) * (q - 1)
    #g = random.randint(1, n ** 2)
    g = n + 1
    if gmpy2.gcd(L(gmpy2.powmod(g, lmd, n ** 2), n), n) != 1:
        print '[!] g is not good enough'
        exit()
    pk = [n, g]
    sk = lmd
    return pk, sk
def encipher(plaintext, pk):
    m = libnum.s2n(plaintext)
    n, g = pk
    r = random.randint(1, n ** 2)
    c = gmpy2.powmod(g, m, n ** 2) * gmpy2.powmod(r, n, n ** 2) % (n ** 2)
    return c
def decipher(c, pk, sk):
    [n, g] = pk
    lmd = sk
    u = gmpy2.invert(L(gmpy2.powmod(g, lmd, n ** 2), n), n) % n
    m = L(gmpy2.powmod(c, lmd, n ** 2), n) * u % n
    plaintext = libnum.n2s(m)
    return plaintext
if __name__ == '__main__':
    pk, sk = keygen()
    #print 'pk:', pk
    #print 'sk:', sk
    plaintext = raw_input('Please input your message: ')
    ciphertext = encipher(plaintext, pk)
    print 'Ciphertext:', ciphertext
    plaintext = decipher(ciphertext, pk, sk)
    print 'Plaintext:', plaintext
