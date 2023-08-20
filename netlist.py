import numpy as np
import time
import math

start = time.time()
f = open("C:/Users/한선진/Desktop/2023_하이닉스/NETLIST.txt", 'r')

TR_min_width = 0.5
TS = 0.5
N_k = {} # dictionary : number of TR k
netlist = {} # dictionary : netlist information of TR k
NMOS_TR = [] # list : list of the NMOS TR
PMOS_TR = [] # list : list of PMOS TR
CC_TR = [] # list of CC TR
NOTCC_TR = [] # list : list of NOTCC TR
TW_k = {} # dictionary : width of TR k
TL_k = {} # dictionary : length of TR k
main_line = ["DET", "NET014"]
main_line_TR = []
support_line = ["NET61<0>", "NET61<1>", "NET56<0>", "NET61<1>"]
support_line_TR = []

# TR, TK_i 생성
TR = {} # dictionary : list of TR (netlist에 나오는 순서대로 indexing)
TK_i = {} # dictionary : =1, if TR i is PMOS; 0 , o.w
count = 0
while True:
    line = f.readline()
    if not line : break
    if 'NMOS' in line and '$bulk2=VVB' in line: # NMOS TR
        if line[3] == '_': # NMOS 중 CC pair인 TR
            if line.split()[0][:5] not in N_k:
                TK_i[line.split()[0][:5]] = 0
                N_k[line.split()[0][:5]] = 1
                netlist[line.split()[0][:5]] = line.split()[1:4]
                CC_TR.append(line.split()[0][:5])
                NMOS_TR.append(line.split()[0][:5])
                TR[count] = line.split()[0][:5]
                count += 1
                TW_k[line.split()[0][:5]] = float(line.split()[-4][2:])
                TL_k[line.split()[0][:5]] = float(line.split()[-3][2:]) + 2 * 0.081
            else:
                N_k[line.split()[0][:5]] += 1
        else: # NMOS 중 CC pair가 아닌 TR
            if line.split()[0][-1] == '>': # 동일한 TR이 2개 이상 존재하는 경우
                if line.split()[0][:-3] not in N_k:
                    TK_i[line.split()[0][:-3]] = 0
                    N_k[line.split()[0][:-3]] = 1
                    netlist[line.split()[0][:-3]] = line.split()[1:4]
                    NOTCC_TR.append(line.split()[0][:-3])
                    NMOS_TR.append(line.split()[0][:-3])
                    TR[count] = line.split()[0][:-3]
                    count += 1
                    TW_k[line.split()[0][:-3]] = float(line.split()[-4][2:])
                    TL_k[line.split()[0][:-3]] = float(line.split()[-3][2:]) + 2 * 0.081
                else:
                    N_k[line.split()[0][:-3]] += 1
            else: # 동일한 TR이 1개만 존재하는 경우
                if line.split()[0] not in N_k:
                    TK_i[line.split()[0]] = 0
                    N_k[line.split()[0]] = 1
                    netlist[line.split()[0]] = line.split()[1:4]
                    NOTCC_TR.append(line.split()[0])
                    NMOS_TR.append(line.split()[0])
                    TR[count] = line.split()[0]
                    count += 1
                    TW_k[line.split()[0]] = float(line.split()[-4][2:])
                    TL_k[line.split()[0]] = float(line.split()[-3][2:]) + 2 * 0.081
    elif 'PMOS' in line and 'nf' in line: # PMOS TR
        if line[3] == '_': # PMOS 중 CC pair인 TR
            if line.split()[0][:5] not in N_k:
                TK_i[line.split()[0][:5]] = 1
                N_k[line.split()[0][:5]] = 1
                netlist[line.split()[0][:5]] = line.split()[1:4]
                CC_TR.append(line.split()[0][:5])
                PMOS_TR.append(line.split()[0][:5])
                TR[count] = line.split()[0][:5]
                count += 1
                TW_k[line.split()[0][:5]] = float(line.split()[-3][2:])
                TL_k[line.split()[0][:5]] = float(line.split()[-2][2:]) + 2 * 0.081
                if line.split()[1] in main_line:
                    main_line_TR.append(line.split()[0][:5])
                elif line.split()[1] in support_line:
                    support_line_TR.append(line.split()[0][:5])
            else:
                N_k[line.split()[0][:5]] += 1
        else: # PMOS 중 CC pair가 아닌 TR
            if line.split()[0][-1] == '>': # 동일한 TR이 2개 이상 존재하는 경우
                if line.split()[0][:-3] not in N_k:
                    TK_i[line.split()[0][:-3]] = 1
                    N_k[line.split()[0][:-3]] = 1
                    netlist[line.split()[0][:-3]] = line.split()[1:4]
                    NOTCC_TR.append(line.split()[0][:-3])
                    PMOS_TR.append(line.split()[0][:-3])
                    TR[count] = line.split()[0][:-3]
                    count += 1
                    TW_k[line.split()[0][:-3]] = float(line.split()[-3][2:])
                    TL_k[line.split()[0][:-3]] = float(line.split()[-2][2:]) + 2 * 0.081
                else:
                    N_k[line.split()[0][:5]] += 1
            else: # 동일한 TR이 1개만 존재하는 경우
                if line.split()[0] not in N_k:
                    TK_i[line.split()[0]] = 1
                    N_k[line.split()[0]] = 1
                    netlist[line.split()[0]] = line.split()[1:4]
                    NOTCC_TR.append(line.split()[0])
                    PMOS_TR.append(line.split()[0])
                    TR[count] = line.split()[0]
                    count += 1
                    TW_k[line.split()[0]] = float(line.split()[-3][2:])
                    TL_k[line.split()[0]] = float(line.split()[-2][2:]) + 2 * 0.081

