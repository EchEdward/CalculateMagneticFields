import numpy as np
import torch
from threading import Thread
from queue import Queue
from time import time
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
import scipy.interpolate
from scipy.optimize import fsolve,broyden1
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo

nvmlInit()

cuda_was_used = False


alf1=np.cos(240*np.pi/180)+1j*np.sin(240*np.pi/180)
alf2=np.cos(120*np.pi/180)+1j*np.sin(120*np.pi/180)

alf3=np.cos(0*np.pi/180)+1j*np.sin(0*np.pi/180)
alf4=np.cos(180*np.pi/180)+1j*np.sin(180*np.pi/180)

def check_memory():
    device = torch.cuda.current_device()
    h = nvmlDeviceGetHandleByIndex(0)
    info = nvmlDeviceGetMemoryInfo(h)

    use_mr = torch.cuda.memory_allocated(device)
    reserv_mr = torch.cuda.memory_cached(device)

    print(f'nvidia_total    : {info.total}')
    print(f'nvidia_free     : {info.free}')
    print(f'nvidia_used     : {info.used}')
    print('use_memory_for_tensors: ',use_mr)
    print('reserved_memory       : ',reserv_mr)
    print("-"*10)

def distribution_memory(dl, cord):
    global cuda_was_used
    device = torch.cuda.current_device()
    h = nvmlDeviceGetHandleByIndex(0)
    info = nvmlDeviceGetMemoryInfo(h)

    busy_memory = torch.cuda.memory_allocated(device)
    reserv_memory = torch.cuda.memory_cached(device)

    free_memory = info.free + reserv_memory - busy_memory
    if not cuda_was_used:
        free_memory-=252*1024**2
        cuda_was_used = True
   
    Trig = []
    used_memory = 0
    for obj in range(len(dl)):
        used_memory += dl[obj].nbytes+cord[obj].nbytes
        Trig.append(free_memory > used_memory)

    print("free memory: ",(free_memory-used_memory)/1024**2)

    return Trig


def VHLine(x1,y1,x2,y2,l,r):
    """ Получение близких к граничным координат на линии """  
    d=r
    m=(r-l/2)/d
    l1=m/(1-m)
    x3=(x1+x2*l1)/(1+l1)
    y3=(y1+y2*l1)/(1+l1) 
    return x3,y3

def SolenParam(P,met,Rnar,Rvn,h,f,Q=None,U=None,Xl=None,I=None):
    """
    Определение количества витков и слоёв в катушке по её номинальным параметрам\n
    P - активные потери в катушке, кВт\n
    met - материал жил катушки\n
    Rnar - наружный радиус катушки, м\n
    Rvn - внутренний радиус катушки, м\n
    h - внутренний радиус катушки, м\n
    f - номинальная частота катушки, Гц\n
    Q - номинальная реактивная мощность катушки, Мвар\n
    U - номинальное напряжение катушки, кВ\n
    Xl - номинальное индуктивное сопротивлене катушки, Ом\n
    I - номинальный ток катушки, А\n
    """
    if P==None or Rnar==None or Rvn==None or h==None or f==None: return
    po = {"Медь":0.0175,"Алюминий":0.028}
    P*=10**3
    if Q!=None or U!=None:
        Q*=10**6
        U*=10**3
        L = U**2/(2*np.pi*f*Q)/ np.sqrt(3)
        Rpr = U**2/P/ np.sqrt(3)
    elif Xl!=None or I!=None:
        L=Xl/(2*np.pi*f)
        Rpr = P/I**2
    else:
        return
    
    W = int(np.sqrt(L*(6*((Rnar+Rvn)/2)+(Rnar-Rvn)*h+10*(Rnar-Rvn))/\
                (0.32*10**-4*((Rnar+Rvn)/2)**2)))
    
    #print(W,L,Rpr)
    param = []
    e=float("inf")
    for m in range(1,31):
        try:
            lvb = (Rnar-Rvn)/(m-1) if m>1 else (Rnar-Rvn)
            Rs =[Rnar-i*lvb for i in range(m)]
            lsum = sum([2*np.pi*Rs[i]*W/m+h for i in range(m)])
            rpr = np.sqrt((po[met]*lsum/Rpr)/np.pi)/10**3
            
            # Проверка на пересечение проводников
            t1 = lvb>=4*rpr if m>1 else lvb>=2*rpr
            t2 = rpr<=h/(2*(W/m))
            # Коэффициенты заполнения по вертикали и горизонтали
            Kh = (W/m*2*rpr)/h
            Kw = ((m-1)*4*rpr)/(Rnar-Rvn) if m>1 else 2*rpr/(Rnar-Rvn)


            if e>abs(Kh-Kw):
                if t1 and t2:
                    e=abs(Kh-Kw)
                    param.append([m,t1,t2,Kh,Kw])
            else:
                if len(param)==0: return
                return W, param[len(param)-1][0]
            
        except Exception:
            break

    return
    
   
