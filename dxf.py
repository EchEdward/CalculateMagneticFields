import ezdxf, pickle

with open('table_color.pkl', "rb" ) as f:
    colors  = pickle.load(f)

def OpenFile(fname):
    dwg = ezdxf.readfile(fname)
    modelspace = dwg.modelspace()

    type_layers = ["objects","areas","receiver"]

    layers = {}
    for e in modelspace:
        ind = e.dxf.layer.find("-")
        tp_l = e.dxf.layer[:ind].lower()
        name = e.dxf.layer[ind:]
        if tp_l==type_layers[0]:
            layers[e.dxf.layer] = {"name":name,"type":tp_l,"circle":{},"lwpolyline":{},\
                "size":[float("inf"),float("inf"),-float("inf"),-float("inf"),]}
        elif tp_l==type_layers[1]:
            layers[e.dxf.layer] = {"name":name,"type":tp_l,"line":{},"point":{},"rectangle":{},\
                "size":[float("inf"),float("inf"),-float("inf"),-float("inf"),]}
        elif tp_l==type_layers[2]:
            layers[e.dxf.layer] = {"name":name,"type":tp_l,"line":{},"size":[float("inf"),float("inf"),-float("inf"),-float("inf"),]}

    for key in layers:
        lines = modelspace.query('LINE[layer=="'+key+'"]')
        for i in lines:
            a=i.dxf.start
            b=i.dxf.end
            if layers[key]["type"] == type_layers[0]:
                layers[key]["lwpolyline"][str(i)]=[[a[0],a[1]],[b[0],b[1]]]
            else:
                layers[key]["line"][str(i)]=[a[0],a[1],b[0],b[1]]
            layers[key]["size"][2]=max(layers[key]["size"][2],a[0],b[0])
            layers[key]["size"][0]=min(layers[key]["size"][0],a[0],b[0])
            layers[key]["size"][3]=max(layers[key]["size"][3],a[1],b[1])
            layers[key]["size"][1]=min(layers[key]["size"][1],a[1],b[1])

        if layers[key]["type"] == type_layers[0]:
            circles = modelspace.query('CIRCLE[layer=="'+key+'"]')
            for i in circles:
                a=i.dxf.center
                r=i.dxf.radius
                layers[key]["circle"][str(i)]=[a,r]
                layers[key]["size"][2]=max(layers[key]["size"][2],a[0]+r)
                layers[key]["size"][0]=min(layers[key]["size"][0],a[0]-r)
                layers[key]["size"][3]=max(layers[key]["size"][3],a[1]+r)
                layers[key]["size"][1]=min(layers[key]["size"][1],a[1]-r)

        """ arcs = modelspace.query('ARC[layer=="'+key+'"]')
        for i in arcs:
            a=i.dxf.center
            r=i.dxf.radius
            layers[key]["arc"][str(i)]=[a,r,i.dxf.start_angle,i.dxf.end_angle]
            layers[key]["size"][2]=max(layers[key]["size"][2],a[0]+r)
            layers[key]["size"][0]=min(layers[key]["size"][0],a[0]-r)
            layers[key]["size"][3]=max(layers[key]["size"][3],a[1]+r)
            layers[key]["size"][1]=min(layers[key]["size"][1],a[1]-r) """

        
        if layers[key]["type"] == type_layers[0] or layers[key]["type"] == type_layers[1]:
            polylines = modelspace.query('LWPOLYLINE[layer=="'+key+'"]')
            for i in polylines:
                p=i.get_points()
                if not i.closed and layers[key]["type"] == type_layers[0]:
                    x=[i[0] for i in p]
                    y=[i[1] for i in p]
                    layers[key]["lwpolyline"][str(i)]=p
                    layers[key]["size"][2]=max([layers[key]["size"][2]]+x)
                    layers[key]["size"][0]=min([layers[key]["size"][0]]+x)
                    layers[key]["size"][3]=max([layers[key]["size"][3]]+y)
                    layers[key]["size"][1]=min([layers[key]["size"][1]]+y)
                
                elif i.closed and len(p)==4 and layers[key]["type"] == type_layers[1]:
                    arr = [min(p[0][0],p[2][0]),min(p[0][1],p[2][1]),max(p[0][0],p[2][0]),max(p[0][1],p[2][1])]
                    layers[key]["rectangle"][str(i)]=arr
                    layers[key]["size"][2]=max(layers[key]["size"][2],arr[2])
                    layers[key]["size"][0]=min(layers[key]["size"][0],arr[0])
                    layers[key]["size"][3]=max(layers[key]["size"][3],arr[3])
                    layers[key]["size"][1]=min(layers[key]["size"][1],arr[1])

        if layers[key]["type"] == type_layers[1]:
            points = modelspace.query('POINT[layer=="'+key+'"]')
            for i in points:
                xy=i.dxf.location
                layers[key]["point"][str(i)]=[xy[0],xy[1]]
                layers[key]["size"][2]=max(layers[key]["size"][2],xy[0])
                layers[key]["size"][0]=min(layers[key]["size"][0],xy[0])
                layers[key]["size"][3]=max(layers[key]["size"][3],xy[1])
                layers[key]["size"][1]=min(layers[key]["size"][1],xy[1])     
            
    return layers