# C1,C2,C 생성
C = {} # dictionary : set of C1 + C2
C1 = {} # dictionary : set of C1
C2 = {} # dictionary : set of C2
count = 0
for i in range(len(CC_TR)):
    for j in range(i + 1, len(CC_TR)):
        if CC_TR[i][:3] == CC_TR[j][:3] and N_k[CC_TR[i]] == N_k[CC_TR[j]]:
            C1[count] = CC_TR[i] + ' ' + CC_TR[j]
            count += 1
for i in range(len(NOTCC_TR)):
    C2[len(C1) + i] = NOTCC_TR[i]
C = C1|C2

# P, N_ip, TW_ip, PL_ip 생성
P = {} # dictionary : (0 : width = TR_min_width, 1 : width = TR_min_width * 2, ...} -> TW_ip 도출 가능
N_ip = {} # dictionary : number of TRs in pattern p of element i in C
TW_ip = {} # dictionary : width of TR in pattern p of element i in C
PL_ip = {} # dictionary : one side length in pattern p of element i in C
O_ip = {} # dictionary : if # of TR of pth pattern of ith TR is 1

for i in range(len(C1)):
    P[i] = list(range(int(math.log2(TW_k[C1[i].split()[0]] // TR_min_width)) + 1))
    for j in range(len(P[i])):
        N_ip[(i, j)] = N_k[C1[i].split()[0]] * 2 * math.pow(2, len(P[i]) - 1 - j)
        if N_ip[(i, j)] == 1.0:
            O_ip[(i, j)] = 1
        else:
            O_ip[(i, j)] = 0
        TW_ip[(i, j)] = 0.5 * math.pow(2, P[i][j])
        PL_ip[(i, j)] = 2 * N_k[C[i].split()[0]] * math.pow(2, len(P[i]) - 1 - j) * TL_k[C[i].split()[0]] + \
                        (2 * N_k[C[i].split()[0]] * math.pow(2, len(P[i]) - 1 - j) - 1) * TS

for i in range(len(C2)):
    P[len(C1) + i] = list(range(int(math.log2(TW_k[C2[len(C1) + i]] // TR_min_width)) + 1))
    for j in range(len(P[len(C1) + i])):
        N_ip[(len(C1) + i, j)] = N_k[C2[len(C1) + i]] * math.pow(2, len(P[len(C1) + i]) - 1 - j)
        if N_ip[(len(C1) + i, j)] == 1.0:
            O_ip[(len(C1) + i, j)] = 1
        else:
            O_ip[(len(C1) + i, j)] = 0
        TW_ip[(len(C1) + i, j)] = 0.5 * math.pow(2, P[len(C1) + i][j])
        PL_ip[(len(C1) + i, j)] = N_k[C[len(C1) + i]] * math.pow(2, len(P[len(C1) + i]) - 1 - j) * TL_k[C[len(C1) + i]] \
                                  + (N_k[C[len(C1) + i]] * math.pow(2, len(P[len(C1) + i]) - 1 - j) - 1) * TS


# R_ij 생성
R_ij = np.zeros((len(C), len(C))) # matrix
for i in range(len(C1)):
    for j in range(len(C2)):
        if netlist[C1[i].split()[0]][0] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[0]][0] == netlist[C2[len(C1) + j]][2]\
                or netlist[C1[i].split()[0]][2] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[0]][2] == netlist[C2[len(C1) + j]][2]\
                or netlist[C1[i].split()[1]][0] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[1]][0] == netlist[C2[len(C1) + j]][2]\
                or netlist[C1[i].split()[1]][2] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[1]][2] == netlist[C2[len(C1) + j]][2]:
            R_ij[i][len(C1) + j] = 1

for i in range(len(C1)):
    for j in range(i + 1, len(C1)):
        if netlist[C1[i].split()[0]][0] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[0]][0] == netlist[C1[j].split()[0]][2]\
                or netlist[C1[i].split()[0]][2] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[0]][2] == netlist[C1[j].split()[0]][2]\
                or netlist[C1[i].split()[0]][0] == netlist[C1[j].split()[1]][0] or netlist[C1[i].split()[0]][0] == netlist[C1[j].split()[1]][2]\
                or netlist[C1[i].split()[0]][2] == netlist[C1[j].split()[1]][0] or netlist[C1[i].split()[0]][0] == netlist[C1[j].split()[1]][2]\
                or netlist[C1[i].split()[1]][0] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[1]][0] == netlist[C1[j].split()[0]][2]\
                or netlist[C1[i].split()[1]][2] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[1]][2] == netlist[C1[j].split()[0]][2]\
                or netlist[C1[i].split()[1]][0] == netlist[C1[j].split()[1]][0] or netlist[C1[i].split()[1]][0] == netlist[C1[j].split()[1]][2]\
                or netlist[C1[i].split()[1]][2] == netlist[C1[j].split()[1]][0] or netlist[C1[i].split()[1]][2] == netlist[C1[j].split()[1]][2]:
            R_ij[i][j] = 1

