#! encoding: utf-8

import phe
from phe import EncodedNumber, paillier
from phe.util import invert, powmod, getprimeover, isqrt
import numpy as np
import pandas as pd
import pdb

def encrypt(public_key, xa):
    return np.array([public_key.encrypt(x) for x in xa])

def decrypt(private_key, xa):
    return np.array([private_key.decrypt(x) for x in xa])


#0: firstly, we need samples. from  http://archive.ics.uci.edu/ml/machine-learning-databases/00294/, get sheet 1
samples = pd.read_csv('samples.csv') 
# AT	V	AP	RH	PE
Y = np.array(samples['PE'])
XA = np.array(samples[['AT', 'V']])
XB = np.array(samples[['AP', 'RH']])

XA /= XA.max(axis=0)
XB /= XB.max(axis=0)

N = Y.size

#1. arbiter generate pub and pri key
public_key, private_key = paillier.generate_paillier_keypair(n_length=1024)

thetaA = np.zeros(XA.shape[1])
thetaB = np.zeros(XB.shape[1])

#XB has label
eta = 0.05
epoch = 100

#build base model
for i in range(epoch):
    UA = np.dot(XA, thetaA)
    UB = np.dot(XB, thetaB)
    UB_minus_Y = UB - Y

    d = np.add(UA, UB_minus_Y)

    gradient_A = np.dot(d, XA) / N
    gradient_B = np.dot(d, XB) / N

    thetaA -= eta * gradient_A 
    thetaB -= eta * gradient_B 

    loss = np.sum(d ** 2) / N

    print("theta:", np.append(thetaA, thetaB), " loss:", loss)
    
#build FL model
thetaA = np.zeros(XA.shape[1])
thetaB = np.zeros(XB.shape[1])

maskA = 0.01
maskB = 0.01

for i in range(epoch):
    #part A, 
    UA = np.dot(XA, thetaA)

    UA_enc = encrypt(public_key, UA) 
    UA2_enc = encrypt(public_key, UA ** 2) 

    #send UA_enc, UA2_enc to part B
    
    #part B, 
    UB = np.dot(XB, thetaB)
    
    UB_minus_Y = UB - Y

    UB_minus_Y_enc = encrypt(public_key, UB_minus_Y)

    #calc d, and send it to part A
    d = np.add(UA_enc, UB_minus_Y_enc)
    
    # calc encry loss, and send it to arbiter
    UB_minus_Y2_enc = encrypt(public_key, UB_minus_Y ** 2)
    UA_enc_UBY_dot = np.dot(UA_enc, UB_minus_Y) * 2
    loss_enc = np.add(UA2_enc.sum(), UB_minus_Y2_enc.sum())
    loss_enc = np.add(loss_enc, UA_enc_UBY_dot)
    
    #part B: calc enc gradient B, and send it to arbiter
    gradient_B_enc = np.dot(d, XB) + public_key.encrypt(maskB)

    #part A: got d and calc enc gradient A, and send ti to arbiter
    gradient_A_enc = np.dot(d, XA) + public_key.encrypt(maskA)

    #arbiter: decrypt gradient A, gradient B, loss
    gradient_A = decrypt(private_key, gradient_A_enc)
    gradient_B = decrypt(private_key, gradient_B_enc)
    loss = private_key.decrypt(loss_enc) / N
    
    #arbiter: send decrypted gradient A to A, gradient B to B
    #gradient_A to part A, and part A updated
    gradient_A -= maskA
    thetaA -= eta * gradient_A / N

    #gradient_B to part B, and part B updated
    gradient_B -= maskB
    thetaB -= eta * gradient_B / N
    
    #out debug info
    print("theta:", np.append(thetaA, thetaB), " loss:", loss)
