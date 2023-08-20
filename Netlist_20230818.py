import numpy as np
import time
import math

start = time.time()

# Netlist 1
f = open("./NETLIST.txt", 'r')
CCT = ["XMC_A", "XMD_A", "XMC_B", "XMB_B", "XMD_B", "XMB_A", "XMA_C", "XMA_D", "XMA_B", "XMA_A"]
CCT_pair = [("XMC_A", "XMC_B"), ("XMD_A", "XMD_B"), ("XMB_B", "XMB_A"), ("XMA_C", "XMA_D"), ("XMA_B", "XMA_A")]
main_line = ["DET", "NET014"]
support_line = ["NET61<0>", "NET61<1>", "NET56<0>", "NET61<1>"]
ES_line = ['OUT', 'OUTB', 'IN', 'INB', 'IN_1', 'IN_2']

"""# Netlist 2
f = open("./NETLIST_230418_modified.txt", 'r') 
CCT = ["XMP1_0", "XMP1_1", "XMP2_0", "XMP2_1", "XMP3_0", "XMP3_1", "XMP4_0", "XMP4_1", "XMP5_0", "XMP5_1", "XMP6_0", "XMP6_1", "XMP7_0", "XMP7_1", "XMP8_0", "XMP8_1"] 
CCT_pair = [("XMP1_0", "XMP1_1"), ("XMP2_0", "XMP2_1"), ("XMP3_0", "XMP3_1"), ("XMP4_0", "XMP4_1"), ("XMP5_0", "XMP5_1"), ("XMP6_0", "XMP6_1"), ("XMP7_0", "XMP7_1"), ("XMP8_0", "XMP8_1")]
main_line = []
support_line = []
ES_line = ['INN', 'INP', 'OUT'] """


