import sys
sys.path.append("D:/[SK Hynix] Placement and Routing/NETLIST 전처리_선진")
sys.path.append("D:/[SK Hynix] Placement and Routing/TR 배치 시각화")

# NETLIST_230418_수정.txt
from Netlist_20230712_수정 import *
from Init_Visualization import *

import gurobipy as gp
from gurobipy import GRB
import numpy as np

def process_solution(m, C, TW, PL, O):
    x_coord = []
    y_coord = []
    split_distance = []
    selected_pattern = []
    gate_direction = []

    for var in m.getVars():
        if var.varName[0] == "x":
            x_coord.append((var.varName, var.x))

        if var.varName[0] == "y":
            y_coord.append((var.varName, var.x))

        if var.varName[0] == "d":
            split_distance.append((var.varName, var.x))

        if var.varName[0] == "u":
            if var.x >= 0.9:
                selected_pattern.append((var.varName, var.x)) 

    selected_TW = []
    selected_PL = []
    selected_O = []

    for idx, pattern in enumerate(selected_pattern):
        tr = idx
        p = int(pattern[0][-1])
        selected_TW.append(TW[tr][p])
        selected_PL.append(PL[tr][p])
        selected_O.append(O[tr][p])

    TR_names = {0:"OP", 1:"MN", 2:"CD", 3:"EF", 4:"AB", 5:"KI", 6:"GH", 7:"IJ", 8:"Z5", 9:"Z2", 10:"Z3", 11:"Z4", 12:"Z8", 13:"Z12", 14:"Z13", 15:"Z11", 16:"Z9", 17:"Z10", 18:"Z7", 19:"Z6" }
    print("\n# (x, y) coordinates and split distances")
    for idx, coord in enumerate(zip(x_coord, y_coord)):   
        print(f"{C[idx]} ({TR_names[idx]}) Coordinate: {coord[0][0], coord[1][0]} => {coord[0][1], coord[1][1]}")
        print(f"TW / PL: {selected_TW[idx]} / {selected_PL[idx]}, d[{idx}]: {split_distance[idx][1]}\n") 

    obj = m.getObjective()
    print(f"Objective function value: {obj.getValue()}")

    x_coords = [x_coord[i][1] for i in range(len(x_coord))]
    y_coords = [y_coord[i][1] for i in range(len(y_coord))]
    split_distances = [split_distance[i][1] for i in range(len(split_distance))]

    return selected_TW, selected_PL, selected_O, x_coords, y_coords, split_distances, gate_direction  

