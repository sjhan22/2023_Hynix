import numpy as np
import time
import math

start = time.time()
f = open("C:/Users/한선진/Desktop/2023_하이닉스/NETLIST_230418_수정.txt", 'r')

TR_min_width = 1.0
TS = 0.5
N_k = {} # dictionary : number of TR k
netlist = {} # dictionary : netlist information of TR k
NMOS_TR = [] # list : list of the NMOS TR
PMOS_TR = [] # list : list of PMOS TR
CC_TR = [] # list of CC TR
NOTCC_TR = [] # list : list of NOTCC TR
TW_k = {} # dictionary : width of TR k
TL_k = {} # dictionary : length of TR k

CCT = ["XMP1_0", "XMP1_1", "XMP2_0", "XMP2_1", "XMP3_0", "XMP3_1", "XMP4_0", "XMP4_1", "XMP5_0", "XMP5_1", "XMP6_0", "XMP6_1", "XMP7_0", "XMP7_1", "XMP8_0", "XMP8_1"] # CCT 직접입력
main_line = []
main_line_TR = []
support_line = []
support_line_TR = []

ES_line = ['INN', 'INP']
ES = {} # 외부 신호(ES_line)와 연결되어 있으면 1; 0, o.w

PMOS_CCT_max_width = 0
NMOS_CCT_max_width = 0