TR_min_width = 1.0
TS = 0.1
N_k = {} # dictionary : number of TR k
netlist = {} # dictionary : netlist information of TR k
NMOS_TR = [] # list : list of the NMOS TR
PMOS_TR = [] # list : list of PMOS TR
CC_TR = [] # list of CC TR
NOTCC_TR = [] # list : list of NOTCC TR
TW_k = {} # dictionary : width of TR k
TL_k = {} # dictionary : length of TR k
main_line_TR = []
support_line_TR = []
ES = {} # 외부 신호(ES_line)와 연결되어 있으면 1; 0, o.w
PMOS_CCT_max_width = 0
NMOS_CCT_max_width = 0
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
                for element in range(len(netlist[line.split()[0][:-3]])):
                    if netlist[line.split()[0][:-3]][element][-1] == '>':
                        netlist[line.split()[0][:-3]][element] = netlist[line.split()[0][:-3]][element][:-3]
                for element in ES_line:
                    if element in netlist[line.split()[0][:-3]]:
                        ES[line.split()[0][:-3]] = 1
                        break
                    else:
                        ES[line.split()[0][:-3]] = 0
                CC_TR.append(line.split()[0][:-3])
                NMOS_TR.append(line.split()[0][:-3])
                TR[count] = line.split()[0][:-3]
                count += 1
                TW_k[line.split()[0][:-3]] = float(line[line.index('w=') + 2 : line.index('l=') - 1])
                if TW_k[line.split()[0][:-3]] > NMOS_CCT_max_width:
                    NMOS_CCT_max_width = TW_k[line.split()[0][:-3]]
                TL_k[line.split()[0][:-3]] = float(line[line.index('l=') + 2 : line.index('nf=') - 1]) + 2 * 0.081
            else:
                N_k[line.split()[0][:-3]] += 1
        else: # NMOS 중 CC pair가 아닌 TR
            if line.split()[0][-1] == '>': # 동일한 TR이 2개 이상 존재하는 경우
                if line.split()[0][:-3] not in N_k:
                    TK_i[line.split()[0][:-3]] = 0
                    N_k[line.split()[0][:-3]] = 1
                    netlist[line.split()[0][:-3]] = line.split()[1:4]
                    for element in range(len(netlist[line.split()[0][:-3]])):
                        if netlist[line.split()[0][:-3]][element][-1] == '>':
                            netlist[line.split()[0][:-3]][element] = netlist[line.split()[0][:-3]][element][:-3]
                    for element in ES_line:
                        if element in netlist[line.split()[0][:-3]]:
                            ES[line.split()[0][:-3]] = 1
                            break
                        else:
                            ES[line.split()[0][:-3]] = 0
                    NOTCC_TR.append(line.split()[0][:-3])
                    NMOS_TR.append(line.split()[0][:-3])
                    TR[count] = line.split()[0][:-3]
                    count += 1
                    TW_k[line.split()[0][:-3]] = float(line[line.index('w=') + 2 : line.index('l=') - 1])
                    TL_k[line.split()[0][:-3]] = float(line[line.index('l=') + 2 : line.index('nf=') - 1]) + 2 * 0.081
                else:
                    N_k[line.split()[0][:-3]] += 1
            else: # 동일한 TR이 1개만 존재하는 경우
                if line.split()[0] not in N_k:
                    TK_i[line.split()[0]] = 0
                    N_k[line.split()[0]] = 1
                    netlist[line.split()[0]] = line.split()[1:4]
                    for element in range(len(netlist[line.split()[0]])):
                        if netlist[line.split()[0]][element][-1] == '>':
                            netlist[line.split()[0]][element] = netlist[line.split()[0]][element][:-3]
                    for element in ES_line:
                        if element in netlist[line.split()[0]]:
                            ES[line.split()[0]] = 1
                            break
                        else:
                            ES[line.split()[0]] = 0
                    NOTCC_TR.append(line.split()[0])
                    NMOS_TR.append(line.split()[0])
                    TR[count] = line.split()[0]
                    count += 1
                    TW_k[line.split()[0]] = float(line[line.index('w=') + 2 : line.index('l=') - 1])
                    TL_k[line.split()[0]] = float(line[line.index('l=') + 2 : line.index('nf=') - 1]) + 2 * 0.081
    elif 'PMOS' in line and 'nf' in line: # PMOS TR
        if line.split()[0][:-3] in CCT: # PMOS 중 CC pair인 TR
            if line.split()[0][:-3] not in N_k:
                TK_i[line.split()[0][:-3]] = 1
                N_k[line.split()[0][:-3]] = 1
                netlist[line.split()[0][:-3]] = line.split()[1:4]
                for element in range(len(netlist[line.split()[0][:-3]])):
                    if netlist[line.split()[0][:-3]][element][-1] == '>':
                        netlist[line.split()[0][:-3]][element] = netlist[line.split()[0][:-3]][element][:-3]
                for element in ES_line:
                    if element in netlist[line.split()[0][:-3]]:
                        ES[line.split()[0][:-3]] = 1
                        break
                    else:
                        ES[line.split()[0][:-3]] = 0
                CC_TR.append(line.split()[0][:-3])
                PMOS_TR.append(line.split()[0][:-3])
                TR[count] = line.split()[0][:-3]
                count += 1
                TW_k[line.split()[0][:-3]] = float(line[line.index('w=') + 2 : line.index('l=') - 1])
                if TW_k[line.split()[0][:-3]] > PMOS_CCT_max_width:
                    PMOS_CCT_max_width = TW_k[line.split()[0][:-3]]
                TL_k[line.split()[0][:-3]] = float(line[line.index('l=') + 2 : line.index('nf=') - 1]) + 2 * 0.081
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
                    for element in range(len(netlist[line.split()[0][:-3]])):
                        if netlist[line.split()[0][:-3]][element][-1] == '>':
                            netlist[line.split()[0][:-3]][element] = netlist[line.split()[0][:-3]][element][:-3]
                    for element in ES_line:
                        if element in netlist[line.split()[0][:-3]]:
                            ES[line.split()[0][:-3]] = 1
                            break
                        else:
                            ES[line.split()[0][:-3]] = 0
                    NOTCC_TR.append(line.split()[0][:-3])
                    PMOS_TR.append(line.split()[0][:-3])
                    TR[count] = line.split()[0][:-3]
                    count += 1
                    TW_k[line.split()[0][:-3]] = float(line[line.index('w=') + 2 : line.index('l=') - 1])
                    TL_k[line.split()[0][:-3]] = float(line[line.index('l=') + 2 : line.index('nf=') - 1]) + 2 * 0.081
                else:
                    N_k[line.split()[0][:-3]] += 1
            else: # 동일한 TR이 1개만 존재하는 경우
                if line.split()[0] not in N_k:
                    TK_i[line.split()[0]] = 1
                    N_k[line.split()[0]] = 1
                    netlist[line.split()[0]] = line.split()[1:4]
                    for element in range(len(netlist[line.split()[0]])):
                        if netlist[line.split()[0]][element][-1] == '>':
                            netlist[line.split()[0]][element] = netlist[line.split()[0]][element][:-3]
                    for element in ES_line:
                        if element in netlist[line.split()[0]]:
                            ES[line.split()[0]] = 1
                            break
                        else:
                            ES[line.split()[0]] = 0
                    NOTCC_TR.append(line.split()[0])
                    PMOS_TR.append(line.split()[0])
                    TR[count] = line.split()[0]
                    count += 1
                    TW_k[line.split()[0]] = float(line[line.index('w=') + 2 : line.index('l=') - 1])
                    TL_k[line.split()[0]] = float(line[line.index('l=') + 2 : line.index('nf=') - 1]) + 2 * 0.081