def color_distance(rgb1, rgb2):
    rm = 0.5 * (rgb1[0] + rgb2[0])
    rd = ((2 + rm) * (rgb1[0] - rgb2[0])) ** 2
    gd = (4 * (rgb1[1] - rgb2[1])) ** 2
    bd = ((3 - rm) * (rgb1[2] - rgb2[2])) ** 2
    return (rd + gd + bd) ** 0.5


def SaveInDXF(sp_points,sp_levels,sp_obj,fname):

    #dwg = ezdxf.readfile(fname)
    #modelspace = dwg.modelspace()
    # Create a new DXF document.
    if fname[1]:
        doc = ezdxf.new(dxfversion='R2010')
        doc.layers.new('OBJECTS') #, dxfattribs={'color': 160}
    else:
        doc = ezdxf.readfile(fname[0])

    # Create new table entries (layers, linetypes, text styles, ...).
    doc.layers.new('POINTS', dxfattribs={'color': 160}) #
    doc.layers.new('LEVELS') #, dxfattribs={'color': 160}
    

    # DXF entities (LINE, TEXT, ...) reside in a layout (modelspace, 
    # paperspace layout or block definition).  
    msp = doc.modelspace()

    # Add entities to a layout by factory methods: layout.add_...() 
    for i in sp_points:
        msp.add_circle(i[:2],50, dxfattribs={'layer': 'POINTS'})
        msp.add_line((i[0]-50, i[1]), (i[0]+50, i[1]), dxfattribs={'layer': 'POINTS'})
        msp.add_line((i[0], i[1]-50), (i[0], i[1]+50), dxfattribs={'layer': 'POINTS'})
        msp.add_text(i[2],
            dxfattribs={'layer': 'POINTS',
                        'height': 2.5}).set_pos((i[0], i[1]+52.5), align='CENTER')

    for i in sp_levels:
        for j in i[2][0]:
            line_color = min([(v,color_distance(i[1], k)) for k,v in colors.items()],key=lambda a:a[1])[0]
            msp.add_lwpolyline(j*1000, dxfattribs={'layer': 'LEVELS','color': line_color}) #



    if fname[1]:
        for i in sp_obj:
            if i[0] == "reactor":
                msp.add_circle((i[1],i[2]),i[3], dxfattribs={'layer': 'OBJECTS'})
            elif i[0] == "conductor":
                cord = [(j[0],-j[1]) for j in i[1]] #,0,0,0
                msp.add_lwpolyline(cord, dxfattribs={'layer': 'OBJECTS'})

    # Save DXF document.
    doc.saveas(fname[0])

    print('dxf is save')


