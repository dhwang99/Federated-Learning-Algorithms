#! encoding: utf-8

import rsa
import hashlib
import random
import gmpy2

def H1(val, salt = None):
    val = str(val)
    if salt != None and salt != '':
        val = val + salt
    return hashlib.sha256(bytes(val, encoding='utf-8')).hexdigest()

def H2(val, salt = None):
    val = str(val)
    if salt != None and salt != '':
        val = val + salt
    return hashlib.md5(bytes(val, encoding='utf-8')).hexdigest() 

def powmod(sid, e, rsa_n):
    return int(gmpy2.powmod(sid, e, rsa_n))

def random_coprime(rsa_n):
    r = 1
    while True:
        r = random.SystemRandom().getrandbits(16)
        a = rsa_n
        b = r
    
        while b != 0:
            tmp = b
            b = a % b
            a = tmp

        if a == 1:
            break
    return r
        

guest_ids = [1,2,3,5]
host_ids = [1,2,3,4]

#step 1: generate rsa private/pub key
(public_key, private_key) = rsa.newkeys(1024)
rsa_e, rsa_n = (public_key.e, public_key.n)
rsa_d = private_key.d

#step 2: guest: gen YA and send to host 
hash_gids = [] 
YA  = []
for sid in guest_ids:
    #r = random_coprime(rsa_n)
    r = random.SystemRandom().getrandbits(16)  #不要求 r 与 rsa_n 互质
    er_h_id = powmod(r, rsa_e, rsa_n) * int(H1(sid), 16) % rsa_n
    hash_gids.append((sid, r, er_h_id))
    YA.append(er_h_id)
   
#step 3: host: calc ZA, ZB
ZA = []
for er_h_id in YA:
    r_dh_id = powmod(er_h_id, rsa_d, rsa_n) 
    ZA.append(r_dh_id)

ZB = []
hash_hids = []
for sid in host_ids:
    hdh_id = H2(powmod(int(H1(sid), 16), rsa_d, rsa_n)) 
    hash_hids.append((sid, hdh_id))
    ZB.append(hdh_id)

#step 4: guest intersect
DA = {}
for i in range(len(ZA)):
    sid, r, eh_id = hash_gids[i]
    hdh_id =  H2(gmpy2.divm(ZA[i], r, rsa_n))
    DA[hdh_id] = sid

I = []
for hdh_id in ZB:
    if hdh_id in DA:
        I.append(DA[hdh_id])

print(I)