# C1,C2,C 생성
C = {} # dictionary : set of C1 + C2
C1 = {} # dictionary : set of C1
C2 = {} # dictionary : set of C2
count = 0
for i in range(len(CC_TR)):
    for j in range(i + 1, len(CC_TR)):
        if (CC_TR[i], CC_TR[j]) in CCT_pair or (CC_TR[j], CC_TR[i]) in CCT_pair:
            C1[count] = CC_TR[i] + ' ' + CC_TR[j]
            count += 1
for i in range(len(NOTCC_TR)):
    C2[len(C1) + i] = NOTCC_TR[i]
C = C1|C2

# PMOS CCT 중 최대 Width

# SG, WG, G_G, G_I, I_I, SG_SG, SG_O, O_O, TG, P, N_ip, TW_ip, PL_ip 생성
SG = [] # Short length gate TR
WG = [] # Wide length gate TR
G_G = [] # Set of required gate-gate connections. {(𝑖,𝑗)}
G_I = [] # Set of required gate-iso connections. {(𝑖,𝑗)}
I_I = [] # Set of required iso-iso connections. {(𝑖,𝑗)}
SG_SG = [] # Set of required short gate-short gate connections. {(𝑖,𝑗)|(𝑖,𝑗)∈[𝐺:𝐺]∩𝑖∈𝑆𝐺∩𝑗∈𝑆𝐺}
SG_O = [] # Set of required short gate-wide gate/source/drain connections. {(𝑖,𝑗)|(𝑖,𝑗)∈[𝐺:𝐺], 𝑖∈𝑆𝐺, 𝑗∈𝑊𝐺}∪{(𝑖,𝑗)|(𝑖,𝑗)∈[𝐺:𝐼], 𝑖∈𝑆𝐺}
O_O = [] # Set of required other-other connections.{(𝑖,𝑗)|(𝑖,𝑗)∈[𝐺:𝐺], 𝑖∈𝑊𝐺, 𝑗∈𝑊𝐺}∪{(𝑖,𝑗)|(𝑖,𝑗)∈[𝐺:𝐼], 𝑖∈𝑊𝐺}∪{(𝑖,𝑗)|(𝑖,𝑗)∈[𝐼:𝐼]}
TG = [] # Set of TRs whose gate is connected to. {𝑖│(𝑖,𝑗)∈[𝐺:𝐺]}∪{𝑗│(𝑖,𝑗)∈[𝐺:𝐺]}∪{𝑖│(𝑖,𝑗)∈[𝐺:𝐼]}
P = {} # dictionary : (0 : width = TR_min_width, 1 : width = TR_min_width * 2, ...} -> TW_ip 도출 가능
N_ip = {} # dictionary : number of TRs in pattern p of element i in C
TW_ip = {} # dictionary : width of TR in pattern p of element i in C
PL_ip = {} # dictionary : one side length in pattern p of element i in C
O_ip = {} # dictionary : if # of TR of pth pattern of ith TR is 1
SC = {} # dictionary : Set of connected TRs by each signal
AI = [] # Set of iso-iso connections {(𝑖,𝑗)} that must be center aligned.
SP = {} # dictionary : Set of signals that connect same TRs.

