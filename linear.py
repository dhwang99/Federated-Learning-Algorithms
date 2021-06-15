#! encoding: utf-8

import phe
from phe import EncodedNumber, paillier
from phe.util import invert, powmod, getprimeover, isqrt
import numpy as np
import pandas as pd
import pdb

#因为有浮点数和整数转换问题，直接调用库来进行计算，不写算法计算过程了
def encrypt(public_key, xa):
    return np.array([public_key.encrypt(x) for x in xa])

def decrypt(private_key, xa):
    return np.array([private_key.decrypt(x) for x in xa])

#0: firstly, we need samples. from  http://archive.ics.uci.edu/ml/machine-learning-databases/00294/, get sheet 1
all_samples = pd.read_csv('samples.csv') 

tsize = int(all_samples.shape[0] * .7)
train_samples = all_samples[:tsize]
test_samples = all_samples[tsize:]

#TRAIN
# AT	V	AP	RH	PE
samples = train_samples
Y = np.array(samples['PE'])
XA = np.array(samples[['AT', 'V']])
XB = np.array(samples[['AP', 'RH']])

XA_max = XA.max(axis=0)
XB_max = XB.max(axis=0)

XA /= XA_max
XB /= XB_max

N = Y.size

#XB has label
eta = 0.05
epoch = 100

#build base model
bThetaA = np.zeros(XA.shape[1])
bThetaB = np.zeros(XB.shape[1])
base_out = [] 

for i in range(epoch):
    UA = np.dot(XA, bThetaA)
    UB = np.dot(XB, bThetaB)
    UB_minus_Y = UB - Y

    d = np.add(UA, UB_minus_Y)

    gradient_A = np.dot(d, XA) / N
    gradient_B = np.dot(d, XB) / N

    bThetaA -= eta * gradient_A 
    bThetaB -= eta * gradient_B 

    loss = np.sum(d ** 2) / N

    base_out.append(np.append(np.append(bThetaA, bThetaB), loss))
    #out debug info
    print("bTheta:", np.append(bThetaA, bThetaB), " loss:", loss)
    
#build FL model
thetaA = np.zeros(XA.shape[1])
thetaB = np.zeros(XB.shape[1])
fl_out = []

#1. ARBITER generate pub and pri key, and send public key to PART A and PART B
public_key, private_key = paillier.generate_paillier_keypair(n_length=1024)

maskA = 0.01
maskB = 0.05

for i in range(epoch):
    #PART A, 
    UA = np.dot(XA, thetaA)

    UA_enc = encrypt(public_key, UA) 
    UA2_enc = encrypt(public_key, UA ** 2) 

    #send UA_enc, UA2_enc to PART B
    
    #PART B, the leader PART
    UB = np.dot(XB, thetaB)
    
    UB_minus_Y = UB - Y

    UB_minus_Y_enc = encrypt(public_key, UB_minus_Y)

    #calc d, and send it to PART A
    d = np.add(UA_enc, UB_minus_Y_enc)
    
    #encry loss, and send it to ARBITER
    UB_minus_Y2_enc = encrypt(public_key, UB_minus_Y ** 2)
    UA_enc_UBY_dot = np.dot(UA_enc, UB_minus_Y) * 2
    loss_enc = np.add(UA2_enc.sum(), UB_minus_Y2_enc.sum())
    loss_enc = np.add(loss_enc, UA_enc_UBY_dot)
    
    #PART B: calc enc gradient B, and send it to ARBITER
    gradient_B_enc = np.dot(d, XB) + public_key.encrypt(maskB)

    #PART A: got d and calc enc gradient A, and send ti to ARBITER
    gradient_A_enc = np.dot(d, XA) + public_key.encrypt(maskA)

    #ARBITER: decrypt gradient A, gradient B, loss
    gradient_A = decrypt(private_key, gradient_A_enc)
    gradient_B = decrypt(private_key, gradient_B_enc)
    loss = private_key.decrypt(loss_enc) / N
    
    #ARBITER: send decrypted gradient A to A, gradient B to B
    #gradient_A to PART A, and PART A updated
    gradient_A -= maskA
    thetaA -= eta * gradient_A / N

    #gradient_B to PART B, and PART B updated
    gradient_B -= maskB
    thetaB -= eta * gradient_B / N
    
    fl_out.append(np.append(np.append(thetaA, thetaB), loss))
    #out debug info
    print("theta:", np.append(thetaA, thetaB), " loss:", loss)

base_out = np.vstack(base_out)
fl_out = np.vstack(fl_out)
diff = np.abs(base_out - fl_out)
s = diff.mean(axis=0)
s1 = diff.mean(axis=0) / np.mean(np.abs(base_out), axis=0)

print("Train Diff:")
print("AE:", diff.sum(axis=0))
print("MAE:", s)
print("MAPE:", s1)

#inference
# AT	V	AP	RH	PE
samples = test_samples
Y = np.array(samples['PE'])
XA = np.array(samples[['AT', 'V']])
XB = np.array(samples[['AP', 'RH']])

XA /= XA_max
XB /= XB_max

N = Y.size

# base model: 
base_pred = np.dot(XA, bThetaA) + np.dot(XB, bThetaB)
base_err = np.abs(base_pred - Y)

#FL model:
#1. ARBITER send ids to PARTA, and PARTB
# blablabla....

#2. each PART inference
#2.1 PARTA cal UA, encrypt them, and send then to ARBITER 
UA = np.dot(XA, thetaA)
UA_enc = encrypt(public_key, UA) 

#2.2 PARTB cal UB, encrypt them, and send then to ARBITER 
UB = np.dot(XB, thetaB)
UB_enc = encrypt(public_key, UB) 

#3. ARBITER add UA_enc, UB_enc, and decrypt 
fl_pred = decrypt(private_key, UA_enc + UB_enc)
fl_err = np.abs(fl_pred - Y)

#DEBUG:
# test inf difference:
pred_diff = base_pred - fl_pred
print("Inference Diff:")
print(np.abs(pred_diff).mean())
print("AE:", np.abs(pred_diff).sum())
print("MAE:", np.abs(pred_diff).mean())
print("MAPE:", np.abs(diff).mean() / np.abs(base_pred).mean())
