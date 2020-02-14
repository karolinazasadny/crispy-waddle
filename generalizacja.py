# -*- coding: cp1250 -*-
import arcpy
import math as m

global tolerance
global k

arcpy.env.overwriteOutput = True

tolerance = float(raw_input ("Podaj tolerancję upraszczania budynków [rad]: "))
k = int(raw_input ("Podaj liczbę wierzchołków odcinanych przez sieczną: "))

##tolerance = 0.1
##k = 3

def Azimuth (X1,X2,Y1,Y2):

    quadrant = m.atan2((Y2-Y1),(X2-X1))

    if quadrant <= 0: A = quadrant + m.pi*2
    else: A = quadrant
    return A

def Angle (X1,X2,X3,Y1,Y2,Y3):

    ang = abs(Azimuth(X2,X1,Y2,Y1) - Azimuth(X2,X3,Y2,Y3))
    return ang

def DataImport ():
    data = arcpy.MakeFeatureLayer_management(r".\Dane.shp", "data")

    buildings = []
    for row in arcpy.da.SearchCursor(data, ["OID@", "SHAPE@"]):
        parts = []
        for part in row[1]:
            vertices = []
            for i in part:
                vertices.append((i.X, i.Y))
            parts.append(vertices)
        buildings.append(parts)
    return buildings

def Simplify(buildings):

    build_simpl = []
    for build in buildings:
        vert_simpl = []
        for part in build:
            vert = 0
            for pnt in part:
                if vert == 0:
                    check = Angle(part[-1][0],part[0][0],part[1][0],part[-1][1],part[0][1],part[1][1])
                elif vert == len(part)-1:
                    check = Angle(part[-2][0],part[-1][0],part[0][0],part[-2][1],part[-1][1],part[0][1])
                else: check = Angle(part[vert-1][0],part[vert][0],part[vert+1][0],part[vert-1][1],part[vert][1],part[vert+1][1])

                if check <= m.pi-float(tolerance) or check >= m.pi+float(tolerance):
                    vert_simpl.append(pnt)
                vert+=1
        build_simpl.append(vert_simpl)
    return build_simpl

def Distance(X1,X2,Y1,Y2):
    
     dist = m.sqrt((X2-X1)**2+(Y2-Y1)**2)
     return dist

def CreateSHP(data, file_name):
    
    shp = arcpy.CreateFeatureclass_management(r".\\", str(file_name)+".shp", "POLYGON")
    cursor = arcpy.da.InsertCursor(shp, ["SHAPE@"])

    for build in data:
        cursor.insertRow([build])
    del cursor

def Secant(building):

    array = arcpy.Array([arcpy.Point(*coords) for coords in building])
    build = arcpy.Geometry("POLYGON", array)                      
    
    secants = []
    k=2
    for pnt in building[2:-2]:
        d = Distance(building[0][0],pnt[0],building[0][1],pnt[1])
        num = k+1
        diction = {'id':(str(0)+str(k)), 'lenght':d, 'vert_num':num, 'id_from':0, 'id_to':k}
        geom = arcpy.Geometry("POLYLINE", arcpy.Array([arcpy.Point(building[0][0],building[0][1]), arcpy.Point(pnt[0],pnt[1])]))
        if not geom.crosses(build):
            secants.append(diction)
        k+=1

    i=1
    for pnt in building[1:]:
        j=i+2
        for oth in building[i+2:-1]:
            d = Distance(pnt[0],oth[0],pnt[1],oth[1])
            num = j-i+1
            diction = {'id':str(i)+str(j), 'lenght':d, 'vert_num':num, 'id_from':i, 'id_to':j}
            geom = arcpy.Geometry("POLYLINE", arcpy.Array([arcpy.Point(pnt[0],pnt[1]), arcpy.Point(oth[0],oth[1])]))
            if not geom.crosses(build):
                secants.append(diction)
            j+=1
        i+=1

    secants = sorted(secants, key=lambda k: k['lenght'])
    return secants

def Generalization(secants,building):

    count = len(building)
    dict_xy = {i:building[i] for i in range (len(building))}
    xy_rej = []
    rej_draw = []
    xy_check = {}
    remain = []

    for sec in secants:
        if sec['vert_num'] >= k and sec['id_from'] not in xy_check.keys() and sec['id_to'] not in xy_check.keys():
            i=0
            count = len(building) - len(xy_check)
            if count <= 5: break
            xy_rej = []
            for vert in range(sec['id_from'], sec['id_to']+1):
                if building[vert] not in xy_check.keys():
                    if not i== 0 and not i == sec['id_to']-sec['id_from']:
                        xy_check[vert] = building[vert]
                    xy_rej.append(building[vert])
                    i+=1
            rej_draw.append(xy_rej)

    
    for pnt in dict_xy:
        if pnt not in xy_check: remain.append(dict_xy[pnt])

    return (rej_draw, [remain])
 

def main ():
    data = DataImport()
    simpl_data = Simplify(data)
    result = [Generalization(Secant(i),i) for i in simpl_data]

    rejected = []
    remained = []

    for build in result:
        rejected += build[0]
        remained += build[1]

    CreateSHP(rejected, "rejected")
    CreateSHP(remained, "remained")
    
if __name__ == '__main__':
    main()