# sg, wg, N_ip, TW_ip, PL_ip, O_ip, P
for i in range(len(C1)):
    if TL_k[C1[i].split()[0]] <= 100: # 100은 임의의 threshold (모든 TR을 short TR로 만들기 위한)
        SG.append(i)
    else:
        WG.append(i)
    if TW_k[C1[i].split()[0]] // TR_min_width <= 1.0:
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
        PL_ip[(i, j)] = (N_k[C[i].split()[0]] + N_k[C[i].split()[1]]) * math.pow(2, len(P[i]) - 1 - j) * TL_k[C[i].split()[0]] / 2 \
                                  + math.floor(((N_k[C[i].split()[0]] + N_k[C[i].split()[1]]) * math.pow(2, len(P[i]) - 1 - j) - 1) / 2) * TS

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
    if TW_k[C2[len(C1) + i]] // TR_min_width <= 1.0:
        P[len(C1) + i] = [0]
    else:
        P[len(C1) + i] = list(range(int(math.log2(TW_k[C2[len(C1) + i]] // TR_min_width)) + 1))
    for j in range(len(P[len(C1) + i])):
        N_ip[(len(C1) + i, j)] = N_k[C2[len(C1) + i]] * math.pow(2, len(P[len(C1) + i]) - 1 - j)
        if N_ip[(len(C1) + i, j)] == 1.0:
            O_ip[(len(C1) + i, j)] = 1
        else:
            O_ip[(len(C1) + i, j)] = 0
        TW_ip[(len(C1) + i, j)] = TR_min_width * math.pow(2, P[len(C1) + i][j])
        PL_ip[(len(C1) + i, j)] = N_k[C[len(C1) + i]] * math.pow(2, len(P[len(C1) + i]) - 1 - j) * TL_k[C[len(C1) + i]] / 2  \
                                  + math.floor((N_k[C[len(C1) + i]] * math.pow(2, len(P[len(C1) + i]) - 1 - j) - 1) / 2) * TS

    if  TK_i[C2[len(C1) + i]] == 1 and TW_k[C2[len(C1) + i]] <= PMOS_CCT_max_width / 2 and N_k[C2[len(C1) + i]] >= 4:
        P[len(C1) + i].append(len(P[len(C1) + i]))
        N_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = N_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] / 2
        TW_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = TW_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] * 2
        PL_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = (PL_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] - TS) / 2
        O_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = 0
    elif TK_i[C2[len(C1) + i]] == 0 and TW_k[C2[len(C1) + i]] <= NMOS_CCT_max_width / 2 and N_k[C2[len(C1) + i]] >= 4:
        P[len(C1) + i].append(len(P[len(C1) + i]))
        N_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = N_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] / 2
        TW_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = TW_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] * 2
        PL_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = (PL_ip[(len(C1) + i, len(P[len(C1) + i]) - 2)] - TS) / 2
        O_ip[(len(C1) + i, len(P[len(C1) + i]) - 1)] = 0

