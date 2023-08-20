import sys
sys.path.append("D:/[SK Hynix] Placement and Routing/NETLIST 전처리_선진")
sys.path.append("D:/[SK Hynix] Placement and Routing/TR 배치 시각화")

from Netlist_20230817_function import *
from Init_Visualization import *

import gurobipy as gp
from gurobipy import GRB
import numpy as np

def process_solution(m, first_netlist, C, TW, PL, O):
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
                
        if var.varName[0] == "g":
            gate_direction.append((var.varName, var.x))
            
        if var.varName[:2] == "tr":
            print((var.varName, var.x))

    selected_TW = []
    selected_PL = []
    selected_O = []

    for idx, pattern in enumerate(selected_pattern):
        tr = idx
        p = int(pattern[0][-1])
        selected_TW.append(TW[tr][p])
        selected_PL.append(PL[tr][p])
        selected_O.append(O[tr][p])
    
    if first_netlist:
        TR_names = {0:'CD', 1:'AB', 2:'EF', 3:'IJ', 4:'GH', 5:'Z3', 6:'Z4', 7:'Z2', 8:'Z1'}
    else:
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

def solve_placement_opt(timelimit, mipGap, first_netlist, sets, parameters, row_restriction):
    
    """Sets"""
    C = sets["C"]     
    C1 = sets["C1"]   
    C2 = sets["C2"]   
    B = sets["B_i"]   
    P = sets["P"]     
    SG = sets["SG"]   
    WG = sets["WG"]   
    GG = sets["G_G"]  
    GI = sets["G_I"]  
    II = sets["I_I"]  
    SG_SG = sets["SG_SG"] 
    SG_O = sets["SG_O"] 
    O_O = sets["O_O"]  
    TG = sets["TG"]   
    AI = sets["AI"]
    
    
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
            phi = [m.addVar(vtype=GRB.BINARY, name="phi" + str(i)) for i in range(num_TR)]
            psi = [[m.addVar(vtype=GRB.BINARY, name="psi" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            zeta = [m.addVar(vtype=GRB.BINARY, name="zeta" + str(i)) for i in range(num_TR)]
            _xi = [[m.addVar(vtype=GRB.BINARY, name="_xi" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            
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

            '''
            zeta = [m.addVar(vtype=GRB.BINARY, name="zeta" + str(i)) for i in range(num_TR)]
            xi = [[m.addVar(vtype=GRB.CONTINUOUS, name="xi" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            rho = [[m.addVar(vtype=GRB.BINARY, name="rho" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            phi = [[m.addVar(vtype=GRB.BINARY, name="phi" + str(i) + str(j)) for j in range(num_TR)] for i in range(num_TR)]
            '''
            
            
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
            for i in C1.keys():
                for j in B[i]:
                    m.addConstr(s[i][j] == 1, "c09-" + str(i) + str(j))
            
            # C10
            for i in C1.keys():
                for j in B[i]:
                    m.addConstr(l[j][i] == 1, "c10-" + str(i) + str(j))
        
            # C11
            for i in C1.keys():
                for j in B[i]:
                    m.addConstr(l[i][j] == 0, "c11-" + str(i) + str(j))
       
                
            # C12
            for i in C.keys():
                m.addConstr(xc[i] == x[i] + pl[i] + (0.5 * d[i]), "c12-" + str(i))
                    
            # C13
            for i in C1.keys():
                for j in B[i]:
                    m.addConstr(xc[i] == x[j] + pl[j] + (0.5 * d[j]), "c13-" + str(i) + str(j))
                            
            # C14
            for i in C.keys():
                m.addConstr(x[i] + (2 * pl[i]) + d[i] <= W, "c14-" + str(i))
                    
            # C15
            for i in range(num_TR):
                m.addConstr(y[i] + tw[i] <= H, "c15-" + str(i))
                
            # C16
            for i in C1.keys():
                m.addConstr(d[i] >= MS, "c16-" + str(i))
                    
            # C17
            for i in C2.keys():
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
                        
            '''
            for i in range(num_TR):
                if (i in C1.keys()):
                    for j in range(num_TR):
                        if (i != j) & (j in C1.keys()):
                            m.addConstr(xc[i] <= xc[j] + (M * rho[i][j]))
                            m.addConstr(xc[i] >= xc[j] - (M * (1 - rho[i][j])))
                            m.addConstr(xi[i][j] >= xc[i] - xc[j])
                            m.addConstr(xi[i][j] <= xc[i] - xc[j] + (M * (1 - rho[i][j])))
                            m.addConstr(xi[i][j] >= xc[j] - xc[i])
                            m.addConstr(xi[i][j] <= xc[j] - xc[i] + (M * rho[i][j]))
                            m.addConstr(tau[i][j] >= 1 - (M * xi[i][j]))
                            m.addConstr(tau[i][j] <= 1 - ((1 / M) * xi[i][j]))    
            '''
                        
            #C22  
            for i in C.keys():
                for j in C.keys():
                    if i != j:
                        m.addConstr(xc[i] <= xc[j] + (W * tau[i][j]), "c22-1-" + str(i) + str(j))
                        m.addConstr(xc[i] >= xc[j] - (W * tau[i][j]), "c22-2-" + str(i) + str(j)) 
                            
            # C23
            for i in C.keys():
                for j in C.keys():
                    if i != j:
                        m.addConstr(tau[i][j] == tau[j][i], "c23-" + str(i) + str(j))
                        
            # C24
            for i in C1.keys():
                for j in C1.keys():
                    if (i != j) & ((i, j) in II):
                        m.addConstr(xc[i] <= xc[j] + (W * (s[i][j] + tau[i][j])), "c24-1-" + str(i) + str(j))
                        m.addConstr(xc[i] >= xc[j] - (W * (s[i][j] + tau[i][j])), "c24-2-" + str(i) + str(j))
                                    
            '''
            for i in C1.keys():
                for j in C1.keys():
                    if (i != j) & (((i, j) in II) | ((j, i) in II)):
                        m.addConstr(phi[i] >= 1 - s[i][j], "c25-" + str(i) + str(j))
                            
            for i in C1.keys():
                m.addConstr(sum(1 - psi[i][j] for j in C1.keys() if (i != j) and (((i, j) in II) or ((j, i) in II))) >= phi[i], "c26-" + str(i))
            
            for i in C1.keys():
                for j in C1.keys():
                    if (i != j) & (((i, j) in II) | ((j, i) in II)):
                        m.addConstr(psi[i][j] >= s[i][j], "c27-" + str(i) + str(j))
                        m.addConstr(psi[i][j] >= tau[i][j], "c28-" + str(i) + str(j))
                        m.addConstr(psi[i][j] <= s[i][j] + tau[i][j], "c29-" + str(i) + str(j))
              
              
            for i in C1.keys():
                for j in C1.keys():
                    if (i != j) & ((i, j) in AI):
                        m.addConstr(zeta[i] >= 1 - s[i][j], "c30-" + str(i) + str(j))
                        
            for i in C1.keys():
                for j in C1.keys():
                    if (i != j) and ((i, j) in AI):  
                        m.addConstr(1 - _xi[i][j] >= zeta[i], "c31-" + str(i) + str(j))
            
            for i in C1.keys():
                for j in C1.keys():
                    if (i != j) & ((i, j) in AI):
                        m.addConstr(_xi[i][j] >= s[i][j], "c32-" + str(i) + str(j))
                        m.addConstr(_xi[i][j] >= tau[i][j], "c33-" + str(i) + str(j))
                        m.addConstr(_xi[i][j] <= s[i][j] + tau[i][j], "c34-" + str(i) + str(j))
            '''
            
            # C25
            for i in C1.keys():
                for j in C1.keys():
                    if (i != j) & (((i, j) in II) | ((j ,i ) in II)):
                        m.addConstr(phi[i] >= 1 - s[i][j], "c25-" + str(i) + str(j))
            
            # C26            
            for i in C1.keys():
                m.addConstr(sum(psi[i][j] for j in C1.keys() if (i != j) and (((i, j) in II) or ((j, i) in II))) >= phi[i], "c26-" + str(i))
            
            # C27~29
            for i in C1.keys():
                for j in C1.keys():
                    if (i != j) & (((i, j) in II) | ((j, i) in II)):
                        m.addConstr(psi[i][j] <= 1 - s[i][j], "c27-" + str(i) + str(j))
                        m.addConstr(psi[i][j] <= 1 - tau[i][j], "c28-" + str(i) + str(j))
                        m.addConstr(psi[i][j] >= 1 - s[i][j] - tau[i][j], "c29-" + str(i) + str(j))
           
            # C30
            for i in C1.keys():
                for j in C1.keys():
                    if (i != j) & (((i, j) in AI) | ((j, i) in AI)):
                        m.addConstr(zeta[i] >= 1 - s[i][j], "c30-" + str(i) + str(j))

            # C31           
            for i in C1.keys():
                for j in C1.keys():
                    if (i != j) and (((i, j) in AI) | ((j, i) in AI)):  
                        m.addConstr(_xi[i][j] >= zeta[i], "c31-" + str(i) + str(j))
            
            # C32~24
            for i in C1.keys():
                for j in C1.keys():
                    if (i != j) & (((i, j) in AI) | ((j, i) in AI)):
                        m.addConstr(_xi[i][j] <= 1 - s[i][j], "c32-" + str(i) + str(j))
                        m.addConstr(_xi[i][j] <= 1 - tau[i][j], "c33-" + str(i) + str(j))
                        m.addConstr(_xi[i][j] >= 1 - s[i][j] - tau[i][j], "c34-" + str(i) + str(j))

            # C35
            for i in range(num_TR):
                for j in C2.keys():
                    if i != j:
                        m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 - l[i][j] - s[i][j] - o[j])), "c35-" + str(i) + str(j))  
                       
            # C36
            for i in C2.keys():
                for j in range(num_TR):
                    if i != j:
                        m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 - l[i][j] - s[i][j] - o[i])), "c36-" + str(i) + str(j))
              
            # C37  
            for i in C1.keys():
                for j in C2.keys():
                    if i != j:
                        m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (4 + o[j] - l[i][j] - s[i][j] - o[i] - tau[i][j])), "c37-" + str(i) + str(j))
            
            # C38
            for i in C2.keys():
                for j in C.keys():
                    if i != j:
                        m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (4 + o[i] - l[i][j] - s[i][j] - o[j] - tau[i][j])), "c38-" + str(i) + str(j))
            
            # C39
            for i in C1.keys():
                for j in C2.keys():
                    if i != j:
                        m.addConstr(x[i] + pl[i] + TS[i][j] <= x[j] + (W * (2 + o[i] + o[j] + tau[i][j] - l[i][j] - s[i][j])), "c39-" + str(i) + str(j))
            
            # C40
            for i in C2.keys():
                for j in C.keys():
                    if i != j:
                        m.addConstr(x[i] + pl[i] + TS[i][j] <= x[j] + (W * (2 + o[i] + o[j] + tau[i][j] - l[i][j] - s[i][j])), "c40-" + str(i) + str(j))
            
            # C41
            for i in C.keys():
                for j in C2.keys():
                    if i != j:
                        m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 + o[i] + o[j] - tau[i][j] - l[i][j] - s[i][j])), "c41-" + str(i) + str(j))
            
            # C42
            for i in C2.keys():
                for j in C.keys():
                    if i != j:
                        m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 + o[i] + o[j] - tau[i][j] - l[i][j] - s[i][j])), "c42-" + str(i) + str(j)) 
                            
            # C43
            for i in C1.keys():
                for j in C1.keys():
                    if i != j:
                        m.addConstr(x[i] + (2 * pl[i]) + d[i] + TS[i][j] <= x[j] + (W * (3 - tau[i][j] - l[i][j] - s[i][j])), "c43-" + str(i) + str(j))
                            
            # C44
            for i in C1.keys():
                for j in C1.keys():
                    if i != j:
                        m.addConstr(x[i] + pl[i] + TS[i][j] <= x[j] + (W * (2 + tau[i][j] - l[i][j] - s[i][j])), "c44-" + str(i) + str(j))
            
            # C45
            for i in range(num_TR):
                m.addConstr(f1[i] >= (0.5 * W) - (0.5 * ((2 * x[i]) + (2 * pl[i]) + d[i])), "c45-" + str(i))
                
            # C46
            for i in range(num_TR):
                m.addConstr(f1[i] >= 0.5 * ((2 * x[i]) + (2 * pl[i]) + d[i]) - (0.5 * W), "c46-" + str(i))
            
            # C47
            for i in C1.keys():
                for j in C1.keys():
                    if i != j:
                        m.addConstr(x[i]+ pl[i] + TS[i][j] <= x[j] + (W * (3 + tau[i][j] + ES[i] + ES[j] - s[i][j] - l[i][j])), "c47-" + str(i) + str(j))            
            
            # C48
            for i in C1.keys():
                for j in C1.keys():
                    if i != j:
                        m.addConstr(l[i][j] >= ES[j] + s[i][j] - tau[i][j] - ES[i] - 1, "c48-" + str(i) + str(j))
                            
            # C49
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(td[i] >= g[k] - 1 + a[i][k], "c49-1-" + str(i) + str(k))
                    m.addConstr(td[i] <= g[k] + 1 - a[i][k], "c49-2-" + str(i) + str(k))
                    
            # C50
            for i in [idx for idx, val in enumerate(TK) if val == 0]:
                for k in range(num_row):
                    m.addConstr(a[i][k] <= 1 - t[k], "c50-" + str(i) + str(k))
                        
            # C51
            for i in [idx for idx, val in enumerate(TK) if val == 1]:
                for k in range(num_row):
                    m.addConstr(a[i][k] <= t[k], "c51-" + str(i) + str(k))
                        
            # C52
            for k in range(num_row-1):
                m.addConstr(t[k+1] <= t[k], "c52-" + str(k))
                
            # C53
            m.addConstr(t[0] == 1, "c53")
            
            # C54
            m.addConstr(t[num_row-1] == 0, "c54")
            
            # C55
            m.addConstr(g[0] == 1, "c55")
            
            # C56
            m.addConstr(g[num_row-1] == 0, "c56")
             
            # C57
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(mx[k] >= tw[i] - (M * (1 - a[i][k])), "c57-" + str(i) + str(k))
            
            # C58
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(ru[k] >= y[i] + tw[i] - (H * (1 - a[i][k])), "c58-" + str(i) + str(k))
                    
            # C59
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(rl[k] <= y[i] + (H * (1 - a[i][k])), "c59-" + str(i) + str(k))
                    
            # C60
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(y[i] >= rl[k] - (H * (2 - a[i][k] - g[k])), "c60-" + str(i) + str(k))
            
            # C61
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(y[i] <= rl[k] + (H * (2 - a[i][k] - g[k])), "c61-" + str(i) + str(k))
            
            # C62
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(y[i] + tw[i] >= ru[k] - (H * (1 + g[k] - a[i][k])), "c62-" + str(i) + str(k))
                    
            # C63
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(y[i] + tw[i] <= ru[k] + (H * (1 + g[k] - a[i][k])), "c63-" + str(i) + str(k))
                    
            # C64
            for i in [idx for idx in range(num_TR) if idx in TG]:
                for k in range(num_row):
                    m.addConstr(qu[k] >= RS3 - (H * (1 + g[k] - a[i][k])), "c64-" + str(i) + str(k))
                        
            # C65
            for i in [idx for idx in range(num_TR) if idx in TG]:
                for k in range(num_row):
                    m.addConstr(ql[k] >= RS3 - (H * (2 - g[k] - a[i][k])), "c65-" + str(i) + str(k))
                    
            # C66
            for k in range(1, num_row):
                m.addConstr(ru[k] + RS1 + qu[k] + ql[k-1] <= rl[k-1] + (H * (2 + t[k] - t[k-1] - r[k])), "c66-" + str(k))
                
            # C67
            for k in range(1, num_row):
                m.addConstr(ru[k] + RS2 + qu[k] + ql[k-1] <= rl[k-1] + (H * (1 - r[k])), "c67-" + str(k))            
                                     
            # C68
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(ru_prime[k] >= rl[k] + mx[k] - (M * (2 - a[i][k] - g[k])), "c68-" + str(i) + str(k))
                    
            # C69
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(ru_prime[k] <= rl[k] + mx[k] + (M * (2 - a[i][k] - g[k])), "c69-" + str(i) + str(k))
            
            # C70
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(rl_prime[k] >= rl[k] - (M * (2 - a[i][k] - g[k])), "c70-" + str(i) + str(k))
            
            # C71
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(rl_prime[k] <= rl[k] + (M * (2 - a[i][k] - g[k])), "c71-" + str(i) + str(k))
            
            # C72
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(ru_prime[k] >= ru[k] - (M * (1 + g[k] - a[i][k])), "c72-" + str(i) + str(k))
            
            # C73
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(ru_prime[k] <= ru[k] + (M * (1 + g[k] - a[i][k])), "c73-" + str(i) + str(k))
            
            # C74
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(rl_prime[k] >= ru[k] - mx[k] - (M * (1 + g[k] - a[i][k])), "c74-" + str(i) + str(k))
            
            # C75
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(rl_prime[k] <= ru[k] - mx[k] + (M * (1 + g[k] - a[i][k])), "c75-" + str(i) + str(k))
                    
            # C76
            for k in range(1, num_row):
                m.addConstr(ru_prime[k] + RS1 + qu[k] + ql[k-1] <= rl_prime[k-1] + (H * (2 + t[k] - t[k-1] - r[k])), "c76-" + str(k))
                
            # C77
            for k in range(1, num_row):
                m.addConstr(ru_prime[k] + RS2 + qu[k] + ql[k-1] <= rl_prime[k-1] + (H * (1 - r[k])), "c77-" + str(k))
            
            # C78
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(a[i][k] <= r[k], "c78-" + str(i) + str(k))
                    
            # C79
            for k in range(num_row - 1):
                m.addConstr(r[k+1] <= r[k], "c79-" + str(k))
                
            # C80
            for k in range(num_row):
                m.addConstr(rl[k] <= ru[k], "c80-" + str(k))
             
            # C81
            m.addConstr(ru[0] <= H, "c81")

            # C82
            for k in range(num_row):
                m.addConstr(sum(a[i][k] for i in range(num_TR)) >= r[k], "c82-" + str(k))
                     
            # C83
            for i in [idx for idx in range(num_TR) if idx in SG]:
                m.addConstr(_y2[i] >= y[i] - (H * (1 - td[i])), "c83-" + str(i))
                    
            # C84
            for i in [idx for idx in range(num_TR) if idx in SG]:
                m.addConstr(_y2[i] <= y[i] + (H * (1 - td[i])), "c84-" + str(i))
                    
            # C85
            for i in [idx for idx in range(num_TR) if idx in SG]:
                m.addConstr(_y2[i] >= y[i] + tw[i] - (H * td[i]), "c85-" + str(i))
                    
            # C86
            for i in [idx for idx in range(num_TR) if idx in SG]:
                m.addConstr(_y2[i] <= y[i] + tw[i] + (H * td[i]), "c86-" + str(i))   
                
            # C87
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_SG):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e1[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (_y2[i] - _y2[j])) - (M * (2 + s[i][j] - u[i][p] - u[j][q])), "c87-" + str(i) + str(j))

            # C88
            for i in range(num_TR):
                for j in range(num_TR):
                     if (i != j) & ((i, j) in SG_SG):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e1[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (_y2[j] - _y2[i])) - (M * (2 + s[i][j] - u[i][p] - u[j][q])), "c88-" + str(i) + str(j))

            # C89
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_SG):
                        m.addConstr(e1[i][j] >= wx[i][j] - (M * (1 - s[i][j])), "c89-" + str(i) + str(j))

            # C90
            for i in range(num_TR):
                m.addConstr(tr[i] == sum(k * a[i][k] for k in range(num_row)), "c90-" + str(i))
                
            # C91
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        m.addConstr(tr[i] - tr[j] <= num_row * b[i][j], "c91-" + str(i) + str(j))
                        
            # C92
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        m.addConstr(b[i][j] + v[i][j] + s[i][j] == 1, "c92-" + str(i) + str(j))
                        
            # C93
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e2[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (y[i] - y[j] - tw[j])) - (M * (4 - v[i][j] - u[i][p] - u[j][q] - td[i])), "c93-" + str(i) + str(j))

            # C94
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e2[i][j] >= wx[i][j] + (N[i][p] * TW[i][p]) + (alpha2[i][p][j][q] * (y[i] - y[j] - tw[j])) - (M * (3 - v[i][j] - u[i][p] - u[j][q] + td[i])), "c94-" + str(i) + str(j))

            # C95
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e2[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (y[j] - y[i] - tw[i])) - (M * (3 - b[i][j] - u[i][p] - u[j][q] + td[i])), "c95-" + str(i) + str(j))

            # C96
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e2[i][j] >= wx[i][j] + (N[i][p] * TW[i][p]) + (alpha2[i][p][j][q] * (y[j] - y[i] - tw[i])) - (M * (4 - b[i][j] - u[i][p] - u[j][q] - td[i])), "c96-" + str(i) + str(j))

            # C97
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in SG_O):
                        m.addConstr(e2[i][j] >= wx[i][j] - (M * (1 - s[i][j])), "c97-" + str(i) + str(j))
                        
            # C98
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in O_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e3[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (y[i] - y[j] - tw[j])) - (M * (2 + s[i][j] - u[i][p] - u[j][q])), "c98-" + str(i) + str(j))

            # C99
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in O_O):
                        for p in range(len(P[i])):
                            for q in range(len(P[j])):
                                m.addConstr(e3[i][j] >= wx[i][j] + (alpha2[i][p][j][q] * (y[j] - y[i] - tw[i])) - (M * (2 + s[i][j] - u[i][p] - u[j][q])), "c99-" + str(i) + str(j))

            # C100
            for i in range(num_TR):
                for j in range(num_TR):
                    if (i != j) & ((i, j) in O_O):
                        m.addConstr(e3[i][j] >= wx[i][j] - (M * (1 - s[i][j])), "c100-" + str(i) + str(j))
                        
                        
            # C101
            for i in range(num_TR):
                for k in range(num_row):
                    m.addConstr(wd[i] >= mx[k] - tw[i] - (H * (1 - a[i][k])), "c101-" + str(i) + str(k))
                        
            # C102~103
            if row_restriction:
                for i in range(num_TR):
                    for j in range(num_TR):
                        if (i != j) & (((i, j) in O_O) | ((i, j) in SG_O) | ((i, j) in SG_SG)):
                            m.addConstr(tr[i] - tr[j] <= 1, "c102-" + str(i) + str(j))
                            m.addConstr(tr[j] - tr[i] <= 1, "c103-" + str(i) + str(j))
            
            # C104
            for k in range(num_row):
                m.addConstr(my <= rl[k] + (H * (1 - r[k])), "c104-" + str(k))
            
            
            '''3 row revision'''
            # m.addConstr(a[4][0] == 1)
            # m.addConstr(a[2][1] == 1)
            
            '''4 row revision'''
            # m.addConstr(a[8][1] == 1)
            # m.addConstr(a[9][1] == 1)
            # m.addConstr(a[10][1] == 1)
            # m.addConstr(a[11][1] == 1)
            # m.addConstr(a[12][3] == 1)
            # m.addConstr(a[13][3] == 1)
            # m.addConstr(a[14][3] == 1)
            # m.addConstr(a[15][3] == 1)
            # m.addConstr(a[16][3] == 1)
            # m.addConstr(a[17][3] == 1)
            # m.addConstr(a[18][3] == 1)
            # m.addConstr(a[19][3] == 1)
            

            """Optimize model"""
            m.optimize()
                
                
            '''Ouput'''
            if m.status == GRB.OPTIMAL:
                print("\n# 최적해를 찾았습니다!")
                result = process_solution(m, first_netlist, C, TW, PL, O)
            
            elif m.status == GRB.TIME_LIMIT:
                print("\n# 시간제한에 도달했습니다. 현재 실행 가능한 해를 사용하겠습니다.")
                result = process_solution(m, first_netlist, C, TW, PL, O)
                
            elif m.status in (GRB.INFEASIBLE, GRB.UNBOUNDED):
                print("모델이 실행 불가능합니다. IIS를 계산하여 문제가 있는 제약식을 찾습니다.")
                m.computeIIS()
                for c in m.getConstrs():
                    if c.IISConstr:
                        print(f"{c.ConstrName} 제약식이 문제가 있습니다.")
                result = None
            
            else:
                print(f"Gurobi 상태 코드 {m.status}: 모델의 최적해를 찾지 못했습니다.")
                result = process_solution(m, first_netlist, C, TW, PL, O)
        
    return result

if __name__ == "__main__":
    mipGap = 0.1
    timelimit = 30
    # file_path = "D:/[SK Hynix] Placement and Routing/NETLIST/NETLIST.txt"
    file_path = "D:/[SK Hynix] Placement and Routing/NETLIST/NETLIST_230418_수정.txt"
    save_path = "."
    sets, parameters = input_data(file_path, first_netlist, W=70, H=10, lambda1=0, lambda2=10, lambda3=0, lambda4=0, MS=0.1, RS1=2.0, RS2=0.4, RS3=0.2, K=4)
    first_netlist = False
    row_restriction = True
    TW, PL, o_pattern, x_coord, y_coord, split_distances, gate_direction = solve_placement_opt(timelimit, mipGap, first_netlist, sets, parameters, row_restriction)   
    placement_visualization(save_path, first_netlist, sets["C"], sets["C1"], sets["C2"], parameters["W"], parameters["H"], TW, PL, x_coord, y_coord, split_distances, o_pattern, gate_direction)