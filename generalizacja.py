# -*- coding: cp1250 -*-
import arcpy
import math as m

global tolerance
global k

arcpy.env.overwriteOutput = True

##tolerance = raw_input ("Podaj tolerancję upraszczania budynków [rad]: ")
##k = raw_input ("Podaj liczbę wierzchołków odcinanych przez sieczną: ")

tolerance = 0.01
k = 4

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
        for part in row[1]:
            vertices = []
            for i in part:
                vertices.append((i.X, i.Y))
        buildings.append(vertices)
    return buildings

def Simplify(buildings):

    build_simpl = []
    for build in buildings:
        vert = 0
        vert_simpl = []
        for pnt in build:
            if vert == 0:
                check = Angle(build[-1][0],build[0][0],build[1][0],build[-1][1],build[0][1],build[1][1])
            elif vert == len(build)-1:
                check = Angle(build[-2][0],build[-1][0],build[0][0],build[-2][1],build[-1][1],build[0][1])
            else: check = Angle(build[vert-1][0],build[vert][0],build[vert+1][0],build[vert-1][1],build[vert][1],build[vert+1][1])

            if check <= m.pi-float(tolerance) or check >= m.pi+float(tolerance):
                vert_simpl.append(pnt)
            vert+=1
        build_simpl.append(vert_simpl)
    return build_simpl

def CreateSHP(data, file_name):
    shp = arcpy.CreateFeatureclass_management(r".\\", str(file_name)+".shp", "POLYGON")
    cursor = arcpy.da.InsertCursor(shp, ["SHAPE@"])

    for build in data:
        cursor.insertRow([build])
    del cursor


def main ():
    data = DataImport()
    s_b = Simplify(data)
    CreateSHP(s_b, "nowe")
    
main()