# I_I, SG_SG, O_O, SG_0, TG, SC
for i in range(len(C1)):
    for j in range(len(C2)):
        if netlist[C1[i].split()[0]][0] != 'VDD' and netlist[C1[i].split()[0]][0] != 'VSS' and \
            (netlist[C1[i].split()[0]][0] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[0]][0] == netlist[C2[len(C1) + j]][2]):
            if (i, len(C1) + j) not in I_I:
                I_I.append((i, len(C1) + j))
            if (i, len(C1) + j) not in O_O:
                O_O.append((i, len(C1) + j))
            if netlist[C1[i].split()[0]][0] not in SC.keys():
                SC[netlist[C1[i].split()[0]][0]] = [i, len(C1) + j]
            else:
                if i not in SC[netlist[C1[i].split()[0]][0]]:
                    SC[netlist[C1[i].split()[0]][0]].append(i)
                if len(C1) + j not in SC[netlist[C1[i].split()[0]][0]]:
                    SC[netlist[C1[i].split()[0]][0]].append(len(C1) + j)
        if netlist[C1[i].split()[0]][2] != 'VDD' and netlist[C1[i].split()[0]][2] != 'VSS' and \
            (netlist[C1[i].split()[0]][2] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[0]][2] == netlist[C2[len(C1) + j]][2]):
            if (i, len(C1) + j) not in I_I:
                I_I.append((i, len(C1) + j))
            if (i, len(C1) + j) not in O_O:
                O_O.append((i, len(C1) + j))
            if netlist[C1[i].split()[0]][2] not in SC.keys():
                SC[netlist[C1[i].split()[0]][2]] = [i, len(C1) + j]
            else:
                if i not in SC[netlist[C1[i].split()[0]][2]]:
                    SC[netlist[C1[i].split()[0]][2]].append(i)
                if len(C1) + j not in SC[netlist[C1[i].split()[0]][2]]:
                    SC[netlist[C1[i].split()[0]][2]].append(len(C1) + j)
        if netlist[C1[i].split()[1]][0] != 'VDD' and netlist[C1[i].split()[1]][0] != 'VSS' and \
            (netlist[C1[i].split()[1]][0] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[1]][0] == netlist[C2[len(C1) + j]][2]):
            if (i, len(C1) + j) not in I_I:
                I_I.append((i, len(C1) + j))
            if (i, len(C1) + j) not in O_O:
                O_O.append((i, len(C1) + j))
            if netlist[C1[i].split()[1]][0] not in SC.keys():
                SC[netlist[C1[i].split()[1]][0]] = [i, len(C1) + j]
            else:
                if i not in SC[netlist[C1[i].split()[1]][0]]:
                    SC[netlist[C1[i].split()[1]][0]].append(i)
                if len(C1) + j not in SC[netlist[C1[i].split()[1]][0]]:
                    SC[netlist[C1[i].split()[1]][0]].append(len(C1) + j)
        if netlist[C1[i].split()[1]][2] != 'VDD' and netlist[C1[i].split()[1]][2] != 'VSS' and \
            (netlist[C1[i].split()[1]][2] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[1]][2] == netlist[C2[len(C1) + j]][2]):
            if (i, len(C1) + j) not in I_I:
                I_I.append((i, len(C1) + j))
            if (i, len(C1) + j) not in O_O:
                O_O.append((i, len(C1) + j))
            if netlist[C1[i].split()[1]][2] not in SC.keys():
                SC[netlist[C1[i].split()[1]][2]] = [i, len(C1) + j]
            else:
                if i not in SC[netlist[C1[i].split()[1]][2]]:
                    SC[netlist[C1[i].split()[1]][2]].append(i)
                if len(C1) + j not in SC[netlist[C1[i].split()[1]][2]]:
                    SC[netlist[C1[i].split()[1]][2]].append(len(C1) + j)

        if ((netlist[C2[len(C1) + j]][1] != 'VDD' and netlist[C2[len(C1) + j]][1] != 'VSS') and (
                netlist[C1[i].split()[0]][1] == netlist[C2[len(C1) + j]][1] or netlist[C1[i].split()[1]][1] ==
                netlist[C2[len(C1) + j]][1])):  # G-G
            G_G.append((i, len(C1) + j))
            TG.append(i)
            TG.append(len(C1) + j)
            if i in SG and len(C1) + j in SG:
                SG_SG.append((i, len(C1) + j))
            elif i in SG and len(C1) + j in WG:
                SG_O.append((i, len(C1) + j))
            elif i in WG and len(C1) + j in WG:
                O_O.append((i, len(C1) + j))

        elif ((netlist[C2[len(C1) + j]][0] != 'VDD' and netlist[C2[len(C1) + j]][0] != 'VSS') and \
              (netlist[C1[i].split()[0]][1] == netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[1]][1] ==
               netlist[C2[len(C1) + j]][0] or netlist[C1[i].split()[0]][1] == netlist[C2[len(C1) + j]][2] or
               netlist[C1[i].split()[1]][1] == netlist[C2[len(C1) + j]][2])):  # G-ISO
            G_I.append((i, len(C1) + j))
            TG.append(i)
            if i in SG:
                SG_O.append((i, len(C1) + j))
            elif i in WG:
                O_O.append((i, len(C1) + j))
        elif ((netlist[C2[len(C1) + j]][1] != 'VDD' and netlist[C2[len(C1) + j]][1] != 'VSS') and \
              (netlist[C1[i].split()[0]][0] == netlist[C2[len(C1) + j]][1] or netlist[C1[i].split()[1]][0] ==
               netlist[C2[len(C1) + j]][1] \
               or netlist[C1[i].split()[0]][2] == netlist[C2[len(C1) + j]][1] or netlist[C1[i].split()[1]][2] ==
               netlist[C2[len(C1) + j]][1])):  # ISO-G
            G_I.append((len(C1) + j, i))
            TG.append(len(C1) + i)
            if len(C1) + j in SG:
                SG_O.append((len(C1) + j, i))
            elif len(C1) + j in WG:
                O_O.append((len(C1) + j, i))