# TR, TK_i 생성
TR = {} # dictionary : list of TR (netlist에 나오는 순서대로 indexing)
TK_i = {} # dictionary : =1, if TR i is PMOS; 0 , o.w
count = 0
while True:
    line = f.readline()
    if not line : break
    if 'NMOS' in line and '$bulk2=VVB' in line: # NMOS TR
        if line.split()[0][:-3] in CCT: # NMOS 중 CC pair인 TR
            if line.split()[0][:-3] not in N_k:
                TK_i[line.split()[0][:-3]] = 0
                N_k[line.split()[0][:-3]] = 1
                netlist[line.split()[0][:-3]] = line.split()[1:4]
                if ES_line[0] in netlist[line.split()[0][:-3]] or ES_line[1] in netlist[line.split()[0][:-3]]:
                    ES[line.split()[0][:-3]] = 1
                else:
                    ES[line.split()[0][:-3]] = 0
                CC_TR.append(line.split()[0][:-3])
                NMOS_TR.append(line.split()[0][:-3])
                TR[count] = line.split()[0][:-3]
                count += 1
                TW_k[line.split()[0][:-3]] = float(line.split()[-5][2:])
                if TW_k[line.split()[0][:-3]] > NMOS_CCT_max_width:
                    NMOS_CCT_max_width = TW_k[line.split()[0][:-3]]
                TL_k[line.split()[0][:-3]] = float(line.split()[-4][2:]) + 2 * 0.081
            else:
                N_k[line.split()[0][:-3]] += 1
        else: # NMOS 중 CC pair가 아닌 TR
            if line.split()[0][-1] == '>': # 동일한 TR이 2개 이상 존재하는 경우
                if line.split()[0][:-3] not in N_k:
                    TK_i[line.split()[0][:-3]] = 0
                    N_k[line.split()[0][:-3]] = 1
                    netlist[line.split()[0][:-3]] = line.split()[1:4]
                    if ES_line[0] in netlist[line.split()[0][:-3]] or ES_line[1] in netlist[line.split()[0][:-3]]:
                        ES[line.split()[0][:-3]] = 1
                    else:
                        ES[line.split()[0][:-3]] = 0
                    NOTCC_TR.append(line.split()[0][:-3])
                    NMOS_TR.append(line.split()[0][:-3])
                    TR[count] = line.split()[0][:-3]
                    count += 1
                    TW_k[line.split()[0][:-3]] = float(line.split()[-5][2:])
                    TL_k[line.split()[0][:-3]] = float(line.split()[-4][2:]) + 2 * 0.081
                else:
                    N_k[line.split()[0][:-3]] += 1
            else: # 동일한 TR이 1개만 존재하는 경우
                if line.split()[0] not in N_k:
                    TK_i[line.split()[0]] = 0
                    N_k[line.split()[0]] = 1
                    netlist[line.split()[0]] = line.split()[1:4]
                    if ES_line[0] in netlist[line.split()[0]] or ES_line[1] in netlist[line.split()[0]]:
                        ES[line.split()[0]] = 1
                    else:
                        ES[line.split()[0]] = 0
                    NOTCC_TR.append(line.split()[0])
                    NMOS_TR.append(line.split()[0])
                    TR[count] = line.split()[0]
                    count += 1
                    TW_k[line.split()[0]] = float(line.split()[-5][2:])
                    TL_k[line.split()[0]] = float(line.split()[-4][2:]) + 2 * 0.081
    elif 'PMOS' in line and 'nf' in line: # PMOS TR
        if line.split()[0][:-3] in CCT: # PMOS 중 CC pair인 TR
            if line.split()[0][:-3] not in N_k:
                TK_i[line.split()[0][:-3]] = 1
                N_k[line.split()[0][:-3]] = 1
                netlist[line.split()[0][:-3]] = line.split()[1:4]
                if ES_line[0] in netlist[line.split()[0][:-3]] or ES_line[1] in netlist[line.split()[0][:-3]]:
                    ES[line.split()[0][:-3]] = 1
                else:
                    ES[line.split()[0][:-3]] = 0
                CC_TR.append(line.split()[0][:-3])
                PMOS_TR.append(line.split()[0][:-3])
                TR[count] = line.split()[0][:-3]
                count += 1
                TW_k[line.split()[0][:-3]] = float(line.split()[-4][2:])
                if TW_k[line.split()[0][:-3]] > PMOS_CCT_max_width:
                    PMOS_CCT_max_width = TW_k[line.split()[0][:-3]]
                TL_k[line.split()[0][:-3]] = float(line.split()[-3][2:]) + 2 * 0.081
                if line.split()[1] in main_line:
                    main_line_TR.append(line.split()[0][:5])
                elif line.split()[1] in support_line:
                    support_line_TR.append(line.split()[0][:5])
            else:
                N_k[line.split()[0][:-3]] += 1
        else: # PMOS 중 CC pair가 아닌 TR
            if line.split()[0][-1] == '>': # 동일한 TR이 2개 이상 존재하는 경우
                if line.split()[0][:-3] not in N_k:
                    TK_i[line.split()[0][:-3]] = 1
                    N_k[line.split()[0][:-3]] = 1
                    netlist[line.split()[0][:-3]] = line.split()[1:4]
                    if ES_line[0] in netlist[line.split()[0][:-3]] or ES_line[1] in netlist[line.split()[0][:-3]]:
                        ES[line.split()[0][:-3]] = 1
                    else:
                        ES[line.split()[0][:-3]] = 0
                    NOTCC_TR.append(line.split()[0][:-3])
                    PMOS_TR.append(line.split()[0][:-3])
                    TR[count] = line.split()[0][:-3]
                    count += 1
                    TW_k[line.split()[0][:-3]] = float(line.split()[-4][2:])
                    TL_k[line.split()[0][:-3]] = float(line.split()[-3][2:]) + 2 * 0.081
                else:
                    N_k[line.split()[0][:-3]] += 1
            else: # 동일한 TR이 1개만 존재하는 경우
                if line.split()[0] not in N_k:
                    TK_i[line.split()[0]] = 1
                    N_k[line.split()[0]] = 1
                    netlist[line.split()[0]] = line.split()[1:4]
                    if ES_line[0] in netlist[line.split()[0]] or ES_line[1] in netlist[line.split()[0]]:
                        ES[line.split()[0]] = 1
                    else:
                        ES[line.split()[0]] = 0
                    NOTCC_TR.append(line.split()[0])
                    PMOS_TR.append(line.split()[0])
                    TR[count] = line.split()[0]
                    count += 1
                    TW_k[line.split()[0]] = float(line.split()[-4][2:])
                    TL_k[line.split()[0]] = float(line.split()[-3][2:]) + 2 * 0.081


# C1,C2,C 생성
C = {} # dictionary : set of C1 + C2
C1 = {} # dictionary : set of C1
C2 = {} # dictionary : set of C2
count = 0
for i in range(len(CC_TR)):
    for j in range(i + 1, len(CC_TR)):
        if CC_TR[i][:-2] == CC_TR[j][:-2]:
            C1[count] = CC_TR[i] + ' ' + CC_TR[j]
            count += 1
for i in range(len(NOTCC_TR)):
    C2[len(C1) + i] = NOTCC_TR[i]
C = C1|C2

# PMOS CCT 중 최대 Width