def solve_placement_opt(timelimit, mipGap, sets, parameters, row_restriction):
    
    """Sets"""
    C = sets["C"]     # Union of C1 and C2
    C1 = sets["C1"]    # Set of Main TR
    C2 = sets["C2"]    # Set of Independent TR
    B = sets["B_i"]     # Set of Sub TR for main TR 
    P = sets["P"]       # Set of TR patterns
    SG = sets["SG"]    # Set of short gate TR
    WG = sets["WG"]    # Set of wide gate TR
    GG = sets["G_G"]    # Set of required gate-gate connections 
    GI = sets["G_I"]    # Set of required gate-iso connections
    II = sets["I_I"]    # Set of required iso-iso connections
    SG_SG = sets["SG_SG"] # Set of required short gate-short gate connections 
    SG_O = sets["SG_O"] # Set of required short gate-wide gate/source/drain connections
    O_O = sets["O_O"]  # Set of required other-other connections
    TG = sets["TG"]   # Set of TRs whose gate is connected to 
    
    
    """Parameters"""
    W = parameters["W"]
    H = parameters["H"]
    MS = parameters["MS"]
    TS = parameters["TS_ij"]
    RS1 = parameters["RS1"]
    RS2 = parameters["RS2"]
    RS3 = parameters["RS3"]
    TW = parameters["TW_ip"]
    PL = parameters["PL_ip"]
    N = parameters["N_ip"]
    O = parameters["O_ip"]
    TK = parameters["TK_i"]
    ES = parameters["ES_i"]
    alpha0 = parameters["alpha0_ipjq"]
    alpha1 = parameters["alpha1_ipjq"]
    alpha2 = parameters["alpha2_ipjq"]
    lambda1 = parameters["lambda1"]
    lambda2 = parameters["lambda2"]
    lambda3 = parameters["lambda3"]
    lambda4 = parameters["lambda4"]
    M = max(H, W) * 50
    
    num_TR = len(TW)
    num_row = parameters["K"]
    
    temp_II = []
    list_II = []
    for val in II:
        if (val[0] in C1) & (val[1] in C1):
            temp_II.append(val)
            list_II.append(val[0])
            list_II.append(val[1])
    list_II = list(set(list_II)) 

    
    with gp.Env(empty=True) as env:
        if mipGap != -1:
            # env.setParam('OutputFlag', 1)
            env.setParam('MIPGap', mipGap) 
        env.start()
        with gp.Model(env=env) as m:
            m.setParam(GRB.Param.TimeLimit, timelimit)
               
            """Decision Variables"""
            u = [[m.addVar(vtype=GRB.BINARY, name="u" + str(i) + str(p)) for p in range(len(P[i]))] for i in range(num_TR)]
            a = [[m.addVar(vtype=GRB.BINARY, name="a" + str(i) + str(k)) for k in range(num_row)] for i in range(num_TR)]
            z = [[[m.addVar(vtype=GRB.BINARY, name="z" + str(i) + str(j) + str(k)) for j in range(num_TR)] for i in range(num_TR)] for k in range(num_row)]
            s = [[m.addVar(vtype=GRB.BINARY, name="s" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            l = [[m.addVar(vtype=GRB.BINARY, name="l" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            b = [[m.addVar(vtype=GRB.BINARY, name="b" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            v = [[m.addVar(vtype=GRB.BINARY, name="v" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            o = [m.addVar(vtype=GRB.BINARY, name="o" + str(i)) for i in range(num_TR)]
            g = [m.addVar(vtype=GRB.BINARY, name="g" + str(k)) for k in range(num_row)]
            t = [m.addVar(vtype=GRB.BINARY, name="t" + str(k)) for k in range(num_row)]
            r = [m.addVar(vtype=GRB.BINARY, name="r" + str(k)) for k in range(num_row)]
            td = [m.addVar(vtype=GRB.BINARY, name="td" + str(i)) for i in range(num_TR)]
            tau = [[m.addVar(vtype=GRB.BINARY, name="tau" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]     
            
            x = [m.addVar(vtype=GRB.CONTINUOUS, name="x" + str(i)) for i in range(num_TR)]
            y = [m.addVar(vtype=GRB.CONTINUOUS, name="y" + str(i)) for i in range(num_TR)]
            tw = [m.addVar(vtype=GRB.CONTINUOUS, name="tw" + str(i)) for i in range(num_TR)]
            pl = [m.addVar(vtype=GRB.CONTINUOUS, name="pl" + str(i)) for i in range(num_TR)]
            qu = [m.addVar(vtype=GRB.CONTINUOUS, name="qu" + str(k)) for k in range(num_row)] 
            ql = [m.addVar(vtype=GRB.CONTINUOUS, name="ql" + str(k)) for k in range(num_row)] 
            tr = [m.addVar(vtype=GRB.CONTINUOUS, name="tr" + str(i)) for i in range(num_TR)] 
            d = [m.addVar(vtype=GRB.CONTINUOUS, name="d" + str(i)) for i in range(num_TR)]
            ru = [m.addVar(vtype=GRB.CONTINUOUS, name="ru" + str(k)) for k in range(num_row)]
            rl = [m.addVar(vtype=GRB.CONTINUOUS, name="rl" + str(k)) for k in range(num_row)]
            ru_prime = [m.addVar(vtype=GRB.CONTINUOUS, name="ru_prime" + str(k)) for k in range(num_row)]
            rl_prime = [m.addVar(vtype=GRB.CONTINUOUS, name="rl_prime" + str(k)) for k in range(num_row)]
            e1 = [[m.addVar(vtype=GRB.CONTINUOUS, name="e1" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            e2 = [[m.addVar(vtype=GRB.CONTINUOUS, name="e2" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            e3 = [[m.addVar(vtype=GRB.CONTINUOUS, name="e3" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            px = [[m.addVar(vtype=GRB.CONTINUOUS, name="px" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            wx = [[m.addVar(vtype=GRB.CONTINUOUS, name="wx" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            mx = [m.addVar(vtype=GRB.CONTINUOUS, name="mx" + str(k)) for k in range(num_row)]
            my = m.addVar(vtype=GRB.CONTINUOUS, name="my", lb=0)
            f1 = [m.addVar(vtype=GRB.CONTINUOUS, name="f1" + str(i)) for i in range(num_TR)]
            _y2 = [m.addVar(vtype=GRB.CONTINUOUS, name="_y2" + str(i)) for i in range(num_TR)]
            xc = [m.addVar(vtype=GRB.CONTINUOUS, name="xc" + str(i)) for i in range(num_TR)]
            wd = [m.addVar(vtype=GRB.CONTINUOUS, name="wd" + str(i)) for i in range(num_TR)]
            
            # zeta = [m.addVar(vtype=GRB.BINARY, name="zeta" + str(i)) for i in range(num_TR)]
            # xi = [[m.addVar(vtype=GRB.CONTINUOUS, name="xi" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            # rho = [[m.addVar(vtype=GRB.BINARY, name="rho" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            # phi = [[m.addVar(vtype=GRB.BINARY, name="phi" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            phi = [m.addVar(vtype=GRB.BINARY, name="phi" + str(i)) for i in range(num_TR)]
            psi = [[m.addVar(vtype=GRB.BINARY, name="psi" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            
            """Objective Function"""  
            m.setObjective(sum(e1[i][j] for i in range(num_TR) for j in range(num_TR) if (i, j) in SG_SG) + 
                           sum(e2[i][j] for i in range(num_TR) for j in range(num_TR) if (i, j) in SG_O) +
                           sum(e3[i][j] for i in range(num_TR) for j in range(num_TR) if (i, j) in O_O) +
                           (lambda1 * sum(f1[i] for i in range(num_TR))) + 
                           (lambda2 * sum(wd[i] for i in range(num_TR))) -
                           (lambda3 * my) +
                           (lambda4 * sum(tau[i][j] for i in range(num_TR) for j in range(num_TR) if (i != j))),
                           GRB.MINIMIZE)
            
            
            """Constraints"""
            # C01
            for i in range(num_TR):
                 m.addConstr(sum([u[i][p] for p in range(len(P[i]))]) == 1, "c01-" + str(i))
            
            # C02
            for i in range(num_TR):
                m.addConstr(o[i] == sum([O[i][p] * u[i][p] for p in range(len(P[i]))]), "c02-" + str(i))
            
            # C03
            for i in range(num_TR):
                m.addConstr(tw[i] == sum([TW[i][p] * u[i][p] for p in range(len(P[i]))]), "c03-" + str(i))
            
            # C04
            for i in range(num_TR):
                m.addConstr(pl[i] == sum([PL[i][p] * u[i][p] for p in range(len(P[i]))]), "c04-" + str(i))

            # C05
            for i in range(num_TR):
                m.addConstr(sum([a[i][k] for k in range(num_row)]) == 1, "c05-" + str(i))
            
            # C06
            for i in range(num_TR):
                for j in range(num_TR):
                    if i != j: 
                        for k in range(num_row):
                            m.addConstr(z[k][i][j] >= a[i][k] + a[j][k] - 1, "c06-1-" + str(i) + str(j) + str(k))
                            m.addConstr(z[k][i][j] <= 0.5 * (a[i][k] + a[j][k]), "c06-2-" + str(i) + str(j) + str(k))
            
            # C07
            for i in range(num_TR):
                for j in range(num_TR): 
                    if i != j:
                        m.addConstr(s[i][j] == sum(z[k][i][j] for k in range(num_row)), "c07-" + str(i) + str(j))                   
                                  
            # C08
            for i in range(num_TR):
                for j in range(num_TR):
                    if i != j:
                        m.addConstr(l[i][j] + l[j][i] >= s[i][j], "c08-1-" + str(i) + str(j))
                        m.addConstr(l[i][j] + l[j][i] <= s[i][j], "c08-2-" + str(i) + str(j))
                        
            # C09
            for i in range(num_TR):
                if i in C1.keys():
                    for j in range(num_TR):
                        if j in B[i]:
                            m.addConstr(s[i][j] == 1, "c09-" + str(i) + str(j))
            
            # C10
            for i in range(num_TR):
                if i in C1.keys():
                    for j in range(num_TR):
                        if j in B[i]:
                            m.addConstr(l[j][i] == 1, "c10-" + str(i) + str(j))
        
            # C11
            for i in range(num_TR):
                if i in C1.keys():
                    for j in range(num_TR):
                        if j in B[i]:
                            m.addConstr(l[i][j] == 0, "c11-" + str(i) + str(j))
                
            # C12
            for i in range(num_TR):
                if i in C1.keys():
                    m.addConstr(xc[i] == x[i] + pl[i] + (0.5 * d[i]), "c12-" + str(i))
                    
            # C13
            for i in range(num_TR):
                if i in C1.keys():
                    for j in range(num_TR):
                        if j in B[i]:
                            m.addConstr(xc[i] == x[j] + pl[j] + (0.5 * d[j]), "c13-" + str(i) + str(j))
            
            # for i in range(num_TR):
            #     if i in C1.keys():
            #         for j in range(num_TR):
            #             if j in B[i]:
            #                 m.addConstr(tau[i][j] == 0)
                            
            # C14
            for i in range(num_TR):
                if i in C.keys():
                    m.addConstr(x[i] + (2 * pl[i]) + d[i] <= W, "c14-" + str(i))
                    
            # C15
            for i in range(num_TR):
                m.addConstr(y[i] + tw[i] <= H, "c15-" + str(i))
                
            # C16
            for i in range(num_TR):
                if i in C1.keys():
                    m.addConstr(d[i] >= MS, "c16-" + str(i))
                    
            # C17
            for i in range(num_TR):
                if i in C2.keys():
                    m.addConstr(W * (1 - o[i]) >= d[i], "c17-1-" + str(i))
                    m.addConstr(d[i] >= MS * (1 - o[i]), "c17-2-" + str(i))
            
            # C18
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j):
                        m.addConstr(px[i][j] >= x[i] + (2 * pl[i]) + d[i], "c18" + str(i) + str(j))
            
            # C19
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j):
                        m.addConstr(px[i][j] >= x[j] + (2 * pl[j]) + d[j], "c19" + str(i) + str(j))

            # C20
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j):
                        m.addConstr(wx[i][j] >= px[i][j] - x[i], "c20" + str(i) + str(j))

            # C21
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j):
                        m.addConstr(wx[i][j] >= px[i][j] - x[j], "c21" + str(i) + str(j))
            
            # C22
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & (j in C2.keys()):
                        m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 - l[i][j] - s[i][j] - o[j])), "c22-" + str(i) + str(j))
                        
            # C23
            for i in range(num_TR):
                if i in C2.keys():
                    for j in range(num_TR):
                        if (i != j):
                            m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 - l[i][j] - s[i][j] - o[i])), "c23-" + str(i) + str(j))

            # C24
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & (j in C2.keys()):
                        m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (2 + o[j] - l[i][j] - s[i][j])), "c24-" + str(i) + str(j))
            
            # C25
            for i in range(num_TR):
                if i in C2.keys():
                    for j in range(num_TR):
                        if (i != j):
                            m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (2 + o[i] - l[i][j] - s[i][j])), "c25-" + str(i) + str(j))
                                          
#             for i in range(num_TR):
#                 for j in range(num_TR):
#                     if (i != j) & (j in C2.keys()):
#                         m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 + o[j] - l[i][j] - s[i][j] - o[i])))
                        
#             for i in range(num_TR):
#                 if i in C2.keys():
#                     for j in range(num_TR):
#                         if (i != j):
#                             m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 + o[i] - l[i][j] - s[i][j] - o[j])))
                            
#             for i in range(num_TR):
#                 for j in range(num_TR):
#                     if (i != j) & (j in C2.keys()):
#                         m.addConstr(x[i] + pl[i] + TS[i][j] <= x[j] + (W * (2 + o[i] + o[j] + tau[i][j] - l[i][j] - s[i][j])))
                        
#             for i in range(num_TR):
#                 if i in C2.keys():
#                     for j in range(num_TR):
#                         if (i != j):
#                             m.addConstr(x[i] + pl[i] + TS[i][j] <= x[j] + (W * (2 + o[i] + o[j] + tau[i][j] - l[i][j] - s[i][j])))
                            
#             for i in range(num_TR):
#                 for j in range(num_TR):
#                     if (i != j) & (j in C2.keys()):
#                         m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 + o[i] + o[j] - tau[i][j] - l[i][j] - s[i][j])))
                        
#             for i in range(num_TR):
#                 if i in C2.keys():
#                     for j in range(num_TR):
#                         if (i != j):
#                             m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 + o[i] + o[j] - tau[i][j] - l[i][j] - s[i][j]))) 
                                      
            # C26
            for i in range(num_TR):
                if i in C1.keys():
                    for j in range(num_TR):
                        if (i != j) & (j in C1.keys()):
                            m.addConstr(xc[i] <= xc[j] + (W * tau[i][j]), "c26-1-" + str(i) + str(j))
                            m.addConstr(xc[i] >= xc[j] - (W * tau[i][j]), "c26-2-" + str(i) + str(j))
            
            # C27
            for i in range(num_TR):
                if i in C1.keys():
                    for j in range(num_TR):
                        if (i != j) & (j in C1.keys()):
                            m.addConstr(tau[i][j] == tau[j][i], "c27-" + str(i) + str(j))

            
            # C28
            for i in range(num_TR):
                if i in C1.keys():
                    for j in range(num_TR):
                        if (i != j) & (j in C1.keys()) & ((i, j) in II):
                            m.addConstr(xc[i] <= xc[j] + (W * (s[i][j] + tau[i][j])), "c28-1-" + str(i) + str(j))
                            m.addConstr(xc[i] >= xc[j] - (W * (s[i][j] + tau[i][j])), "c28-2-" + str(i) + str(j))
          
            # C29
            for i in range(num_TR):
                if i in C1.keys():
                    for j in range(num_TR):
                        if (i != j) & (j in C1.keys()):
                            m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 - tau[i][j] - l[i][j] - s[i][j])), "c29-" + str(i) + str(j))
                            
            # C30
            for i in range(num_TR):
                if i in C1.keys():
                    for j in range(num_TR):
                        if (i != j) & (j in C1.keys()):
                            m.addConstr(x[i] + pl[i] + TS[i][j] <= x[j] + (W * (2 + tau[i][j] - l[i][j] - s[i][j])), "c30-" + str(i) + str(j))

#             for i in range(num_TR):
#                 if (i in C1.keys()):
#                     for j in range(num_TR):
#                         if (i != j) & (j in C1.keys()):
#                             m.addConstr(xc[i] <= xc[j] + (M * rho[i][j]))
#                             m.addConstr(xc[i] >= xc[j] - (M * (1 - rho[i][j])))
#                             m.addConstr(xi[i][j] >= xc[i] - xc[j])
#                             m.addConstr(xi[i][j] <= xc[i] - xc[j] + (M * (1 - rho[i][j])))
#                             m.addConstr(xi[i][j] >= xc[j] - xc[i])
#                             m.addConstr(xi[i][j] <= xc[j] - xc[i] + (M * rho[i][j]))
#                             m.addConstr(tau[i][j] >= 1 - (M * xi[i][j]))
#                             m.addConstr(tau[i][j] <= 1 - ((1 / M) * xi[i][j]))    


#             for i in range(num_TR):
#                 if i in C1.keys():
#                     for j in range(num_TR):
#                         if (i != j) & (j in C1.keys()):
#                             m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS <= x[j] + (W * (2 - l[i][j] - s[i][j] + tau[i][j])))
#                             m.addConstr(x[i] + pl[i] + TS <= x[j] + (W * (3 - tau[i][j] - l[i][j] - s[i][j])))
            
            # C31
            for i in range(num_TR):
                m.addConstr(f1[i] >= (0.5 * W) - (0.5 * ((2 * x[i]) + (2 * pl[i]) + d[i])), "c31-" + str(i))
                
            # C32
            for i in range(num_TR):
                m.addConstr(f1[i] >= 0.5 * ((2 * x[i]) + (2 * pl[i]) + d[i]) - (0.5 * W), "c32-" + str(i))
            
            # C33
            for i in range(num_TR):
                if i in C1.keys():
                    for j in range(num_TR):
                        if (i != j) & (j in C1.keys()):
                            m.addConstr(x[i]+ pl[i] + TS[i][j] <= x[j] + (W * (3 + tau[i][j] + ES[i] + ES[j] - s[i][j] - l[i][j])), "c33-" + str(i) + str(j))
            
            # C34
            for i in range(num_TR):
                if i in C1.keys():
                    for j in range(num_TR):
                        if (i != j) & (j in C1.keys()):
                            m.addConstr(l[i][j] >= ES[j] + s[i][j] - tau[i][j] - ES[i] - 1, "c34-" + str(i) + str(j))
            
            # C35
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(td[i] >= g[k] - 1 + a[i][k], "c35-1-" + str(i) + str(k))
                    m.addConstr(td[i] <= g[k] + 1 - a[i][k], "c35-2-" + str(i) + str(k))
                    
            # C36
            for i in range(num_TR):
                if TK[i] == 0: 
                    for k in range(num_row):
                        m.addConstr(a[i][k] <= 1 - t[k], "c36-" + str(i) + str(k))
                        
            # C37
            for i in range(num_TR):
                if TK[i] == 1:
                    for k in range(num_row):
                        m.addConstr(a[i][k] <= t[k], "c37-" + str(i) + str(k))
                        
            # C38
            for k in range(num_row-1):
                m.addConstr(t[k+1] <= t[k], "c38-" + str(k))
                
            # C39
            m.addConstr(t[0] == 1, "c39")
            
            # C40
            m.addConstr(t[num_row-1] == 0, "c40")
            
            # C41
            m.addConstr(g[0] == 1, "c41")
            
            # C42
            m.addConstr(g[num_row-1] == 0, "c42")
             
            # C43
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(mx[k] >= tw[i] - (M * (1 - a[i][k])), "c43-" + str(i) + str(k))
            
            # C44
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(ru[k] >= y[i] + tw[i] - (H * (1 - a[i][k])), "c44-" + str(i) + str(k))
                    
            # C45
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(rl[k] <= y[i] + (H * (1 - a[i][k])), "c45-" + str(i) + str(k))
                    
            # C46
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(y[i] >= rl[k] - (H * (2 - a[i][k] - g[k])), "c46-" + str(i) + str(k))
            
            # C47
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(y[i] <= rl[k] + (H * (2 - a[i][k] - g[k])), "c47-" + str(i) + str(k))
            
            # C48
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(y[i] + tw[i] >= ru[k] - (H * (1 + g[k] - a[i][k])), "c48-" + str(i) + str(k))
                    
            # C49
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(y[i] + tw[i] <= ru[k] + (H * (1 + g[k] - a[i][k])), "c49-" + str(i) + str(k))
                    
            # C50
            for i in range(num_TR):
                if i in TG:
                    for k in range(num_row):
                        m.addConstr(qu[k] >= RS3 - (H * (1 + g[k] - a[i][k])), "c50-" + str(i) + str(k))
                        
            # C51
            for i in range(num_TR):
                if i in TG:
                    for k in range(num_row):
                        m.addConstr(ql[k] >= RS3 - (H * (2 - g[k] - a[i][k])), "c51-" + str(i) + str(k))

            # C52
            for k in range(1, num_row):
                m.addConstr(ru[k] + RS1 + qu[k] + ql[k-1] <= rl[k-1] + (H * (2 + t[k] - t[k-1] - r[k])), "c52-" + str(k))
                
            # C53
            for k in range(1, num_row):
                m.addConstr(ru[k] + RS2 + qu[k] + ql[k-1] <= rl[k-1] + (H * (1 - r[k])), "c53-" + str(k))            
                                     
            # C54
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(ru_prime[k] >= rl[k] + mx[k] - (M * (2 - a[i][k] - g[k])), "c54-" + str(i) + str(k))
                    
            # C55
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(ru_prime[k] <= rl[k] + mx[k] + (M * (2 - a[i][k] - g[k])), "c55-" + str(i) + str(k))
            
            # C56
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(rl_prime[k] >= rl[k] - (M * (2 - a[i][k] - g[k])), "c56-" + str(i) + str(k))
            
            # C57
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(rl_prime[k] <= rl[k] + (M * (2 - a[i][k] - g[k])), "c57-" + str(i) + str(k))
            
            # C58
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(ru_prime[k] >= ru[k] - (M * (1 + g[k] - a[i][k])), "c58-" + str(i) + str(k))
            
            # C59
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(ru_prime[k] <= ru[k] + (M * (1 + g[k] - a[i][k])), "c59-" + str(i) + str(k))
            
            # C60
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(rl_prime[k] >= ru[k] - mx[k] - (M * (1 + g[k] - a[i][k])), "c60-" + str(i) + str(k))
            
            # C61
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(rl_prime[k] <= ru[k] - mx[k] + (M * (1 + g[k] - a[i][k])), "c61-" + str(i) + str(k))
                    
            # C62
            for k in range(1, num_row):
                m.addConstr(ru_prime[k] + RS1 + qu[k] + ql[k-1] <= rl_prime[k-1] + (H * (2 + t[k] - t[k-1] - r[k])), "c62-" + str(k))
                
            # C63
            for k in range(1, num_row):
                m.addConstr(ru_prime[k] + RS2 + qu[k] + ql[k-1] <= rl_prime[k-1] + (H * (1 - r[k])), "c63-" + str(k))
            
            # C64
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(a[i][k] <= r[k], "c64-" + str(i) + str(k))
                    
            # C65
            for k in range(num_row - 1):
                m.addConstr(r[k+1] <= r[k], "c65-" + str(k))
                
            # C66
            for k in range(num_row):
                m.addConstr(rl[k] <= ru[k], "c66-" + str(k))
             
            # C67
            m.addConstr(ru[0] <= H, "c67")

            # C68
            for k in range(num_row):
                m.addConstr(sum(a[i][k] for i in range(num_TR)) >= r[k], "c68-" + str(k))
                     
            # C69
            for i in range(num_TR):
                if i in SG:
                    m.addConstr(_y2[i] >= y[i] - (H * (1 - td[i])), "c69-" + str(i))
                    
            # C70
            for i in range(num_TR):
                if i in SG:
                    m.addConstr(_y2[i] <= y[i] + (H * (1 - td[i])), "c70-" + str(i))
                    
            # C71
            for i in range(num_TR):
                if i in SG:
                    m.addConstr(_y2[i] >= y[i] + tw[i] - (H * td[i]), "c71-" + str(i))
                    
            # C72
            for i in range(num_TR):
                if i in SG:
                    m.addConstr(_y2[i] <= y[i] + tw[i] + (H * td[i]), "c72-" + str(i))
                    
            # C73
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_SG):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e1[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (_y2[i] - _y2[j])) - (M * (2 + s[i][j] - u[i][p] - u[j][q])), "c73-" + str(i) + str(j))

            # C74
            for i in range(num_TR):
                for j in range(num_TR):
                     if (i != j) & ((i, j) in SG_SG):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e1[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (_y2[j] - _y2[i])) - (M * (2 + s[i][j] - u[i][p] - u[j][q])), "c74-" + str(i) + str(j))

            # C75
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_SG):
                        m.addConstr(e1[i][j] >= wx[i][j] - (M * (1 - s[i][j])), "c75-" + str(i) + str(j))

            # C76
            for i in range(num_TR):
                m.addConstr(tr[i] == sum(k * a[i][k] for k in range(num_row)), "c76-" + str(i))
                
            # C77
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        m.addConstr(tr[i] - tr[j] <= num_row * b[i][j], "c77-" + str(i) + str(j))
                        
            # C78
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        m.addConstr(b[i][j] + v[i][j] + s[i][j] == 1, "c78-" + str(i) + str(j))
                        
            # C79
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e2[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (y[i] - y[j] - tw[j])) - (M * (4 - v[i][j] - u[i][p] - u[j][q] - td[i])), "c79-" + str(i) + str(j))

            # C80
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e2[i][j] >= wx[i][j] + (N[i][p] * TW[i][p]) + (alpha2[i][p][j][q] * (y[i] - y[j] - tw[j])) - (M * (3 - v[i][j] - u[i][p] - u[j][q] + td[i])), "c80-" + str(i) + str(j))

            # C81
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e2[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (y[j] - y[i] - tw[i])) - (M * (3 - b[i][j] - u[i][p] - u[j][q] + td[i])), "c81-" + str(i) + str(j))

            # C82
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e2[i][j] >= wx[i][j] + (N[i][p] * TW[i][p]) + (alpha2[i][p][j][q] * (y[j] - y[i] - tw[i])) - (M * (4 - b[i][j] - u[i][p] - u[j][q] - td[i])), "c82-" + str(i) + str(j))

            # C83
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        m.addConstr(e2[i][j] >= wx[i][j] - (M * (1 - s[i][j])), "c83-" + str(i) + str(j))
                        
            # C84
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in O_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e3[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (y[i] - y[j] - tw[j])) - (M * (2 + s[i][j] - u[i][p] - u[j][q])), "c84-" + str(i) + str(j))

            # C85
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in O_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e3[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (y[j] - y[i] - tw[i])) - (M * (2 + s[i][j] - u[i][p] - u[j][q])), "c85-" + str(i) + str(j))

            # C86
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in O_O):
                        m.addConstr(e3[i][j] >= wx[i][j] - (M * (1 - s[i][j])), "c86-" + str(i) + str(j))

            # C87
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(wd[i] >= mx[k] - tw[i] - (H * (1 - a[i][k])), "c87-" + str(i) + str(k))
                        
            # C88, C89
            if row_restriction:
                for i in range(num_TR):
                    for j in range(num_TR):
                        if (i != j) & (((i, j) in O_O) | ((i, j) in SG_O) | ((i, j) in SG_SG)):
                            m.addConstr(tr[i] - tr[j] <= 1, "c88-" + str(i) + str(j))
                            m.addConstr(tr[j] - tr[i] <= 1, "c89-" + str(i) + str(j))
            
            # C90
            for k in range(num_row):
                m.addConstr(my <= rl[k] + (H * (1 - r[k])), "c90-" + str(k))
                
            # C91
            for i in list_II:
                m.addConstr(sum(s[i][j] + (1 - tau[i][j]) for j in range(num_TR) if (j in C1.keys()) and ((i, j) in II)) >= 1, "c91-" + str(i))
            
#             for i in [0, 1, 2, 3]:
#                 m.addConstr(sum(phi[i][j] for j in range(num_TR) if (j in C1.keys()) and ((i, j) in II)) >= 1)
                
#             for i in range(num_TR):
#                 if i in C1.keys():
#                     for j in range(num_TR):
#                         if (j in C1.keys()) & ((i, j) in II):
#                             m.addConstr(phi[i][j] <= 1 - s[i][j])
#                             m.addConstr(phi[i][j] <= 1 - tau[i][j])
#                             m.addConstr(phi[i][j] >= 1 - s[i][j] - tau[i][j])
   
    
#             for i in range(num_TR):
#                 if i in C1.keys():
#                     for j in range(num_TR):
#                         if (i != j) & (j in C1.keys()) & ((i, j) in II):
#                             m.addConstr(phi[i] >= 1 - s[i][j])


#             for i in range(num_TR):
#                 if i in C1.keys():
#                     m.addConstr(sum(1 - tau[i][j] for j in range(num_TR) if (i != j) and (j in C1.keys()) and ((i, j) in II)) >= phi[i])


#             for i in C1.keys():
#                 for j in C1.keys():
#                     if (i != j) & ((i, j) in II):
#                         m.addConstr(phi[i] >= 1 - s[i][j])
                            
#             for i in list_II:
#                 m.addConstr(sum(psi[i][j] for j in C1.keys() if (i != j) and (((i, j) in II) or ((j, i) in II))) >= phi[i])
            
#             for i in list_II:
#                 for j in C1.keys():
#                     if (i != j) & (((i, j) in II) | ((j, i) in II)):
#                         m.addConstr(psi[i][j] <= 1 - s[i][j])
#                         m.addConstr(psi[i][j] <= 1 - tau[i][j])
#                         m.addConstr(psi[i][j] >= 1 - s[i][j] - tau[i][j])
                        
            
            
            # m.addConstr(tau[0][7] == 0) # OP-IJ
            # m.addConstr(tau[1][3] == 0) # MN-EF
            # m.addConstr(tau[1][6] == 0) # MN-GH
            # m.addConstr(tau[3][6] == 0) # EF-GH
            # m.addConstr(tau[2][5] == 0) # CD-KI
            
        
            """Optimize model"""
            m.optimize()
                
                
            '''Ouput'''
            if m.status == GRB.OPTIMAL:
                print("\n# 최적해를 찾았습니다!")
                result = process_solution(m, C, TW, PL, O)
            
            elif m.status == GRB.TIME_LIMIT:
                print("\n# 시간제한에 도달했습니다. 현재 실행 가능한 해를 사용하겠습니다.")
                result = process_solution(m, C, TW, PL, O)
                
            elif m.status in (GRB.INFEASIBLE, GRB.UNBOUNDED):
                print("모델이 실행 불가능합니다. IIS를 계산하여 문제가 있는 제약식을 찾습니다.")
                m.computeIIS()
                for c in m.getConstrs():
                    if c.IISConstr:
                        print(f"{c.ConstrName} 제약식이 문제가 있습니다.")
                result = None
            
            else:
                print(f"Gurobi 상태 코드 {m.status}: 모델의 최적해를 찾지 못했습니다.")
                result = process_solution(m, C, TW, PL, O)
        
    return result

if __name__ == "__main__":
    mipGap = 0.1
    timelimit = 30
    file_path = "D:/[SK Hynix] Placement and Routing/NETLIST/NETLIST_230418_수정.txt"
    save_path = "."
    sets, parameters = input_data(file_path, W=70, H=10, lambda1=0, lambda2=0, lambda3=0, lambda4=0, MS=0.1, RS1=2.0, RS2=0.4, RS3=0.2, K=2)
    row_restriction = True
    TW, PL, o_pattern, x_coord, y_coord, split_distances, gate_direction = solve_placement_opt(timelimit, mipGap, sets, parameters, row_restriction)   
    placement_visualization(save_path, sets["C"], sets["C1"], sets["C2"], parameters["W"], parameters["H"], TW, PL, x_coord, y_coord, split_distances, o_pattern, gate_direction)