for i in range(len(C1)):
    for j in range(i + 1, len(C1)):
        if netlist[C1[i].split()[0]][0] != 'VDD' and netlist[C1[i].split()[0]][0] != 'VSS'\
            and (netlist[C1[i].split()[0]][0] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[0]][0] == netlist[C1[j].split()[0]][2] \
            or netlist[C1[i].split()[0]][0] == netlist[C1[j].split()[1]][0] or netlist[C1[i].split()[0]][0] == netlist[C1[j].split()[1]][2]):
            if (i, j) not in I_I:
                I_I.append((i, j))
            if (i, j) not in O_O:
                O_O.append((i, j))
            if netlist[C1[i].split()[0]][0] not in SC.keys():
                SC[netlist[C1[i].split()[0]][0]] = [i, j]
            else:
                if i not in SC[netlist[C1[i].split()[0]][0]]:
                    SC[netlist[C1[i].split()[0]][0]].append(i)
                if j not in SC[netlist[C1[i].split()[0]][0]]:
                    SC[netlist[C1[i].split()[0]][0]].append(j)
        if netlist[C1[i].split()[0]][2] != 'VDD' and netlist[C1[i].split()[0]][2] != 'VSS'\
            and (netlist[C1[i].split()[0]][2] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[0]][2] == netlist[C1[j].split()[0]][2] \
            or netlist[C1[i].split()[0]][2] == netlist[C1[j].split()[1]][0] or netlist[C1[i].split()[0]][2] == netlist[C1[j].split()[1]][2]):
            if (i, j) not in I_I:
                I_I.append((i, j))
            if (i, j) not in O_O:
                O_O.append((i, j))
            if netlist[C1[i].split()[0]][2] not in SC.keys():
                SC[netlist[C1[i].split()[0]][2]] = [i, j]
            else:
                if i not in SC[netlist[C1[i].split()[0]][2]]:
                    SC[netlist[C1[i].split()[0]][2]].append(i)
                if j not in SC[netlist[C1[i].split()[0]][2]]:
                    SC[netlist[C1[i].split()[0]][2]].append(j)
        if netlist[C1[i].split()[1]][0] != 'VDD' and netlist[C1[i].split()[1]][0] != 'VSS' \
            and (netlist[C1[i].split()[1]][0] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[1]][0] == netlist[C1[j].split()[0]][2] \
            or netlist[C1[i].split()[1]][0] == netlist[C1[j].split()[1]][0] or netlist[C1[i].split()[1]][0] == netlist[C1[j].split()[1]][2]):
            if (i, j) not in I_I:
                I_I.append((i, j))
            if (i, j) not in O_O:
                O_O.append((i, j))
            if netlist[C1[i].split()[1]][0] not in SC.keys():
                SC[netlist[C1[i].split()[1]][0]] = [i, j]
            else:
                if i not in SC[netlist[C1[i].split()[1]][0]]:
                    SC[netlist[C1[i].split()[1]][0]].append(i)
                if j not in SC[netlist[C1[i].split()[1]][0]]:
                    SC[netlist[C1[i].split()[1]][0]].append(j)
        if netlist[C1[i].split()[1]][2] != 'VDD' and netlist[C1[i].split()[1]][2] != 'VSS'\
            and (netlist[C1[i].split()[1]][2] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[1]][2] == netlist[C1[j].split()[0]][2] \
            or netlist[C1[i].split()[1]][2] == netlist[C1[j].split()[1]][0] or netlist[C1[i].split()[1]][2] == netlist[C1[j].split()[1]][2]):
            if (i, j) not in I_I:
                I_I.append((i, j))
            if (i, j) not in O_O:
                O_O.append((i, j))
            if netlist[C1[i].split()[1]][2] not in SC.keys():
                SC[netlist[C1[i].split()[1]][2]] = [i, j]
            else:
                if i not in SC[netlist[C1[i].split()[1]][2]]:
                    SC[netlist[C1[i].split()[1]][2]].append(i)
                if j not in SC[netlist[C1[i].split()[1]][2]]:
                    SC[netlist[C1[i].split()[1]][2]].append(j)

        if ((netlist[C1[i].split()[0]][1] != 'VDD' and netlist[C1[i].split()[0]][1] != 'VSS') and (
                netlist[C1[i].split()[0]][1] == netlist[C1[j].split()[0]][1] or netlist[C1[i].split()[0]][1] ==
                netlist[C1[j].split()[1]][1])) \
                or ((netlist[C1[i].split()[1]][1] != 'VDD' and netlist[C1[i].split()[1]][1] != 'VSS') and (
                netlist[C1[i].split()[1]][1] == netlist[C1[j].split()[0]][1] or netlist[C1[i].split()[1]][1] ==
                netlist[C1[j].split()[1]][1])):  # G-G
            G_G.append((i, j))
            TG.append(i)
            TG.append(j)
            if i in SG and j in SG:
                SG_SG.append((i, j))
            elif i in SG and j in WG:
                SG_O.append((i, j))
            elif i in WG and j in WG:
                O_O.append((i, j))
        elif ((netlist[C1[i].split()[0]][1] != 'VDD' and netlist[C1[i].split()[0]][1] != 'VSS') \
              and (netlist[C1[i].split()[0]][1] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[0]][1] ==
                   netlist[C1[j].split()[1]][0] \
                   or netlist[C1[i].split()[0]][1] == netlist[C1[j].split()[0]][2] or netlist[C1[i].split()[0]][1] ==
                   netlist[C1[j].split()[1]][2])) \
                or ((netlist[C1[i].split()[0]][1] != 'VDD' and netlist[C1[i].split()[0]][1] != 'VSS')
                    and (netlist[C1[i].split()[1]][1] == netlist[C1[j].split()[0]][0] or netlist[C1[i].split()[1]][1] ==
                         netlist[C1[j].split()[1]][0] \
                         or netlist[C1[i].split()[1]][1] == netlist[C1[j].split()[0]][2] or netlist[C1[i].split()[1]][
                             1] == netlist[C1[j].split()[1]][2])):  # G-ISO
            G_I.append((i, j))
            TG.append(i)
            if i in SG:
                SG_O.append((i, j))
            elif i in WG:
                O_O.append((i, j))
        elif ((netlist[C1[j].split()[0]][1] != 'VDD' and netlist[C1[j].split()[0]][1] != 'VSS') and (
                netlist[C1[i].split()[0]][0] == netlist[C1[j].split()[0]][1] or netlist[C1[i].split()[1]][0] ==
                netlist[C1[j].split()[0]][1])) \
                or ((netlist[C1[j].split()[1]][1] != 'VDD' and netlist[C1[j].split()[1]][1] != 'VSS') and (
                netlist[C1[i].split()[0]][2] == netlist[C1[j].split()[1]][1] or netlist[C1[i].split()[1]][2] ==
                netlist[C1[j].split()[1]][1])):  # ISO-G
            G_I.append((j, i))
            TG.append(j)
            if j in SG:
                SG_O.append((j, i))
            elif j in WG:
                O_O.append((j, i))