# SG, WG, G_G, G_I, I_I, SG_SG, SG_O, O_O, TG, P, N_ip, TW_ip, PL_ip 생성
SG = []
WG = []
G_G = []
G_I = []
I_I = []
SG_SG = []
SG_O = []
O_O = []
TG = []
P = {} # dictionary : (0 : width = TR_min_width, 1 : width = TR_min_width * 2, ...} -> TW_ip 도출 가능
N_ip = {} # dictionary : number of TRs in pattern p of element i in C
TW_ip = {} # dictionary : width of TR in pattern p of element i in C
PL_ip = {} # dictionary : one side length in pattern p of element i in C
O_ip = {} # dictionary : if # of TR of pth pattern of ith TR is 1

for i in range(len(C1)):
    if TL_k[C1[i].split()[0]] <= 100: # 100은 임의의 threshold (모든 TR을 short TR로 만들기 위한)
        SG.append(i)
    else:
        WG.append(i)
    if TW_k[C1[i].split()[0]] // TR_min_width == 0:
        P[i] = [0]
    else:
        P[i] = list(range(int(math.log2(TW_k[C1[i].split()[0]] // TR_min_width)) + 1))
    for j in range(len(P[i])):
        N_ip[(i, j)] = (N_k[C1[i].split()[0]] + N_k[C1[i].split()[1]]) * math.pow(2, len(P[i]) - 1 - j)
        if N_ip[(i, j)] == 1.0:
            O_ip[(i, j)] = 1
        else:
            O_ip[(i, j)] = 0
        TW_ip[(i, j)] = TR_min_width * math.pow(2, P[i][j])
        PL_ip[(i, j)] = 2 * N_k[C[i].split()[0]] * math.pow(2, len(P[i]) - 1 - j) * TL_k[C[i].split()[0]] + \
                        (2 * N_k[C[i].split()[0]] * math.pow(2, len(P[i]) - 1 - j) - 1) * TS
    if  TK_i[C1[i].split()[0]] == 1 and TW_k[C1[i].split()[0]] <= PMOS_CCT_max_width / 2 and N_k[C1[i].split()[0]] + N_k[C1[i].split()[1]] >= 4:
        P[i].append(len(P[i]))
        N_ip[(i, len(P[i]) - 1)] = N_ip[(i, len(P[i]) - 2)] / 2
        TW_ip[(i, len(P[i]) - 1)] = TW_ip[(i, len(P[i]) - 2)] * 2
        PL_ip[(i, len(P[i]) - 1)] = (PL_ip[(i, len(P[i]) - 2)] - TS) / 2
        O_ip[(i, len(P[i]) - 1)] = 0
    elif TK_i[C1[i].split()[0]] == 0 and TW_k[C1[i].split()[0]] <= NMOS_CCT_max_width / 2 and N_k[C1[i].split()[0]] + N_k[C1[i].split()[1]] >= 4:
        P[i].append(len(P[i]))
        N_ip[(i, len(P[i]) - 1)] = N_ip[(i, len(P[i]) - 2)] / 2
        TW_ip[(i, len(P[i]) - 1)] = TW_ip[(i, len(P[i]) - 2)] * 2
        PL_ip[(i, len(P[i]) - 1)] = (PL_ip[(i, len(P[i]) - 2)] - TS) / 2
        O_ip[(i, len(P[i]) - 1)] = 0

for i in range(len(C2)):
    if TL_k[C2[len(C1) + i]] <= 100: # 100은 임의의 threshold (모든 TR을 short TR로 만들기 위한)
        SG.append(len(C1) + i)
    else:
        WG.append(len(C1) + i)
    if TW_k[C2[len(C1) + i]] // TR_min_width == 0:
        P[len(C1) + i] = [0]
    else:
        P[len(C1) + i] = list(range(int(math.log2(TW_k[C2[len(C1) + i]] // TR_min_width)) + 1))
    for j in range(len(P[len(C1) + i])):
        N_ip[(len(C1) + i, j)] = N_k[C2[len(C1) + i]] * math.pow(2, len(P[len(C1) + i]) - 1 - j)
        if N_ip[(len(C1) + i, j)] == 1.0:
            O_ip[(len(C1) + i, j)] = 1
        else:
            O_ip[(len(C1) + i, j)] = 0
        TW_ip[(len(C1) + i, j)] = 0.5 * math.pow(2, P[len(C1) + i][j])
        PL_ip[(len(C1) + i, j)] = N_k[C[len(C1) + i]] * math.pow(2, len(P[len(C1) + i]) - 1 - j) * TL_k[C[len(C1) + i]] / 2\
                                  + (N_k[C[len(C1) + i]] * math.pow(2, len(P[len(C1) + i]) - 1 - j) - 1) / 2 * TS

    if  TK_i[C2[len(C1) + i]] == 1 and TW_k[C2[len(C1) + i]] <= PMOS_CCT_max_width / 2 and N_k[C2[len(C1) + i]] + N_k[C2[len(C1) + i]] >= 4:
        P[len(C1) + i].append(len(P[len(C1) + i]))
        N_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = N_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] / 2
        TW_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = TW_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] * 2
        PL_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = (PL_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] - TS) / 2
        O_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = 0
    elif TK_i[C2[len(C1) + i]] == 0 and TW_k[C2[len(C1) + i]] <= NMOS_CCT_max_width / 2 and N_k[C2[len(C1) + i]] + N_k[C2[len(C1) + i]] >= 4:
        P[len(C1) + i].append(len(P[len(C1) + i]))
        N_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = N_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] / 2
        TW_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = TW_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] * 2
        PL_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = (PL_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] - TS) / 2
        O_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = 0

# I_I, G_G, I,I
for i in range(len(C1)):
    for j in range(len(C2)):
        if netlist[C1[i].split()[0]][0] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[0]][0] == netlist[C2[len(C1) + j]][2]\
        or netlist[C1[i].split()[0]][2] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[0]][2] == netlist[C2[len(C1) + j]][2]\
        or netlist[C1[i].split()[1]][0] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[1]][0] == netlist[C2[len(C1) + j]][2]\
        or netlist[C1[i].split()[1]][2] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[1]][2] == netlist[C2[len(C1) + j]][2]:
            I_I.append((i, len(C1) + j))
            O_O.append((i, len(C1) + j))

        if netlist[C1[i].split()[0]][1] == netlist[C2[len(C1) + j]][1] or netlist[C1[i].split()[1]][1] == netlist[C2[len(C1) + j]][1]: # G-G
            G_G.append((i, len(C1) + j))
            TG.append(i)
            TG.append(len(C1) + j)
            if i in SG and len(C1) + j in SG:
                SG_SG.append((i, len(C1) + j))
            elif i in SG and len(C1) + j in WG:
                SG_O.append((i, len(C1) + j))
            elif i in WG and len(C1) + j in WG:
                O_O.append((i, len(C1) + j))

        elif netlist[C1[i].split()[0]][1] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[1]][1] == netlist[C2[len(C1) + j]][0]\
          or netlist[C1[i].split()[0]][1] == netlist[C2[len(C1) + j]][2] or netlist[C1[i].split()[1]][1] == netlist[C2[len(C1) + j]][2]: # G-ISO
            G_I.append((i, len(C1) + j))
            TG.append(i)
            if i in SG:
                SG_O.append((i, len(C1) + j))
            elif i in WG:
                O_O.append((i, len(C1) + j))
        elif netlist[C1[i].split()[0]][0] == netlist[C2[len(C1) + j]][1] or netlist[C1[i].split()[1]][0] == netlist[C2[len(C1) + j]][1]\
          or netlist[C1[i].split()[0]][2] == netlist[C2[len(C1) + j]][1] or netlist[C1[i].split()[1]][2] == netlist[C2[len(C1) + j]][1]: # ISO-G
            G_I.append((len(C1) + j, i))
            TG.append(len(C1) + i)
            if len(C1) + j in SG:
                SG_O.append((len(C1) + j, i))
            elif len(C1) + j in WG:
                O_O.append((len(C1) + j, i))

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
            I_I.append((i, j))
            O_O.append((i, j))

        if netlist[C1[i].split()[0]][1] == netlist[C1[j].split()[0]][1] or netlist[C1[i].split()[0]][1] == netlist[C1[j].split()[1]][1]\
        or netlist[C1[i].split()[1]][1] == netlist[C1[j].split()[0]][1] or netlist[C1[i].split()[1]][1] == netlist[C1[j].split()[1]][1]: # G-G
            G_G.append((i, j))
            TG.append(i)
            TG.append(j)
            if i in SG and j in SG:
                SG_SG.append((i, j))
            elif i in SG and j in WG:
                SG_O.append((i, j))
            elif i in WG and j in WG:
                O_O.append((i, j))
        elif netlist[C1[i].split()[0]][1] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[0]][1] == netlist[C1[j].split()[1]][0]\
          or netlist[C1[i].split()[0]][1] == netlist[C1[j].split()[0]][2] or netlist[C1[i].split()[0]][1] == netlist[C1[j].split()[1]][2]\
          or netlist[C1[i].split()[1]][1] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[1]][1] == netlist[C1[j].split()[1]][0]\
          or netlist[C1[i].split()[1]][1] == netlist[C1[j].split()[0]][2] or netlist[C1[i].split()[1]][1] == netlist[C1[j].split()[1]][2]: # G-ISO
            G_I.append((i, j))
            TG.append(i)
            if i in SG:
                SG_O.append((i, j))
            elif i in WG:
                O_O.append((i, j))
        elif netlist[C1[i].split()[0]][0] == netlist[C1[j].split()[0]][1] or netlist[C1[i].split()[0]][2] == netlist[C1[j].split()[1]][1]\
          or netlist[C1[i].split()[1]][0] == netlist[C1[j].split()[0]][1] or netlist[C1[i].split()[1]][2] == netlist[C1[j].split()[1]][1]: # ISO-G
            G_I.append((j, i))
            TG.append(j)
            if j in SG:
                SG_O.append((j, i))
            elif j in WG:
                O_O.append((j, i))