for i in range(len(C2)):
    for j in range(i + 1, len(C2)):
        if netlist[C2[len(C1) + i]][0] == netlist[C2[len(C1) + j]][0] or netlist[C2[len(C1) + i]][0] == netlist[C2[len(C1) + j]][2] \
            or netlist[C2[len(C1) + i]][2] == netlist[C2[len(C1) + j]][0] or netlist[C2[len(C1) + i]][2] == netlist[C2[len(C1) + j]][2]:
            R_ij[len(C1) + i][len(C1) + j] = 1

# G_ij 생성
G_ij = np.zeros((len(C), len(C))) # matrix
for i in range(len(C1)):
    for j in range(len(C2)):
        if TK_i[C1[i].split()[0]] == TK_i[C2[len(C1) + j]] and (netlist[C1[i].split()[0]][1] == netlist[C2[len(C1) + j]][1] or netlist[C1[i].split()[1]][1] == netlist[C2[len(C1) + j]][1]):
            G_ij[i][len(C1) + j] = 1

for i in range(len(C1)):
    for j in range(i + 1, len(C1)):
        if TK_i[C1[i].split()[0]] == TK_i[C1[j].split()[0]] and (netlist[C1[i].split()[0]][1] == netlist[C1[j].split()[0]][1] or netlist[C1[i].split()[0]][1] == netlist[C1[j].split()[1]][1]\
                or netlist[C1[i].split()[1]][1] == netlist[C1[j].split()[0]][1] or netlist[C1[i].split()[1]][1] == netlist[C1[j].split()[1]][1]):
            G_ij[i][j] = 1

for i in range(len(C2)):
    for j in range(i + 1, len(C2)):
        if TK_i[C2[len(C1) + i]] == TK_i[C2[len(C1) + j]] and netlist[C2[len(C1) + i]][1] == netlist[C2[len(C1) + j]][1]:
            G_ij[len(C1) + i][len(C1) + j] = 1

# 보조 라인 B_ij 생성
B_ij = np.zeros((len(C), len(C))) # matrix
for i in range(len(C1)):
    for j in range(len(C1)):
        if C1[i].split()[0] in support_line_TR and C1[j].split()[0] in main_line_TR:
            B_ij[i][j] = 1


f.close()
end = time.time()
print('<Sets>')
print('C1 :', C1)
print('C2 :', C2)
print('C :', C)
print('P :', P)
print('TR :', TR)
print('<Parameters>')
print('TK_i :', TK_i)
print('N_ip:', N_ip)
print('O_ip:', O_ip)
print('TW_ip', TW_ip)
print('PL_ip', PL_ip)
print('R_ij :', R_ij)
print('G_ij :', G_ij)
print('elapsed time :', end-start)
print('TW_k', TW_k)
print('N_k', N_k)
print('B_ij', B_ij)
print('main_line_TR :', main_line_TR)
print('support_line_TR :', support_line_TR)