for i in range(len(C2)):
    for j in range(i + 1, len(C2)):
        if (netlist[C2[len(C1) + i]][0] != 'VDD' and netlist[C2[len(C1) + i]][0] != 'VSS') and\
                (netlist[C2[len(C1) + i]][0] == netlist[C2[len(C1) + j]][0] or netlist[C2[len(C1) + i]][0] == netlist[C2[len(C1) + j]][2]):
            if (len(C1) + i, len(C1) + j) not in I_I:
                I_I.append((len(C1) + i, len(C1) + j))
            if (len(C1) + i, len(C1) + j) not in O_O:
                O_O.append((len(C1) + i, len(C1) + j))
            if netlist[C2[len(C1) + i]][0] not in SC.keys():
                SC[netlist[C2[len(C1) + i]][0]] = [len(C1) + i, len(C1) + j]
            else:
                if len(C1) + i not in SC[netlist[C2[len(C1) + i]][0]]:
                    SC[netlist[C2[len(C1) + i]][0]].append(len(C1) + i)
                if len(C1) + j not in SC[netlist[C2[len(C1) + i]][0]]:
                    SC[netlist[C2[len(C1) + i]][0]].append(len(C1) + j)
        if (netlist[C2[len(C1) + i]][2] != 'VDD' and netlist[C2[len(C1) + i]][2] != 'VSS') and \
                (netlist[C2[len(C1) + i]][2] == netlist[C2[len(C1) + j]][0] or netlist[C2[len(C1) + i]][2] == netlist[C2[len(C1) + j]][2]):
            if (len(C1) + i, len(C1) + j) not in I_I:
                I_I.append((len(C1) + i, len(C1) + j))
            if (len(C1) + i, len(C1) + j) not in O_O:
                O_O.append((len(C1) + i, len(C1) + j))
            if netlist[C2[len(C1) + i]][2] not in SC.keys():
                SC[netlist[C2[len(C1) + i]][2]] = [len(C1) + i, len(C1) + j]
            else:
                if len(C1) + i  not in SC[netlist[C2[len(C1) + i]][2]]:
                    SC[netlist[C2[len(C1) + i]][2]].append(len(C1) + i)
                if len(C1) + j not in SC[netlist[C2[len(C1) + i]][2]]:
                    SC[netlist[C2[len(C1) + i]][2]].append(len(C1) + j)

        if netlist[C2[len(C1) + i]][1] != 'VDD' and netlist[C2[len(C1) + i]][1] != 'VSS' and netlist[C2[len(C1) + i]][
            1] == netlist[C2[len(C1) + j]][1]:  # G-G
            G_G.append((len(C1) + i, len(C1) + j))
            TG.append(len(C1) + i)
            TG.append(len(C1) + j)
            if len(C1) + i in SG and len(C1) + j in SG:
                SG_SG.append((len(C1) + i, len(C1) + j))
            elif len(C1) + i in SG and len(C1) + j in WG:
                SG_O.append((len(C1) + i, len(C1) + j))
            elif len(C1) + i in WG and len(C1) + j in WG:
                O_O.append((len(C1) + i, len(C1) + j))
        elif ((netlist[C2[len(C1) + i]][1] != 'VDD' and netlist[C2[len(C1) + i]][1] != 'VSS') and (
                netlist[C2[len(C1) + i]][1] == netlist[C2[len(C1) + j]][0] or netlist[C2[len(C1) + i]][1] ==
                netlist[C2[len(C1) + j]][2])):  # G-ISO
            G_I.append((len(C1) + i, len(C1) + j))
            TG.append(len(C1) + i)
            if len(C1) + i in SG:
                SG_O.append((len(C1) + i, len(C1) + j))
        elif ((netlist[C2[len(C1) + j]][1] != 'VDD' and netlist[C2[len(C1) + j]][1] != 'VSS') and (
                netlist[C2[len(C1) + i]][0] == netlist[C2[len(C1) + j]][1] or netlist[C2[len(C1) + i]][2] ==
                netlist[C2[len(C1) + j]][1])):  # ISO-G
            G_I.append((len(C1) + j, len(C1) + i))
            TG.append(len(C1) + j)
            if len(C1) + j in SG:
                SG_O.append((len(C1) + j, len(C1) + i))

TG = list(set(TG))
for key in SC.keys():
    if len(SC[key]) == 2:
        if tuple(SC[key]) not in AI:
            AI.append(tuple(SC[key]))

for i in SC.keys():
    for j in SC.keys():
        if i < j and SC[i] == SC[j]:
            SP[i, j] = SC[i]

# 보조 라인 B_ij
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
print('ES :', ES)
print('SC :', SC)
print('AI :', AI)
print('SP :', SP)
print(netlist)