for i in range(len(C2)):
    for j in range(i + 1, len(C2)):
        if netlist[C2[len(C1) + i]][0] == netlist[C2[len(C1) + j]][0] or netlist[C2[len(C1) + i]][0] == netlist[C2[len(C1) + j]][2] \
        or netlist[C2[len(C1) + i]][2] == netlist[C2[len(C1) + j]][0] or netlist[C2[len(C1) + i]][2] == netlist[C2[len(C1) + j]][2]:
            I_I.append((len(C1) + i, len(C1) + j))
            O_O.append((len(C1) + i, len(C1) + j))

        if netlist[C2[len(C1) + i]][1] == netlist[C2[len(C1) + j]][1]: # G-G
            G_G.append((len(C1) + i, len(C1) + j))
            TG.append(len(C1) + i)
            TG.append(len(C1) + j)
            if len(C1) + i in SG and len(C1) + j in SG:
                SG_SG.append((len(C1) + i, len(C1) + j))
            elif len(C1) + i in SG and len(C1) + j in WG:
                SG_O.append((len(C1) + i, len(C1) + j))
            elif len(C1) + i in WG and len(C1) + j in WG:
                O_O.append((len(C1) + i, len(C1) + j))
        elif netlist[C2[len(C1) + i]][1] == netlist[C2[len(C1) + j]][0] or netlist[C2[len(C1) + i]][1] == netlist[C2[len(C1) + j]][2]: # G-ISO
            G_I.append((len(C1) + i, len(C1) + j))
            TG.append(len(C1) + i)
            if len(C1) + i in SG:
                SG_O.append((len(C1) + i, len(C1) + j))
        elif netlist[C2[len(C1) + i]][0] == netlist[C2[len(C1) + j]][1] or netlist[C2[len(C1) + i]][2] == netlist[C2[len(C1) + j]][1]: # ISO-G
            G_I.append((len(C1) + j, len(C1) + i))
            TG.append(len(C1) + j)
            if len(C1) + j in SG:
                SG_O.append((len(C1) + j, len(C1) + i))

TG = list(set(TG))

# 보조 라인 B_ij 생성
B_ij = np.zeros((len(C), len(C))) # matrix
for i in range(len(C1)):
    for j in range(len(C1)):
        if C1[i].split()[0] in support_line_TR and C1[j].split()[0] in main_line_TR:
            B_ij[i][j] = 1

f.close()
end = time.time()
print('elapsed time :', end-start)
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
print('TW_k :', TW_k)
print('N_k :', N_k)
print('main_line_TR : ', main_line_TR)
print('support_line_TR : ', support_line_TR)
print('External Signal : ', ES)
print('NMOS_CCT_max_width :' , NMOS_CCT_max_width)
print('PMOS_CCT_max_width :', PMOS_CCT_max_width)
print('TL_k :', TL_k)
print('SG :', SG)
print('WG :', WG)
print('G_G :', G_G)
print('G_I :', G_I)
print('I_I :', I_I)
print('SG_SG :', SG_SG)
print('SG_O :', SG_O)
print('O_O :', O_O)
print('TG :', TG)
print(netlist)