#print(SolenParam(473.4*10**3,"Алюминий",1.17,0.8,1.84 ,50 ,Q=13.3,U=10))

def Solinoid1(x,y,z,r,h,n,m,l,dalf):
    """
    Построение координат элементарных участков соленойда\n
    x,y,z, - координаты отсчёта построения соленойда\n
    r - внешний радиус соленойда\n
    h - высота соленойда\n
    n - количество витков в соленойде\n
    m - количество слоёв соленойде\n
    l - растояние между слоями\n
    dalf - угловая длинна элементарного участка\n
    """
    tvr = int(h//(np.deg2rad(dalf)*r))+2
    ns = [int((n-(n%m))/(m-(0 if n%m==0 else 1))) if i!=m-1 else n//m for i in range(m)]
    ti = [int(360/dalf*i)+1 for i in ns]
    t = sum(ti)+(m-1)*tvr
    ri=[r-i*l for i in range(m)]
    ri.reverse()
    #print(ri)
    cordinates = np.zeros((t,3),dtype=np.float32)
    dl = np.zeros((t-1,3),dtype=np.float32)

    k=-1
    for i in range(m):
        for j in range(ti[i]):
            k+=1
            cordinates[k][0] = ri[i]*np.cos(2*np.pi*j*ns[i]/(ti[i]-1))+x
            cordinates[k][1] = ri[i]*np.sin(2*np.pi*j*ns[i]/(ti[i]-1))+y
            cordinates[k][2] = h*j/(ti[i]-1) + z
            if k>=1:
                dl[k-1] = cordinates[k:k+1,:]-cordinates[k-1:k,:]
            
            #print(cordinates[k][0],cordinates[k][1],cordinates[k][2],"v")

        if i != m-1:
            xpr = cordinates[k][0]-l/2
            for j in range(tvr):
                k+=1
                cordinates[k][0] = xpr
                cordinates[k][1] = cordinates[k-1][1]
                cordinates[k][2] = h*(1-j/(tvr-1)) + z
                dl[k-1] = cordinates[k:k+1,:]-cordinates[k-1:k,:]
                #print(cordinates[k][0],cordinates[k][1],cordinates[k][2],'prt')

    
    return cordinates, dl


    

def Solinoid(x,y,z,r,h,n,t):
    """
    Построение координат элементарных участков соленойда\n
    x,y,z, - координаты отсчёта построения соленойда\n
    r - радиус соленойда\n
    h - высота соленойда\n
    n - количество витков в соленойде\n
    t - угловая длинна элементарного участка\n
    """
    # 
    t = int(360/t*n)
    cordinates = np.zeros((t,3),dtype=np.float32)
    dl = np.zeros((t-1,3),dtype=np.float32)
    
    for i in range(t):
        cordinates[i][0] = r*np.cos(2*np.pi*i*n/t)+x
        cordinates[i][1] = r*np.sin(2*np.pi*i*n/t)+y
        cordinates[i][2] = h*i/t + z
        if i>=1:
            dl[i-1] = cordinates[i:i+1,:]-cordinates[i-1:i,:]

    return cordinates, dl


def equations(a,x,y):
    return (a[0]+a[1]*x[0]+a[2]*x[0]**2-y[0],
            a[0]+a[1]*x[1]+a[2]*x[1]**2-y[1],
            a[0]+a[1]*x[2]+a[2]*x[2]**2-y[2])


def Parab(p1,p2,p3):
    f = lambda a: equations(a,(p1[0],p2[0],p3[0]),(p1[1],p2[1],p3[1]))
    a = fsolve(f, (1, 1, 1))
    return lambda x: a[0]+a[1]*x+a[2]*x**2



#print(type(Parab((0,3),(1,2),(2,3))))



def Line(points,DL, fmax = None):
    dist = [((points[i][0]-points[i-1][0])**2+\
            (points[i][1]-points[i-1][1])**2+\
            (points[i][2]-points[i-1][2])**2)**0.5 for i in range(1,len(points))]

    st = [int(i/DL) for i in dist]

    t = sum(st)+1
    cordinates = np.zeros((t,3),dtype=np.float32)
    dl = np.zeros((t-1,3),dtype=np.float32)

    k = -1
    for i in range(len(st)):
        if fmax is not None:
            f = Parab((0,points[i][2]),(dist[i]/2,fmax[i]),(dist[i],points[i+1][2]))
        for j in range(st[i]+1):
            if j==st[i] and len(st)-1!=i: continue
            k+=1

            m=DL*j/dist[i]

            cordinates[k][0] = (points[i][0]+points[i+1][0]*(m/(1-m)))/(1+(m/(1-m))) if j != st[i] else points[i+1][0]
            cordinates[k][1] = (points[i][1]+points[i+1][1]*(m/(1-m)))/(1+(m/(1-m))) if j != st[i] else points[i+1][1]
            if fmax is not None: #
                cordinates[k][2] = f(DL*j) if j != st[i] else points[i+1][2]
                #print(cordinates[k][2])
            else:
                cordinates[k][2] = (points[i][2]+points[i+1][2]*(m/(1-m)))/(1+(m/(1-m))) if j != st[i] else points[i+1][2]
            if k>=1:
                dl[k-1] = cordinates[k:k+1,:]-cordinates[k-1:k,:]

    return cordinates, dl





def MagnetikVoltage(I,cordinates,dl,x,y,z):
    """
    Расчёт напряжённости от одного проводника\n
    I - ток в расматриваем проводнике\n
    cordinates - координаты элементрных участков проводника\n
    dl - длинна элементарных участков\n
    x,y,z - координаты точки в которой определяем напряжённость поля\n
    """
    t = np.shape(dl)[0]
    point = np.array([x,y,z],dtype=np.float64)
    rv = (point - cordinates)[:t,:]
    r = 1/(4*np.pi*np.linalg.norm(rv,axis=1)**3)
    r.shape = (t,1)
    dH = np.cross(dl, rv)*r
    rez = np.sum(dH,axis=0)*I
    return np.array([rez[0] if not np.isnan(rez[0]) else I,\
                    rez[1] if not np.isnan(rez[1]) else I,\
                    rez[2] if not np.isnan(rez[2]) else I,],dtype=np.float64)

def MagnetikVoltageTorch(device,I,cordinates,dl,x,y,z,alfs,qu,H_area):
    """
    Расчёт напряжённости от одного проводника\n
    I - ток в расматриваем проводнике\n
    cordinates - координаты элементрных участков проводника\n
    dl - длинна элементарных участков\n
    x,y,z - координаты точки в которой определяем напряжённость поля\n
    """
    while True:
        task_for, k, obj = qu.get()

        if task_for is None and k is None and obj is None:
            break

        t = dl[obj].size()[0]
        point = torch.tensor([x[k],y[k],z],dtype=torch.float32).to(device)
        rv = (point - cordinates[obj])[:t,:]
        r = 1/(4*np.pi*torch.norm(rv,dim=1)**3)
        r = torch.reshape(r, (t,1))
        dH = torch.cross(dl[obj], rv)*r
        rez = torch.sum(dH,dim=0)*I[obj]
        trig = torch.isnan(rez)
        rt = torch.tensor([rez[0] if not trig[0] else I,\
                            rez[1] if not trig[1] else I,\
                            rez[2] if not trig[2] else I,],dtype=torch.float32).numpy()*alfs[obj]
        
        H_area[k,:] += rt
    
    #return rt


def MutualInduct(cordinates_1,dl_1,cordinates_2,dl_2):
    """
    Расчёт взаимной индукции между двумя произвольно расположенными проводниками\n
     
    """
    t_1 = np.shape(dl_1)[0]
    t_2 = np.shape(dl_2)[0]
    
    Cordinates_1 = cordinates_1[:t_1,:]
    Cordinates_2 = cordinates_2[:t_2,:]

    M = 0

    for i in range(t_2):
        r = 1/np.linalg.norm(Cordinates_1-Cordinates_2[i,:],axis=1)
        M += np.sum(np.dot(dl_1,dl_2[i,:])*r) 
        
 
    return M*10**-7

def SameInduct(cordinates,dl,mu=1):
    """
    Расчёт собственной индукции м проводника\n
     
    """
    t = np.shape(dl)[0]
      
    Cordinates_1 = cordinates[:t,:]
    Cordinates_2 = cordinates[1:t+1,:]

    dr = np.sum(dl,axis=0)/t
    
    M = 0

    for i in range(t):
        own = np.zeros((t,3),dtype=np.float64)
        own[i,:]=dr
        r = 1/np.linalg.norm((Cordinates_1+Cordinates_2-Cordinates_1[i,:]-Cordinates_2[i,:]+own)/2,axis=1)
        M += np.sum(np.dot(dl,dl[i,:])*r) 

    

    return (M+np.sum(np.linalg.norm(dl))/2*mu) *10**-7

def provod(xn,yn,zn,xk,yk,zk,t):
    dx = (xk-xn)/(t-1)
    dy = (yk-yn)/(t-1)
    dz = (zk-zn)/(t-1)

    cordinates = np.zeros((t,3),dtype=np.float32)
    dl = np.zeros((t-1,3),dtype=np.float32)

    cordinates[0][0] = xn
    cordinates[0][1] = yn
    cordinates[0][2] = zn

    for i in range(1,t):
        cordinates[i][0] = cordinates[i-1][0]+dx
        cordinates[i][1] = cordinates[i-1][1]+dy
        cordinates[i][2] = cordinates[i-1][2]+dz

        dl[i-1][0] = cordinates[i][0]-cordinates[i-1][0]
        dl[i-1][1] = cordinates[i][1]-cordinates[i-1][1]
        dl[i-1][2] = cordinates[i][2]-cordinates[i-1][2]

    return cordinates, dl

        
  
    
def ReadSol(d,deg):
    try:
        x, y, z = float(d["X"]), float(d["Y"]), float(d["Z"])
        Rnar = float(d["Rnar"])
        h = float(d["H"])
        n = int(d["W"])
        m = int(d["m"])
        fase = float(d["deg"])
        alf=np.cos(fase*np.pi/180)+1j*np.sin(fase*np.pi/180)
        I = float(d["I"])
        if m > 1 and d["Rvn"]=="":
            raise Exception
        elif m > 1 and float(d["Rvn"])>=Rnar:
            raise Exception
        elif m > 1:
            Rvn = float(d["Rvn"])          
            
    except Exception:
        return None
    else:
        if m > 1:
            a = [x,y,z,Rnar,h,n,m,(Rnar-Rvn)/(m-1),deg]
        else:
            a = [x,y,z,Rnar,h,n,deg]

        return (a, m, alf, I)

def ReadConduct(d,DL):
    try:
        I = float(d["I"])
        fase = float(d["deg"])
        alf=np.cos(fase*np.pi/180)+1j*np.sin(fase*np.pi/180)
        cord = []
        
        for i in range(len(d["tbl_cord"])):
            cord.append([float(d["tbl_cord"][i][0]),float(d["tbl_cord"][i][1]),float(d["tbl_cord"][i][2])])
        if d['chck_fmax']:
            fmax = []
            for i in range(len(d["tbl_fmax"])):
                fmax.append(float(d["tbl_fmax"][i]))

    except Exception:
        return None
    else:
        if d['chck_fmax']:
            a = [cord,DL,fmax]
        else:
            a = [cord,DL]

        return (a, alf, I)
        


def run_area_calc(tp,lst, area, hz, step, DL, deg):
    cordinates = []
    dls = []
    alfs = []
    Is = []
    
    for i in lst:
        if i["obj_type"] == "reactor":
            rez = ReadSol(i,deg)
            if rez is not None:
                args, m, alf, I = rez
            else: continue
            if m == 1:
                cordinate, dl = Solinoid(*args)
            elif m>1:
                cordinate, dl = Solinoid1(*args)
        elif i["obj_type"] == "conductor":
            rez = ReadConduct(i,DL)
            if rez is not None:
                args, alf, I = rez
            else: continue
            cordinate, dl = Line(*args)
            
        alfs.append(alf)
        cordinates.append(cordinate)
        dls.append(dl)
        Is.append(I)

    f = lambda x,y: (x//y+(1 if x>=0 else 0))*y if x%y!=0 else x

    if tp == "H_calc_area":
        
        area = [f(i,step) for i in area]
        col = int((area[2]-area[0])/step)+1
        row = int((area[3]-area[1])/step)+1

        #H_area = np.zeros(row*col,dtype=np.float32)
        H_area = np.zeros((row*col,3),dtype=np.complex64)
        X = np.zeros(row*col,dtype=np.float32)
        Y = np.zeros(row*col,dtype=np.float32)

        #check_memory()

        device = torch.cuda.current_device()

        #required_memory = sum([cordinates[obj].nbytes+dls[obj].nbytes for obj in range(len(dls))])
        #print("required_memory " ,required_memory)

        print(distribution_memory(dls, cordinates))

        crd1 = []
        ddllss1 = []
        crd2 = []
        ddllss2 = []
        for obj in range(len(dls)):
            #print(cordinates[obj].dtype)
            crd1.append(torch.from_numpy(cordinates[obj]))
            ddllss1.append(torch.from_numpy(dls[obj]))
            crd2.append(crd1[obj].to(device))
            ddllss2.append(ddllss1[obj].to(device))

        qu = Queue()

        #check_memory()
                
        k=0
        for i in range(row):
            for j in range(col):
                X[k] =j*step+area[0]
                Y[k] =i*step+area[1]

                for obj in range(len(dls)):
                    qu.put(("all",k,obj))
                k+=1
        
        qu.put((None,None,None))
        qu.put((None,None,None))

        p1 = Thread(target=MagnetikVoltageTorch, args = ("cpu",Is, crd1, ddllss1, X,Y,hz[0],alfs,qu,H_area))
        p2 = Thread(target=MagnetikVoltageTorch, args = (device,Is, crd2, ddllss2, X,Y,hz[0],alfs,qu,H_area))
        p1.start()
        p2.start()
        p1.join()
        p2.join()

        k = len(crd2)-1
        while k>-1:
            del crd2[k]
            del ddllss2[k]
            k-=1

        #check_memory()

        #torch.cuda.empty_cache()
        H_area = np.linalg.norm(H_area,axis=1)
        return (X,Y), H_area

        
    elif tp == "V_calc_area":
        d = ((area[2]-area[0])**2+(area[3]-area[1])**2)**0.5
        d = f(d,step)
        col = int(d/step)+1

        hz = (f(hz[0],step),f(hz[1],step))
        row = int((hz[1]-hz[0])/step)+1

        H_area = np.zeros(row*col,dtype=np.float64)
        X = np.zeros(row*col,dtype=np.float64)
        Y = np.zeros(row*col,dtype=np.float64)
        Z = np.zeros(row*col,dtype=np.float64)

        
        k=0
        for i in range(row):
            for j in range(col):
                m=step*j/d
                X[k] = (area[0]+area[2]*(m/(1-m)))/(1+(m/(1-m))) if (1-m)!= 0 else area[2]
                Y[k] = (area[1]+area[3]*(m/(1-m)))/(1+(m/(1-m))) if (1-m)!= 0 else area[3]
                Z[k] = i*step+hz[0]
                H_point = np.zeros(3,dtype=np.complex128)
                for obj in range(len(dls)):
                    H_point += MagnetikVoltage(Is[obj],cordinates[obj], dls[obj],X[k],Y[k],Z[k])*alfs[obj]
                H_area[k] = np.linalg.norm(H_point)
                k+=1

        return (X,Y,Z), H_area

        
    elif tp == "O_calc_point":
        H_point = np.zeros(3,dtype=np.complex128)
        for obj in range(len(dls)):
            H_point += MagnetikVoltage(Is[obj],cordinates[obj], dls[obj],area[0],area[1],hz[0])*alfs[obj]
        H_area = np.linalg.norm(H_point)

        return str(round(H_area,2))
    

if __name__ == '__main__':
    #cordinates_1,dl_1 = provod(0,0,  0, 1,0,  0,1000)
    #cordinates_2,dl_2 = provod(0,0.1,0, 1,0.1,0,1000)
    cordinates_1,dl_1 = Solinoid1(0,0,1.33,1.1175,1.115,1400,14,0.024,1)

    #print(MutualInduct(cordinates_1,dl_1,cordinates_2,dl_2))
    print(SameInduct(cordinates_1,dl_1))


    """ tic = time()
    #cordinatesA, dl_A = Solinoid1(0,2,3.461,1.17,1.84,67,2,0.2,1)
    cordinatesB, dl_B = Solinoid1(2,-2,3.461,1.17,1.84,67,2,0.2,1)
    cordinatesC, dl_C = Solinoid1(-2,-2,3.461,1.17,1.84,67,2,0.2,1)

    cordinatesA, dl_A  = Line([[-4,-4,3],[-4,4,4],[4,4,4],[4,-4,3]],0.1,fmax=[2,2,2]) #,fmax=[2,2,2]
    #print(cordinatesA)
    #print(dl_A )


    #mn = -20
    #mx = 20
    stap = 0.1
    #row = int((mx-mn)/stap)

    area = [-5,-5,5,5]
    col = int((area[2]-area[0])/stap)
    row = int((area[3]-area[1])/stap)

    
    H_area = np.zeros(row*col,dtype=np.float64)
    X = np.zeros(row*col,dtype=np.float64)
    Y = np.zeros(row*col,dtype=np.float64)




    k=0
    for i in range(row):#row
        for j in range(col):
            
            X[k] =j*stap+area[0]
            Y[k] =i*stap+area[1]
            H_pointA = MagnetikVoltage(1*1754,cordinatesA, dl_A,X[k],Y[k],1.8)#1.8
            #H_pointB = MagnetikVoltage(1*1754,cordinatesB, dl_B,X[k],Y[k],1.8)
            #H_pointC = MagnetikVoltage(1*1754,cordinatesC, dl_C,X[k],Y[k],1.8)
            H_area[k] = np.linalg.norm(H_pointA)#+H_pointB*alf1+H_pointC*alf2
            k+=1
            #print( X[k], Y[k],k)

    tuc = time()
    print(tuc-tic)
 

    xi, yi = np.linspace(X.min(), X.max(), 100), np.linspace(Y.min(), Y.max(), 100)
    xi, yi = np.meshgrid(xi, yi)

    rbf = scipy.interpolate.Rbf(X, Y, H_area, function='linear')
    zi = rbf(xi, yi)

    plt.imshow(zi, vmin=H_area.min(), vmax=H_area.max(), origin='lower',
            extent=[X.min(), X.max(), Y.min(), Y.max()])
    plt.scatter(X, Y, c=H_area)
    plt.colorbar()

    #  Задаем значение каждого уровня:
    lev = [30,300]

    #  Создаем массив RGB цветов каждого уровня:
    color_line = np.zeros((2, 3))
    color_line[0] = np.array([0,0,1])
    color_line[1] = np.array([1,0,0])

    #  Контуры одного цвета:
    cs = plt.contour(xi, yi, zi, levels = lev,
            colors = color_line)

    countur_date = cs.allsegs
    #print(countur_date)
    plt.clabel(cs)

    plt.show()  """


    """ mn = -5
    mx = 5
    stap = 0.25
    row = int((mx-mn)/stap)
    H_area = np.zeros(row*row,dtype=np.float64)
    X = np.zeros(row*row,dtype=np.float64)
    Y = np.zeros(row*row,dtype=np.float64)

    cordinatesA1, dl_A1 = Solinoid1(-2.059,0,0.9878,0.9638,0.6585,15,2,0.219,1)
    cordinatesB1, dl_B1 = Solinoid1(-2.059,0,1.9207,0.9638,0.6585,15,2,0.219,1)
    cordinatesC1, dl_C1 = Solinoid1(-2.059,0,2.8536,0.9638,0.6585,15,2,0.219,1)

    cordinatesA2, dl_A2 = Solinoid1(2.059,0,0.9878,0.9638,0.6585,15,2,0.219,1)
    cordinatesB2, dl_B2 = Solinoid1(2.059,0,1.9207,0.9638,0.6585,15,2,0.219,1)
    cordinatesC2, dl_C2 = Solinoid1(2.059,0,2.8536,0.9638,0.6585,15,2,0.219,1)
    k=0
    for i in range(row):#row
        for j in range(row):
            #print(k)
            X[k] =i*stap+mn
            Y[k] =j*stap+mn
            H_pointA1 = MagnetikVoltage(24100,cordinatesA1, dl_A1,X[k],Y[k],4.5)#24100№1500
            H_pointB1 = MagnetikVoltage(24100,cordinatesB1, dl_B1,X[k],Y[k],4.5)
            H_pointC1 = MagnetikVoltage(24100,cordinatesC1, dl_C1,X[k],Y[k],4.5)

            H_pointA2 = MagnetikVoltage(18200,cordinatesA2, dl_A2,X[k],Y[k],4.5)#18200№1500
            H_pointB2 = MagnetikVoltage(18200,cordinatesB2, dl_B2,X[k],Y[k],4.5)
            H_pointC2 = MagnetikVoltage(18200,cordinatesC2, dl_C2,X[k],Y[k],4.5)

            H_area[k] = np.linalg.norm(H_pointA1+H_pointA2+H_pointB1*alf1+H_pointB2*alf1+H_pointC1*alf2+H_pointC2*alf2)

            k+=1


    xi, yi = np.linspace(X.min(), X.max(), 100), np.linspace(Y.min(), Y.max(), 100)
    xi, yi = np.meshgrid(xi, yi)

    rbf = scipy.interpolate.Rbf(X, Y, H_area, function='linear')
    zi = rbf(xi, yi)

    plt.imshow(zi, vmin=H_area.min(), vmax=H_area.max(), origin='lower',
            extent=[X.min(), X.max(), Y.min(), Y.max()])
    plt.scatter(X, Y, c=H_area)
    plt.colorbar()

    plt.show()  """

    """ cordinatesA1, dl_A1 = Solinoid1(-2.059,0,0.9878,0.9638,0.6585,15,2,0.219,1)
    cordinatesB1, dl_B1 = Solinoid1(-2.059,0,1.9207,0.9638,0.6585,15,2,0.219,1)
    cordinatesC1, dl_C1 = Solinoid1(2.059,0,0.9878,0.9638,0.6585,15,2,0.219,1)

    H_pointA1 = MagnetikVoltage(1,cordinatesA1, dl_A1,5.291,0.8737,4.5)#31400
    H_pointB1 = MagnetikVoltage(27193.2,cordinatesB1, dl_B1,5.291,0.8737,4.5)#27193.2
    H_pointC1 = MagnetikVoltage(27193.2,cordinatesC1, dl_C1,5.291,0.8737,4.5)#3637


    H_area = np.linalg.norm(H_pointA1*1+H_pointB1*alf3+H_pointC1*alf4)

    print(H_area) """