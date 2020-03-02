import numpy as np

mat = {"Сталь":0.115,"Медь":0.0175,"Алюминий":0.028} #Ом*мм2/м

def Distance(line):
    """ Расчёт растояния между двумя точками """
    #print(np.sqrt((line[1][0]-line[0][0])**2+(line[1][1]-line[0][1])**2))
    (x1,y1,z1),(x2,y2,z2) = line
    #np.linalg.norm(rv,axis=1)
    return np.sqrt((x2-x1)**2+(y2-y1)**2+(z2-z1)**2)


def Lies(point,line):
    """ Проверка принадлежности точки отрезку """
    (x4,y4,z4)=point
    [(x1,y1,z1),(x2,y2,z2)]=line
    e1=0.01

    if (abs(x4 - x1)<e1 and abs(y4 - y1)<e1 and abs(z4 - z1)<e1) or (abs(x4 - x2)<e1 and abs(y4 - y2)<e1 and abs(z4 - z2)<e1):
        return True
    else:
        if x1==x2==x4 and z1==z2==z4 and (y1<=y4<=y2 or y1>=y4>=y2):
            return True
        elif y1==y2==y4 and z1==z2==z4 and (x1<=x4<=x2 or x1>=x4>=x2):
            return True
        elif x1==x2==x4 and y1==y2==y4 and (z1<=z4<=z2 or z1>=z4>=z2):
            return True
        else:
            a=abs((x4-x1)*(z2-z1)-(z4-z1)*(x2-x1)) <= e1
            b=abs((x4-x1)*(y2-y1)-(y4-y1)*(x2-x1)) <= e1
            c=abs((y4-y1)*(z2-z1)-(z4-z1)*(y2-y1)) <= e1
            #print(a,b,c,(x4,y4,z4))
            return (a and b and c)

def LiesBadPoint(point,line,h):
    """ Проверка находится ли точка вблизи линии """
    if Lies(point,line):
        return point
    else:
        (x4,y4)=point
        [(x1,y1),(x2,y2)]=line
        if (y4-y1)**2+(x4-x1)**2<=h**2:
            return (x1,y1)
        if (y4-y2)**2+(x4-x2)**2<=h**2:
            return (x2,y2)
        if (x1-h<=x4<=x2+h or x1+h>=x4>=x2-h) and (y1-h<=y4<=y2+h or y1+h>=y4>=y2-h):
            point2 = Intersection(point,line)
            if point2 != None:
                if Distance([point,point2]) < h:
                    return point2

        return False

def VHLine(line):
    """ Получение близких к граничным координат на линии """
    [(x1,y1),(x2,y2)] = line
    d=Distance(line)
    m=0.1/d
    l1=m/(1-m)
    l2=(1-m)/m
    x3=(x1+x2*l1)/(1+l1)
    y3=(y1+y2*l1)/(1+l1)
    x4=(x1+x2*l2)/(1+l2)
    y4=(y1+y2*l2)/(1+l2)
    
    return [(x3,y3),(x4,y4)]

p = [
    [(1.0, 1.0, 1.0), (4.0, 1.0, 1.0), (7.0, 1.0, 1.5)],
    [(1.0, 2.0, 0.0), (7.0, 8.0, 1.0)],
    [(1.0, 1.0, 1.0), (1.0, 2.0, 0.0)],
    [(2.5, 1.0, 1.0), (3.0, 4.0, 0.333)],
    [(5.5, 1.0, 1.25), (5.0, 6.0, 0.666)],
    [(7.0, 1.0, 1.5), (7.0, 8.0, 1.0)]
]


def getGraph(pls, diam, materials):
    e = 0.01 
    nodes = set()
    branches1 = []
    for pl, i in zip(pls,range(len(pls))):
        for ip in range(1,len(pl)):
            nd1, nd2 = pl[ip-1], pl[ip]
            if nd1 not in nodes:
                for nd in nodes:
                    if Distance([nd,nd1])<=e:
                        nd1=nd
                        break
                else:
                    nodes.add(nd1)
            
            if nd2 not in nodes:
                for nd in nodes:
                    if Distance([nd,nd2])<=e:
                        nd2=nd
                        break
                else:
                    nodes.add(nd2)

            branches1.append([i, ip-1, nd1, nd2])

    branches2 = []
    for pl, ln, nd1, nd2 in branches1:
        midle_nodes = [nd1, nd2]
        for nd in nodes:
            if nd1 != nd and nd2 != nd:
                if Lies(nd,[nd1,nd2]):
                    midle_nodes.append(nd)

        midle_nodes.sort(key=lambda node:Distance([nd1,node]))

        for i in range(1,len(midle_nodes)):
            branches2.append([pl,ln,midle_nodes[i-1],midle_nodes[i]])

    nodes2 = {}
    j=-1
    for pl, ln, nd1, nd2 in branches2:
        j+=1
        for nd in [nd1,nd2]:
            if nd not in nodes2:
                nodes2[nd]=1
            else:
                nodes2[nd]+=1

    nodes3 = {}
    k=-1
    for i,j in nodes2.items():
        if j>1:
            k+=1
            nodes3[i]=k

    branches3 = []
    for pl, ln, nd1, nd2 in branches2:
        if nd1 in nodes3 and nd2 in nodes3:
            branches3.append([pl, ln, nd1, nd2])

    A = np.zeros((len(nodes3),len(branches3)),dtype=np.float32)
    R, L, Lines = [], [], []

    j=-1
    for pl, ln, nd1, nd2 in branches3:
        j+=1
        A[nodes3[nd1],j] = -1
        A[nodes3[nd2],j] =  1

        d = Distance([nd1, nd2])
        Lc = 5.081*(np.log(4*d/(diam[pl][ln]*10**-3))-1)*10**-9
        Rc = mat[materials[pl][ln]]*d/(np.pi*diam[pl][ln]**2/4)
        L.append(Lc)
        R.append(Rc)
        Lines.append((nd1,nd2))

    return A, tuple(Lines), tuple(R), tuple(L)



    """ for i,j in nodes3.items():
        print(i,j)
    for i in branches3:
        print(i)

    print(A) """

#getGraph(p)