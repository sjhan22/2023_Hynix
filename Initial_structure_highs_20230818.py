import sys
sys.path.append("./Netlist_20230819_function.py")
sys.path.append("./Init_Visualization.py")
from Netlist_20230819_function import *
from Init_Visualization import *
from pyomo.environ import *
from pyomo.environ import SolverFactory
import pyomo.contrib.appsi.build
from pyomo.contrib.appsi.build import build_appsi
from pyomo.contrib import appsi

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
        TR_names = {0: 'CD', 1: 'AB', 2: 'EF', 3: 'IJ', 4: 'GH', 5: 'Z3', 6: 'Z4', 7: 'Z2', 8: 'Z1'}
    else:
        TR_names = {0: "OP", 1: "MN", 2: "CD", 3: "EF", 4: "AB", 5: "KI", 6: "GH", 7: "IJ", 8: "Z5", 9: "Z2", 10: "Z3",
                    11: "Z4", 12: "Z8", 13: "Z12", 14: "Z13", 15: "Z11", 16: "Z9", 17: "Z10", 18: "Z7", 19: "Z6"}

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

def solve_placement_opt(sets, parameters, row_restriction):
    
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

    # model
    m = ConcreteModel()

    # decision variables
    m.u = Var([(i, p) for i in range(num_TR) for p in range(len(P[i]))], domain = Binary)
    m.a = Var([(i, k) for i in range(num_TR) for k in range(num_row)], domain = Binary)
    m.z = Var([(i, j, k) for i in range(num_TR) for j in range(num_TR) for k in range(num_row)], domain = Binary)
    m.s = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = Binary)
    m.l = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = Binary)
    m.b = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = Binary)
    m.v = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = Binary)
    m.o = Var([i for i in range(num_TR)], domain = Binary)
    m.g = Var([k for k in range(num_row)], domain = Binary)
    m.t = Var([k for k in range(num_row)], domain = Binary)
    m.r = Var([k for k in range(num_row)] , domain = Binary)
    m.td = Var([i for i in range(num_TR)], domain = Binary)
    m.tau = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = Binary)
    m.phi = Var([i for i in range(num_TR)], domain = Binary)
    m.psi = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = Binary)
    m.zeta = Var([i for i in range(num_TR)], domain = Binary)
    m._xi = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = Binary)

    m.x = Var([i for i in range(num_TR)], domain = NonNegativeReals)
    m.y = Var([i for i in range(num_TR)], domain = NonNegativeReals)
    m.tw = Var([i for i in range(num_TR)], domain = NonNegativeReals)
    m.pl = Var([i for i in range(num_TR)], domain = NonNegativeReals)
    m.qu = Var([k for k in range(num_row)], domain = NonNegativeReals)
    m.ql = Var([k for k in range(num_row)], domain = NonNegativeReals)
    m.tr = Var([i for i in range(num_TR)], domain = NonNegativeReals)
    m.d = Var([i for i in range(num_TR)], domain = NonNegativeReals)
    m.ru = Var([k for k in range(num_row)], domain = NonNegativeReals)
    m.rl = Var([k for k in range(num_row)], domain = NonNegativeReals)
    m.ru_prime = Var([k for k in range(num_row)], domain = NonNegativeReals)
    m.rl_prime = Var([k for k in range(num_row)], domain = NonNegativeReals)
    m.e1 = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = NonNegativeReals)
    m.e2 = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = NonNegativeReals)
    m.e3 = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = NonNegativeReals)
    m.px = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = NonNegativeReals)
    m.wx = Var([(i, j) for i in range(num_TR) for j in range(num_TR)], domain = NonNegativeReals)
    m.mx = Var([k for k in range(num_row)], domain = NonNegativeReals)
    m.my = Var(domain = NonNegativeReals, initialize = 0.0)
    m.f1 = Var([i for i in range(num_TR)], domain = NonNegativeReals, initialize = 0.0)
    m._y2 = Var([i for i in range(num_TR)], domain = NonNegativeReals)
    m.xc = Var([i for i in range(num_TR)], domain = NonNegativeReals)
    m.wd = Var([i for i in range(num_TR)], domain = NonNegativeReals, initialize = 0.0)

    # objective
    m.obj = Objective(expr = sum(m.e1[i, j] for i in range(num_TR) for j in range(num_TR) if (i, j) in SG_SG) +
                             sum(m.e2[i, j] for i in range(num_TR) for j in range(num_TR) if (i, j) in SG_O) +
                             sum(m.e3[i, j] for i in range(num_TR) for j in range(num_TR) if (i, j) in O_O) +
                             (lambda1 * sum(m.f1[i] for i in range(num_TR))) + (lambda2 * sum(m.wd[i] for i in range(num_TR))) - (lambda3 * m.my) +
                             (lambda4 * sum(m.tau[i, j] for i in range(num_TR) for j in range(num_TR) if (i != j))), sense = minimize)

    # constraints
    def constraint_1_rule(model, i):
        return sum([model.u[i, p] for p in range(len(P[i]))]) == 1
    m.c1 = Constraint([i for i in range(num_TR)], rule = constraint_1_rule)

    def constraint_2_rule(model, i):
        return model.o[i] == sum([O[i][p] * model.u[i, p] for p in range(len(P[i]))])
    m.c2 = Constraint([i for i in range(num_TR)], rule = constraint_2_rule)

    def constraint_3_rule(model, i):
        return model.tw[i] == sum([TW[i][p] * model.u[i, p] for p in range(len(P[i]))])
    m.c3 = Constraint([i for i in range(num_TR)], rule = constraint_3_rule)

    def constraint_4_rule(model, i):
        return model.pl[i] == sum([PL[i][p] * model.u[i, p] for p in range(len(P[i]))])
    m.c4 = Constraint([i for i in range(num_TR)], rule = constraint_4_rule)

    def constraint_5_rule(model, i):
        return sum([model.a[i, k] for k in range(num_row)]) == 1
    m.c5 = Constraint([i for i in range(num_TR)], rule = constraint_5_rule)

    def constraint_6_1_rule(model, i, j, k):
        if i != j:
            return model.z[i, j, k] >= model.a[i, k] + model.a[j, k] - 1
        else:
            return Constraint.Skip
    m.c6_1 = Constraint([(i, j, k) for i in range(num_TR) for j in range(num_TR) for k in range(num_row)], rule = constraint_6_1_rule)

    def constraint_6_2_rule(model, i, j, k):
        if i != j:
            return model.z[i, j, k] <= 0.5 * (model.a[i, k] + model.a[j, k])
        else:
            return Constraint.Skip
    m.c6_2 = Constraint([(i, j, k) for i in range(num_TR) for j in range(num_TR) for k in range(num_row)], rule = constraint_6_2_rule)

    def constraint_7_rule(model, i, j):
        if i != j:
            return model.s[i, j] == sum(model.z[i, j, k] for k in range(num_row))
        else:
            return Constraint.Skip
    m.c7 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_7_rule)

    def constraint_8_1_rule(model, i, j):
        if i != j:
            return model.l[i, j] + model.l[j, i] >= model.s[i, j]
        else:
            return Constraint.Skip
    m.c8_1 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_8_1_rule)

    def constraint_8_2_rule(model, i, j):
        if i != j:
            return model.l[i, j] + model.l[j, i] <= model.s[i, j]
        else:
            return Constraint.Skip
    m.c8_2 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_8_2_rule)

    def constraint_9_rule(model, i, j):
        if i in C1.keys() and j in B[i]:
            return model.s[i, j] == 1
        else:
            return Constraint.Skip
    m.c9 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_9_rule)

    def constraint_10_rule(model, i, j):
        if i in C1.keys() and j in B[i]:
            return model.l[j, i] == 1
        else:
            return Constraint.Skip
    m.c10 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_10_rule)

    def constraint_11_rule(model, i, j):
        if i in C1.keys() and j in B[i]:
            return model.l[i, j] == 0
        else:
            return Constraint.Skip
    m.c11 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_11_rule)

    def constraint_12_rule(model, i):
        if i in C1.keys():
            return model.xc[i] == model.x[i] + model.pl[i] + (0.5 * model.d[i])
        else:
            return Constraint.Skip
    m.c12 = Constraint([i for i in range(num_TR)], rule = constraint_12_rule)

    def constraint_13_rule(model, i, j):
        if i in C1.keys() and j in B[i]:
            return model.xc[i] == model.x[j] + model.pl[j] + (0.5 * model.d[j])
        else:
            return Constraint.Skip
    m.c13 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_13_rule)

    def constraint_14_rule(model, i):
        if i in C.keys():
            return model.x[i] + (2 * model.pl[i]) + model.d[i] <= W
        else:
            return Constraint.Skip
    m.c14 = Constraint([i for i in range(num_TR)], rule = constraint_14_rule)

    def constraint_15_rule(model, i):
        return model.y[i] + model.tw[i] <= H
    m.c15 = Constraint([i for i in range(num_TR)], rule = constraint_15_rule)

    def constraint_16_rule(model, i):
        if i in C1.keys():
            return model.d[i] >= MS
        else:
            return Constraint.Skip
    m.c16 = Constraint([i for i in range(num_TR)], rule = constraint_16_rule)

    def constraint_17_1_rule(model, i):
        if i in C2.keys():
            return W * (1 - model.o[i]) >= model.d[i]
        else:
            return Constraint.Skip
    m.c17_1 = Constraint([i for i in range(num_TR)], rule = constraint_17_1_rule)

    def constraint_17_2_rule(model, i):
        if i in C2.keys():
            return model.d[i] >= MS * (1 - model.o[i])
        else:
            return Constraint.Skip
    m.c17_2 = Constraint([i for i in range(num_TR)], rule = constraint_17_2_rule)

    def constraint_18_rule(model, i, j):
        if i != j:
            return model.px[i, j] >= model.x[i] + 2 * model.pl[i] + model.d[i]
        else:
            return Constraint.Skip
    m.c18 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_18_rule)

    def constraint_19_rule(model, i, j):
        if i != j:
            return model.px[i, j] >= model.x[j] + (2 * model.pl[j]) + model.d[j]
        else:
            return Constraint.Skip
    m.c19 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_19_rule)

    def constraint_20_rule(model, i, j):
        if i != j:
            return model.wx[i, j] >= model.px[i, j] - model.x[i]
        else:
            return Constraint.Skip
    m.c20 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_20_rule)

    def constraint_21_rule(model, i, j):
        if i != j:
            return model.wx[i, j] >= model.px[i, j] - model.x[j]
        else:
            return Constraint.Skip
    m.c21 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_21_rule)

    def constraint_22_1_rule(model, i, j):
        if i != j:
            return model.xc[i] <= model.xc[j] + (W * model.tau[i, j])
        else:
            return Constraint.Skip

    m.c22_1 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule=constraint_22_1_rule)

    def constraint_22_2_rule(model, i, j):
        if i != j:
            return model.xc[i] >= model.xc[j] - (W * model.tau[i, j])
        else:
            return Constraint.Skip

    m.c22_2 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule=constraint_22_2_rule)

    def constraint_23_rule(model, i, j):
        if i != j:
            return model.tau[i, j] == model.tau[j, i]
        else:
            return Constraint.Skip

    m.c23 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule=constraint_23_rule)

    def constraint_24_1_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys() and (i, j) in II:
            return model.xc[i] <= model.xc[j] + (W * (model.s[i, j] + model.tau[i, j]))
        else:
            return Constraint.Skip

    m.c24_1 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule=constraint_24_1_rule)

    def constraint_24_2_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys() and (i, j) in II:
            return model.xc[i] >= model.xc[j] - (W * (model.s[i, j] + model.tau[i, j]))
        else:
            return Constraint.Skip

    m.c24_2 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule=constraint_24_2_rule)

    def constraint_25_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys() and (((i, j) in II) or ((j ,i) in II)):
            return model.phi[i] >= 1 - model.s[i, j]
        else:
            return Constraint.Skip
    m.c25 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_25_rule)

    def constraint_26_rule(model, i):
        if i in C1.keys():
            return sum(model.psi[i, j] for j in C1.keys() if i != j and (((i, j) in II) or ((j, i) in II))) >= model.phi[i]
        else:
            return Constraint.Skip
    m.c26 = Constraint([i for i in range(num_TR)], rule = constraint_26_rule)

    def constraint_27_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys() and (((i, j) in II) or ((j, i) in II)):
            return model.psi[i, j] <= 1 - model.s[i, j]
        else:
            return Constraint.Skip
    m.c27 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_27_rule)

    def constraint_28_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys() and (((i, j) in II) or ((j, i) in II)):
            return model.psi[i, j] <= 1 - model.tau[i, j]
        else:
            return Constraint.Skip
    m.c28 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_28_rule)

    def constraint_29_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys() and (((i, j) in II) or ((j, i) in II)):
            return model.psi[i, j] >= 1 - model.s[i, j] - model.tau[i, j]
        else:
            return Constraint.Skip
    m.c29 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_29_rule)

    def constraint_30_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys() and (((i, j) in AI) or ((j, i) in AI)):
            return model.zeta[i] >= 1 - model.s[i, j]
        else:
            return Constraint.Skip
    m.c30 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_30_rule)

    def constraint_31_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys() and (((i, j) in AI) or ((j, i) in AI)):
            return model._xi[i, j] >= model.zeta[i]
        else:
            return Constraint.Skip
    m.c31 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_31_rule)

    def constraint_32_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys() and (((i, j) in AI) or ((j, i) in AI)):
            return model._xi[i, j] >= 1 - model.s[i, j]
        else:
            return Constraint.Skip
    m.c32 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_32_rule)

    def constraint_33_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys() and (((i, j) in AI) or ((j, i) in AI)):
            return model._xi[i, j] >= 1 - model.tau[i, j]
        else:
            return Constraint.Skip
    m.c33 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_33_rule)

    def constraint_34_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys() and (((i, j) in AI) or ((j, i) in AI)):
            return model._xi[i, j] >= 1 - model.s[i, j] - model.tau[i, j]
        else:
            return Constraint.Skip
    m.c34 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_34_rule)

    def constraint_35_rule(model, i, j):
        if i != j and j in C2.keys():
            return model.x[i] + (2 * model.pl[i]) + model.d[i] + TS[i][j] <= model.x[j] + (W * (3 - model.l[i, j] - model.s[i, j] - model.o[j]))
        else:
            return Constraint.Skip
    m.c35 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_35_rule)

    def constraint_36_rule(model, i, j):
        if i != j and i in C2.keys():
            return model.x[i] + (2 * model.pl[i]) + model.d[i] + TS[i][j] <= model.x[j] + (W * (3 - model.l[i, j] - model.s[i, j] - model.o[i]))
        else:
            return Constraint.Skip
    m.c36 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_36_rule)

    def constraint_37_rule(model, i, j):
        if i != j and j in C2.keys():
            return model.x[i] + (2 * model.pl[i]) + model.d[i] + TS[i][j] <= model.x[j] + (W * (4 + model.o[j] - model.l[i, j] - model.s[i, j] - model.o[i] - model.tau[i, j]))
        else:
            return Constraint.Skip
    m.c37 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_37_rule)

    def constraint_38_rule(model, i, j):
        if i != j and i in C2.keys():
            return model.x[i] + (2 * model.pl[i]) + model.d[i] + TS[i][j] <= model.x[j] + (W * (4 + model.o[i] - model.l[i, j] - model.s[i, j] - model.o[j] - model.tau[i, j]))
        else:
            return Constraint.Skip
    m.c38 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_38_rule)

    def constraint_39_rule(model, i, j):
        if i != j and j in C2.keys():
            return model.x[i] + (2 * model.pl[i]) + model.d[i] + TS[i][j] <= model.x[j] + (W * (2 + model.o[j] - model.l[i, j] - model.s[i, j]))
        else:
            return Constraint.Skip
    m.c39 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_39_rule)

    def constraint_40_rule(model, i, j):
        if i != j and i in C2.keys():
            return model.x[i] + (2 * model.pl[i]) + model.d[i] + TS[i][j] <= model.x[j] + (W * (2 + model.o[i] - model.l[i, j] - model.s[i, j]))
        else:
            return Constraint.Skip
    m.c40 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_40_rule)

    def constraint_41_rule(model, i, j):
        if i != j and j in C2.keys():
            return model.x[i] + (2 * model.pl[i]) + model.d[i] + TS[i][j] <= model.x[j] + (W * (3 + model.o[i] + model.o[j] - model.tau[i, j] - model.l[i, j] - model.s[i, j]))
        else:
            return Constraint.Skip
    m.c41 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_41_rule)

    def constraint_42_rule(model, i, j):
        if i != j and i in C2.keys():
            return model.x[i] + (2 * model.pl[i]) + model.d[i] + TS[i][j] <= model.x[j] + (W * (3 + model.o[i] + model.o[j] - model.tau[i, j]- model.l[i, j] - model.s[i, j]))
        else:
            return Constraint.Skip
    m.c42 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_42_rule)

    def constraint_43_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys():
            return model.x[i] + (2 * model.pl[i]) + model.d[i] + TS[i][j] <= model.x[j] + (W * (3 - model.tau[i, j] - model.l[i, j] - model.s[i, j]))
        else:
            return Constraint.Skip
    m.c43 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_43_rule)

    def constraint_44_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys():
            return model.x[i] + model.pl[i] + TS[i][j] <= model.x[j] + (W * (2 + model.tau[i, j] - model.l[i, j] - model.s[i, j]))
        else:
            return Constraint.Skip
    m.c44 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_44_rule)

    def constraint_45_rule(model, i):
        return model.f1[i] >= (0.5 * W) - (0.5 * ((2 * model.x[i]) + (2 * model.pl[i]) + model.d[i]))
    m.c45 = Constraint([i for i in range(num_TR)], rule = constraint_45_rule)

    def constraint_46_rule(model, i):
        return model.f1[i] >= 0.5 * ((2 * model.x[i]) + (2 * model.pl[i]) + model.d[i]) - (0.5 * W)
    m.c46 = Constraint([i for i in range(num_TR)], rule = constraint_46_rule)

    def constraint_47_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys():
            return model.x[i] + model.pl[i] + TS[i][j] <= model.x[j] + (W * (3 + model.tau[i, j] + ES[i] + ES[j] - model.s[i, j] - model.l[i, j]))
        else:
            return Constraint.Skip
    m.c47 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_47_rule)

    def constraint_48_rule(model, i, j):
        if i != j and i in C1.keys() and j in C1.keys():
            return model.l[i, j] >= ES[j] + model.s[i, j] - model.tau[i, j] - ES[i] - 1
        else:
            return Constraint.Skip
    m.c48 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_48_rule)

    def constraint_49_1_rule(model, i, k):
        return model.td[i] >= model.g[k] - 1 + model.a[i, k]
    m.c49_1 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_49_1_rule)

    def constraint_49_2_rule(model, i, k):
        return model.td[i] <= model.g[k] + 1 - model.a[i, k]
    m.c49_2 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_49_2_rule)

    def constraint_50_rule(model, i, k):
        if TK[i] == 0:
            return model.a[i, k] <= 1 - model.t[k]
        else:
            return Constraint.Skip
    m.c50 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_50_rule)

    def constraint_51_rule(model, i, k):
        if TK[i] == 1:
            return model.a[i, k] <= model.t[k]
        else:
            return Constraint.Skip
    m.c51 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_51_rule)

    def constraint_52_rule(model, k):
        return model.t[k + 1] <= model.t[k]
    m.c52 = Constraint([k for k in range(num_row - 1)], rule = constraint_52_rule)

    def constraint_53_rule(model):
        return model.t[0] == 1
    m.c53 = Constraint(rule = constraint_53_rule)

    def constraint_54_rule(model):
        return model.t[num_row - 1] == 0
    m.c54 = Constraint(rule = constraint_54_rule)

    def constraint_55_rule(model):
        return model.g[0] == 1
    m.c55 = Constraint(rule = constraint_55_rule)

    def constraint_56_rule(model):
        return model.g[num_row - 1] == 0
    m.c56 = Constraint(rule = constraint_56_rule)

    def constraint_57_rule(model, i, k):
        return model.mx[k] >= model.tw[i] - (M * (1 - model.a[i, k]))
    m.c57 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_57_rule)

    def constraint_58_rule(model, i, k):
        return model.ru[k] >= model.y[i] + model.tw[i] - (H * (1 - model.a[i, k]))
    m.c58 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_58_rule)

    def constraint_59_rule(model, i, k):
        return model.rl[k] <= model.y[i] + (H * (1 - model.a[i, k]))
    m.c59 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_59_rule)

    def constraint_60_rule(model, i, k):
        return model.y[i] >= model.rl[k] - (H * (2 - model.a[i, k] - model.g[k]))
    m.c60 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_60_rule)

    def constraint_61_rule(model, i, k):
        return model.y[i] <= model.rl[k] + (H * (2 - model.a[i, k] - model.g[k]))
    m.c61 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_61_rule)

    def constraint_62_rule(model, i, k):
        return model.y[i] + model.tw[i] >= model.ru[k] - (H * (1 + model.g[k] - model.a[i, k]))
    m.c62 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_62_rule)

    def constraint_63_rule(model, i, k):
        return model.y[i] + model.tw[i] <= model.ru[k] + (H * (1 + model.g[k] - model.a[i, k]))
    m.c63 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_63_rule)

    def constraint_64_rule(model, i, k):
        if i in TG and k in TG:
            return model.qu[k] >= RS3 - (H * (1 + model.g[k] - model.a[i, k]))
        else:
            return Constraint.Skip
    m.c64 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_64_rule)

    def constraint_65_rule(model, i, k):
        if i in TG and k in TG:
            return model.ql[k] >= RS3 - (H * (2 - model.g[k] - model.a[i, k]))
        else:
            return Constraint.Skip
    m.c65 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_65_rule)

    def constraint_66_rule(model, k):
        return model.ru[k] + RS1 + model.qu[k] + model.ql[k - 1] <= model.rl[k - 1] + (H * (2 + model.t[k] - model.t[k - 1] - model.r[k]))
    m.c66 = Constraint([k for k in range(1, num_row)], rule = constraint_66_rule)

    def constraint_67_rule(model, k):
        return model.ru[k] + RS2 + model.qu[k] + model.ql[k - 1] <= model.rl[k - 1] + (H * (1 - model.r[k]))
    m.c67 = Constraint([k for k in range(1, num_row)], rule = constraint_67_rule)

    def constraint_68_rule(model, i, k):
        return model.ru_prime[k] >= model.rl[k] + model.mx[k] - (M * (2 - model.a[i, k] - model.g[k]))
    m.c68 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_68_rule)

    def constraint_69_rule(model, i, k):
        return model.ru_prime[k] <= model.rl[k] + model.mx[k] + (M * (2 - model.a[i, k] - model.g[k]))
    m.c69 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_69_rule)

    def constraint_70_rule(model, i, k):
        return model.rl_prime[k] >= model.rl[k] - (M * (2 - model.a[i, k] - model.g[k]))
    m.c70 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_70_rule)

    def constraint_71_rule(model, i, k):
        return model.rl_prime[k] <= model.rl[k] + (M * (2 - model.a[i, k] - model.g[k]))
    m.c71 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_71_rule)

    def constraint_72_rule(model, i, k):
        return model.ru_prime[k] >= model.ru[k] - (M * (1 + model.g[k] - model.a[i, k]))
    m.c72 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_72_rule)

    def constraint_73_rule(model, i, k):
        return model.ru_prime[k] <= model.ru[k] + (M * (1 + model.g[k] - model.a[i, k]))
    m.c73 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_73_rule)

    def constraint_74_rule(model, i, k):
        return model.rl_prime[k] >= model.ru[k] - model.mx[k] - (M * (1 + model.g[k] - model.a[i, k]))
    m.c74 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_74_rule)

    def constraint_75_rule(model, i, k):
        return model.rl_prime[k] <= model.ru[k] - model.mx[k] + (M * (1 + model.g[k] - model.a[i, k]))
    m.c75 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_75_rule)

    def constraint_76_rule(model, k):
        return model.ru_prime[k] + RS1 + model.qu[k] + model.ql[k - 1] <= model.rl_prime[k - 1] + (H * (2 + model.t[k] - model.t[k - 1] - model.r[k]))
    m.c76 = Constraint([k for k in range(1, num_row)], rule = constraint_76_rule)

    def constraint_77_rule(model, k):
        return model.ru_prime[k] + RS2 + model.qu[k] + model.ql[k - 1] <= model.rl_prime[k - 1] + (H * (1 - model.r[k]))
    m.c77 = Constraint([k for k in range(1, num_row)], rule = constraint_77_rule)

    def constraint_78_rule(model, i, k):
        return model.a[i, k] <= model.r[k]
    m.c78 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_78_rule)

    def constraint_79_rule(model, k):
        return model.r[k + 1] <= model.r[k]
    m.c79 = Constraint([k for k in range(num_row - 1)], rule = constraint_79_rule)

    def constraint_80_rule(model, k):
        return model.rl[k] <= model.ru[k]
    m.c80 = Constraint([k for k in range(num_row)], rule = constraint_80_rule)

    def constraint_81_rule(model):
        return model.ru[0] <= H
    m.c81 = Constraint(rule = constraint_81_rule)

    def constraint_82_rule(model, k):
        return sum(model.a[i, k] for i in range(num_TR)) >= model.r[k]
    m.c82 = Constraint([k for k in range(num_row)], rule = constraint_82_rule)

    def constraint_83_rule(model, i):
        if i in SG:
            return model._y2[i] >= model.y[i] - (H * (1 - model.td[i]))
        else:
            return Constraint.Skip
    m.c83 = Constraint([i for i in range(num_TR)], rule = constraint_83_rule)

    def constraint_84_rule(model, i):
        if i in SG:
            return model._y2[i] <= model.y[i] + (H * (1 - model.td[i]))
        else:
            return Constraint.Skip
    m.c84 = Constraint([i for i in range(num_TR)], rule = constraint_84_rule)

    def constraint_85_rule(model, i):
        if i in SG:
            return model._y2[i] >= model.y[i] + model.tw[i] - (H * model.td[i])
        else:
            return Constraint.Skip
    m.c85 = Constraint([i for i in range(num_TR)], rule = constraint_85_rule)

    def constraint_86_rule(model, i):
        if i in SG:
            return model._y2[i] <= model.y[i] + model.tw[i] + (H * model.td[i])
        else:
            return Constraint.Skip
    m.c86 = Constraint([i for i in range(num_TR)], rule = constraint_86_rule)

    def constraint_87_rule(model, i, j, p, q):
        if i != j and (i, j) in SG_SG:
            return model.e1[i, j] >= model.wx[i, j] + (alpha2[i][p][j][q] * (model._y2[i] - model._y2[j])) - (M * (2 + model.s[i, j] - model.u[i, p] - model.u[j, q]))
        else:
            return Constraint.Skip
    m.c87 = Constraint([(i, j, p, q) for i in range(num_TR) for j in range(num_TR) for p in range(len(P[i])) for q in range(len(P[j]))], rule = constraint_87_rule)

    def constraint_88_rule(model, i, j, p, q):
        if i != j and (i, j) in SG_SG:
            return model.e1[i, j] >= model.wx[i, j] + (alpha2[i][p][j][q] * (model._y2[j] - model._y2[i])) - (M * (2 + model.s[i, j] - model.u[i, p] - model.u[j, q]))
        else:
            return Constraint.Skip
    m.c88 = Constraint([(i, j, p, q) for i in range(num_TR) for j in range(num_TR) for p in range(len(P[i])) for q in range(len(P[j]))], rule = constraint_88_rule)

    def constraint_89_rule(model, i, j):
        if i != j and (i, j) in SG_SG:
            return model.e1[i, j] >= model.wx[i, j] - (M * (1 - model.s[i, j]))
        else:
            return Constraint.Skip
    m.c89 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_89_rule)

    def constraint_90_rule(model, i):
        return model.tr[i] == sum(k * model.a[i, k] for k in range(num_row))
    m.c90 = Constraint([i for i in range(num_TR)], rule = constraint_90_rule)

    def constraint_91_rule(model, i, j):
        if i != j and (i, j) in SG_O:
            return model.tr[i] - model.tr[j] <= num_row * model.b[i, j]
        else:
            return Constraint.Skip
    m.c91 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_91_rule)

    def constraint_92_rule(model, i, j):
        if i != j and (i, j) in SG_O:
            return model.b[i, j] + model.v[i, j] + model.s[i, j] == 1
        else:
            return Constraint.Skip
    m.c92 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_92_rule)

    def constraint_93_rule(model, i, j, p, q):
        if i != j and (i, j) in SG_O:
            return model.e2[i, j] >= model.wx[i, j] + (alpha2[i][p][j][q] * (model.y[i] - model.y[j] - model.tw[j])) - (M * (4 - model.v[i, j] - model.u[i, p] - model.u[j, q] - model.td[i]))
        else:
            return Constraint.Skip
    m.c93 = Constraint([(i, j, p, q) for i in range(num_TR) for j in range(num_TR) for p in range(len(P[i])) for q in range(len(P[j]))], rule = constraint_93_rule)

    def constraint_94_rule(model, i, j, p, q):
        if i != j and (i, j) in SG_O:
            return model.e2[i, j] >= model.wx[i, j] + (N[i][p] * TW[i][p]) + (alpha2[i][p][j][q] * (model.y[i] - model.y[j] - model.tw[j])) - (M * (3 - model.v[i, j] - model.u[i, p] - model.u[j, q] + model.td[i]))
        else:
            return Constraint.Skip
    m.c94 = Constraint([(i, j, p, q) for i in range(num_TR) for j in range(num_TR) for p in range(len(P[i])) for q in range(len(P[j]))], rule = constraint_94_rule)

    def constraint_95_rule(model, i, j, p, q):
        if i != j and (i, j) in SG_O:
            return model.e2[i, j] >= model.wx[i, j] + (alpha2[i][p][j][q] * (model.y[j] - model.y[i] - model.tw[i])) - (M * (3 - model.b[i, j] - model.u[i, p] - model.u[j, q] + model.td[i]))
        else:
            return Constraint.Skip
    m.c95 = Constraint([(i, j, p ,q) for i in range(num_TR) for j in range(num_TR) for p in range(len(P[i])) for q in range(len(P[j]))], rule = constraint_95_rule)

    def constraint_96_rule(model, i, j, p, q):
        if i != j and (i, j) in SG_O:
            return model.e2[i, j] >= model.wx[i, j] + (N[i][p] * TW[i][p]) + (alpha2[i][p][j][q] * (model.y[j] - model.y[i] - model.tw[i])) - (M * (4 - model.b[i, j] - model.u[i, p] - model.u[j, q] - model.td[i]))
        else:
            return Constraint.Skip
    m.c96 = Constraint([(i, j, p, q) for i in range(num_TR) for j in range(num_TR) for p in range(len(P[i])) for q in range(len(P[j]))], rule = constraint_96_rule)

    def constraint_97_rule(model, i, j, p, q):
        if i != j and (i, j) in SG_O:
            return model.e2[i, j] >= model.wx[i, j] - (M * (1 - model.s[i, j]))
        else:
            return Constraint.Skip
    m.c97 = Constraint([(i, j, p ,q) for i in range(num_TR) for j in range(num_TR) for p in range(len(P[i])) for q in range(len(P[j]))], rule = constraint_97_rule)

    def constraint_98_rule(model, i, j, p, q):
        if i != j and (i, j) in O_O:
            return model.e3[i, j] >= model.wx[i, j] + (alpha2[i][p][j][q] * (model.y[i] - model.y[j] - model.tw[j])) - (M * (2 + model.s[i, j] - model.u[i, p] - model.u[j, q]))
        else:
            return Constraint.Skip
    m.c98 = Constraint([(i, j, p, q) for i in range(num_TR) for j in range(num_TR) for p in range(len(P[i])) for q in range(len(P[j]))], rule = constraint_98_rule)

    def constraint_99_rule(model, i, j, p ,q):
        if i != j and (i, j) in O_O:
            return model.e3[i, j] >= model.wx[i, j] + (alpha2[i][p][j][q] * (model.y[j] - model.y[i] - model.tw[i])) - (M * (2 + model.s[i, j] - model.u[i, p] - model.u[j, q]))
        else:
            return Constraint.Skip
    m.c99 = Constraint([(i, j, p, q) for i in range(num_TR) for j in range(num_TR) for p in range(len(P[i])) for q in range(len(P[j]))], rule = constraint_99_rule)

    def constraint_100_rule(model, i, j):
        if i != j and (i, j) in O_O:
            return model.e3[i, j] >= model.wx[i, j] - (M * (1 - model.s[i, j]))
        else:
            return Constraint.Skip
    m.c100 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_100_rule)

    def constraint_101_rule(model, i, k):
        return model.wd[i] >= model.mx[k] - model.tw[i] - (H * (1 - model.a[i, k]))
    m.c101 = Constraint([(i, k) for i in range(num_TR) for k in range(num_row)], rule = constraint_101_rule)

    def constraint_102_rule(model, i, j):
        if row_restriction and i != j and ((i, j) in O_O) or ((i, j) in SG_O) or ((i, j) in SG_SG):
            return model.tr[i] - model.tr[j] <= 1
        else:
            return Constraint.Skip
    m.c102= Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_102_rule)

    def constraint_103_rule(model, i, j):
        if row_restriction and i != j and ((i, j) in O_O) or ((i, j) in SG_O) or ((i, j) in SG_SG):
            return model.tr[j] - model.tr[i] <= 1
        else:
            return Constraint.Skip
    m.c103 = Constraint([(i, j) for i in range(num_TR) for j in range(num_TR)], rule = constraint_103_rule)

    def constraint_104_rule(model, k):
        return model.my <= model.rl[k] + (H * (1 - model.r[k]))
    m.c104 = Constraint([k for k in range(num_row)], rule = constraint_104_rule)

    # Highs
    solver = appsi.solvers.highs.Highs()
    solver.highs_options = {'time_limit' : 30}
    solver.highs_options = {'mip_rel_gap' : 0.9}
    solver.config.stream_solver = True  # Highs 결과 출력
    results = solver.solve(m)

    """# Gurobi
    solver = SolverFactory('gurobi')
    solver.options['TimeLimit'] = 10
    results = solver.solve(m)
    #results = solver.solve(m, tee = True, timelimit = 30)"""

    x_coord = []
    y_coord = []
    split_distance = []
    selected_pattern = []
    gate_direction = []

    for i in range(num_TR):
        x_coord.append((i, m.x[i].value))
        y_coord.append((i, m.y[i].value))
        split_distance.append((i, m.d[i].value))
        for p in range(len(P[i])):
            if m.u[i, p].value >= 0.9:
                selected_pattern.append((str(i) + str(p), m.u[i, p].value))

    selected_TW = []
    selected_PL = []
    selected_O = []

    for idx, pattern in enumerate(selected_pattern):
        tr = idx
        p = int(pattern[0][-1])
        selected_TW.append(TW[tr][p])
        selected_PL.append(PL[tr][p])
        selected_O.append(O[tr][p])

    TR_names = {0: "OP", 1: "MN", 2: "CD", 3: "EF", 4: "AB", 5: "KI", 6: "GH", 7: "IJ", 8: "Z5", 9: "Z2", 10: "Z3",
                11: "Z4", 12: "Z8", 13: "Z12", 14: "Z13", 15: "Z11", 16: "Z9", 17: "Z10", 18: "Z7", 19: "Z6"}
    print("\n# (x, y) coordinates and split distances")
    for idx, coord in enumerate(zip(x_coord, y_coord)):
        print(f"{C[idx]} ({TR_names[idx]}) Coordinate: {coord[0][0], coord[1][0]} => {coord[0][1], coord[1][1]}")
        print(f"TW / PL: {selected_TW[idx]} / {selected_PL[idx]}, d[{idx}]: {split_distance[idx][1]}\n")

    x_coords = [x_coord[i][1] for i in range(len(x_coord))]
    y_coords = [y_coord[i][1] for i in range(len(y_coord))]
    split_distances = [split_distance[i][1] for i in range(len(split_distance))]

    return selected_TW, selected_PL, selected_O, x_coords, y_coords, split_distances, gate_direction

    # result
    print("Status:", results.solver.termination_condition)
    print("Objective Value:", m.obj())

if __name__ == "__main__":
    file_path = "./NETLIST_230418_modified.txt"
    save_path = "."
    sets, parameters = input_data(file_path, W=55, H=10, lambda1=0, lambda2=0, lambda3=0, lambda4=0, MS=0.5, RS1=2.0, RS2=0.4, RS3=0.2, K=2)
    row_restriction = True
    TW, PL, o_pattern, x_coord, y_coord, split_distances, gate_direction = solve_placement_opt(sets, parameters, row_restriction)
    placement_visualization(save_path, sets["C"], sets["C1"], sets["C2"], parameters["W"], parameters["H"], TW, PL, x_coord, y_coord, split_distances, o_pattern, gate_direction)


