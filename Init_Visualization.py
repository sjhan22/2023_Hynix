import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
# %matplotlib inline

def placement_visualization(path:str, _C:dict, _C1:dict, _C2:dict, _Width:float, _Height:float, _TW:list, _PL:list,
                            _x_coordinates:list, _y_coordinates:list, _split_distances:list, _o_pattern:list, _g:list)->None:
         
    fig, ax = plt.subplots(figsize=(15, 12))
    plt.axis([0, _Width, 0, _Height])
    
    # TR_names = _C
    TR_names = {0:"OP", 1:"MN", 2:"CD", 3:"EF", 4:"AB", 5:"KI", 6:"GH", 7:"IJ", 8:"Z5", 9:"Z2", 10:"Z3", 11:"Z4", 12:"Z8", 13:"Z12", 14:"Z13", 15:"Z11", 16:"Z9", 17:"Z10", 18:"Z7", 19:"Z6" }
    
    ax.axvline(_Width / 2, 0, _Height, color='red', linestyle='--', linewidth=2)
    for i in range(len(_C.keys())):
        if _o_pattern[i] == 1:
            ax.add_patch(Rectangle((_x_coordinates[i], _y_coordinates[i]), _PL[i] * 2, _TW[i], facecolor="gray", edgecolor='k'))
            ax.annotate(TR_names[i], (_x_coordinates[i] + 0.2, _y_coordinates[i] + (_TW[i] / 2) - 0.1), color='black', fontsize=10) 
            
            # if _g[i] == 1:
            #     ax.add_patch(Rectangle((_x_coordinates[i], _y_coordinates[i] + _TW[i]), _PL[i] * 2, 0.2, facecolor="red", edgecolor='k'))
            # else:
            #     ax.add_patch(Rectangle((_x_coordinates[i], _y_coordinates[i] - 0.2), _PL[i] * 2, 0.2, facecolor="red", edgecolor='k'))
        
        elif (_o_pattern[i] == 0) & (i in _C1.keys()):
            ax.add_patch(Rectangle((_x_coordinates[i], _y_coordinates[i]), _PL[i], _TW[i], facecolor="coral", edgecolor='k'))
            ax.annotate(TR_names[i], (_x_coordinates[i] + (_PL[i] / 2) - .7, _y_coordinates[i] + (_TW[i] / 2) - 0.1), color='black', fontsize=10)
            
            # if _g[i] == 1:
            #     ax.add_patch(Rectangle((_x_coordinates[i], _y_coordinates[i] + _TW[i]), _PL[i], 0.2, facecolor="red", edgecolor='k'))
            # else:
            #     ax.add_patch(Rectangle((_x_coordinates[i], _y_coordinates[i] - 0.2), _PL[i] * 2, 0.2, facecolor="red", edgecolor='k'))
            
            ax.add_patch(Rectangle((_x_coordinates[i] + _PL[i] + _split_distances[i], _y_coordinates[i]), _PL[i], _TW[i], facecolor="coral", edgecolor='k'))
            ax.annotate(TR_names[i], (_x_coordinates[i] + _PL[i] + _split_distances[i] + (_PL[i] / 2) - .7, _y_coordinates[i] + (_TW[i] / 2) - 0.1), color='black', fontsize=10)
        
        elif (_o_pattern[i] == 0) & (i in _C2.keys()):
            ax.add_patch(Rectangle((_x_coordinates[i], _y_coordinates[i]), _PL[i], _TW[i], facecolor="gray", edgecolor='k'))
            ax.annotate(TR_names[i], (_x_coordinates[i] + (_PL[i] / 2) - .7, _y_coordinates[i] + (_TW[i] / 2) - 0.1), color='black', fontsize=10)
            
            ax.add_patch(Rectangle((_x_coordinates[i] + _PL[i] + _split_distances[i], _y_coordinates[i]), _PL[i], _TW[i], facecolor="gray", edgecolor='k'))
            ax.annotate(TR_names[i], (_x_coordinates[i] + _PL[i] + _split_distances[i] + (_PL[i] / 2) - .7, _y_coordinates[i] + (_TW[i] / 2) - 0.1), color='black', fontsize=10)
    
    plt.savefig(path+'/Initial Structure.png', dpi=300)    
    plt.show()