from gputreads import Paralel_Calc, distribution_memory
import numpy as np
import torch
import scipy.interpolate
from scipy.optimize import fsolve,broyden1
from make_graph import getGraph, setTextPos

from time import time, sleep





alf1=np.cos(240*np.pi/180)+1j*np.sin(240*np.pi/180)
alf2=np.cos(120*np.pi/180)+1j*np.sin(120*np.pi/180)

alf3=np.cos(0*np.pi/180)+1j*np.sin(0*np.pi/180)
alf4=np.cos(180*np.pi/180)+1j*np.sin(180*np.pi/180)

numbers_type = (torch.float32,np.float32,np.complex64)

def setTypes(t):
    global numbers_type
    if t == 'float32':
        numbers_type = (torch.float32,np.float32,np.complex64)
    elif t == 'float64':
        numbers_type = (torch.float64,np.float64,np.complex128)

def cuda_available():
    return torch.cuda.is_available()

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
    cordinates = np.zeros((t,3),dtype=numbers_type[1])
    dl = np.zeros((t-1,3),dtype=numbers_type[1])

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


def Solinoid1Torch(x,y,z,r,h,n,m,l,dalf,dp=None):
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

    arr_type = torch.float32

    cordinates = torch.zeros(t,3,dtype=numbers_type[0])
    dl = torch.zeros(t-1,3,dtype=numbers_type[0])

    if dp is not None:
        cordinates_2 = torch.zeros(t,3,dtype=numbers_type[0])
        dl_2 = torch.zeros(t-1,3,dtype=numbers_type[0])

    t_arr_v = torch.arange(0,tvr,1,dtype=numbers_type[0]) 

    k=0
    for i in range(m):
        t_arr = torch.arange(0,ti[i],1,dtype=numbers_type[0])

        if dp is None:
            cordinates[k:k+ti[i],0] = ri[i]*torch.cos(2*np.pi*t_arr*ns[i]/(ti[i]-1)) + x
            cordinates[k:k+ti[i],1] = ri[i]*torch.sin(2*np.pi*t_arr*ns[i]/(ti[i]-1)) + y
            cordinates[k:k+ti[i],2] = h*t_arr/(ti[i]-1) + z
        else:
            cordinates[k:k+ti[i],0] = (ri[i]-dp/2)*torch.cos(2*np.pi*t_arr*ns[i]/(ti[i]-1)) + x
            cordinates[k:k+ti[i],1] = (ri[i]-dp/2)*torch.sin(2*np.pi*t_arr*ns[i]/(ti[i]-1)) + y
            cordinates[k:k+ti[i],2] = h*t_arr/(ti[i]-1) + z

            cordinates_2[k:k+ti[i],0] = (ri[i]+dp/2)*torch.cos(2*np.pi*t_arr*ns[i]/(ti[i]-1)) + x
            cordinates_2[k:k+ti[i],1] = (ri[i]+dp/2)*torch.sin(2*np.pi*t_arr*ns[i]/(ti[i]-1)) + y
            cordinates_2[k:k+ti[i],2] = h*t_arr/(ti[i]-1) + z

        k += ti[i]

        if i != m-1:
            xpr = cordinates[k-1][0]-l/2
            ypr = cordinates[k-1][1]
            if dp is None:
                cordinates[k:k+tvr,0] = xpr
                cordinates[k:k+tvr,1] = ypr
                cordinates[k:k+tvr,2] = h*(1-t_arr_v/(tvr-1)) + z
            else:
                cordinates[k:k+tvr,0] = xpr-dp/2
                cordinates[k:k+tvr,1] = ypr
                cordinates[k:k+tvr,2] = h*(1-t_arr_v/(tvr-1)) + z

                cordinates_2[k:k+tvr,0] = xpr+dp/2
                cordinates_2[k:k+tvr,1] = ypr
                cordinates_2[k:k+tvr,2] = h*(1-t_arr_v/(tvr-1)) + z

            k += tvr
    
    dl = cordinates[1:k,:] - cordinates[0:k-1,:]
    #.numpy()
    if dp is None:
        return cordinates, dl
    else:
        dl_2 = cordinates_2[1:k,:] - cordinates_2[0:k-1,:]
        return cordinates, dl, cordinates_2, dl_2
    

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
    cordinates = np.zeros((t,3),dtype=numbers_type[1])
    dl = np.zeros((t-1,3),dtype=numbers_type[1])
    
    for i in range(t):
        cordinates[i][0] = r*np.cos(2*np.pi*i*n/t)+x
        cordinates[i][1] = r*np.sin(2*np.pi*i*n/t)+y
        cordinates[i][2] = h*i/t + z
        if i>=1:
            dl[i-1] = cordinates[i:i+1,:]-cordinates[i-1:i,:]

    return cordinates, dl

def SolinoidTorch(x,y,z,r,h,n,t):
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
    
    cordinates = torch.zeros(t,3,dtype=numbers_type[0])
    dl = torch.zeros(t-1,3,dtype=numbers_type[0])

    t_arr = torch.arange(0,t,1,dtype=numbers_type[0])
    cordinates[:,0] = r*torch.cos(2*np.pi*t_arr*n/t) + x
    cordinates[:,1] = r*torch.sin(2*np.pi*t_arr*n/t) + y
    cordinates[:,2] = h*t_arr/t + z

    dl = cordinates[1:t,:] - cordinates[0:t-1,:]
    #.numpy()
    return cordinates, dl


def equations(a,x,y):
    return (a[0]+a[1]*x[0]+a[2]*x[0]**2-y[0],
            a[0]+a[1]*x[1]+a[2]*x[1]**2-y[1],
            a[0]+a[1]*x[2]+a[2]*x[2]**2-y[2])


def Parab(p1,p2,p3):
    f = lambda a: equations(a,(p1[0],p2[0],p3[0]),(p1[1],p2[1],p3[1]))
    a = fsolve(f, (1, 1, 1))
    return lambda x: a[0]+a[1]*x+a[2]*x**2


def Line(points, fmax = None, DL = 0.01):
    dist = [((points[i][0]-points[i-1][0])**2+\
            (points[i][1]-points[i-1][1])**2+\
            (points[i][2]-points[i-1][2])**2)**0.5 for i in range(1,len(points))]

    st = [int(i/DL) for i in dist]

    t = sum(st)+1
    cordinates = torch.zeros(t,3,dtype=numbers_type[0])
    dl = torch.zeros(t-1,3,dtype=numbers_type[0])

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

    #return torch.from_numpy(cordinates), torch.from_numpy(dl)
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
    point = np.array([x,y,z],dtype=numbers_type[1])
    rv = (point - cordinates)[:t,:]
    r = 1/(4*np.pi*np.linalg.norm(rv,axis=1)**3)
    r.shape = (t,1)
    dH = np.cross(dl, rv)*r
    rez = np.sum(dH,axis=0)*I
    return np.array([rez[0] if not np.isnan(rez[0]) else I,\
                    rez[1] if not np.isnan(rez[1]) else I,\
                    rez[2] if not np.isnan(rez[2]) else I,],dtype=numbers_type[1])


def MagnetikVoltageNumpy(cordinates,dl,x,y,z,alfs,I,dtype,trig,k,obj,device):
    #print(k,obj)
    t = np.shape(dl[obj])[0]
    point = np.array([x[k],y[k],z[k] if trig else z],dtype=numbers_type[1])
    rv = (point - cordinates[obj])[:t,:]
    #print(np.min(np.linalg.norm(rv,axis=1)))
    r = 1/(4*np.pi*np.linalg.norm(rv,axis=1)**3)
    r.shape = (t,1)
    dH = np.cross(dl[obj], rv)*r
    rez = np.sum(dH,axis=0)*I[obj]
    return np.array([rez[0] if not np.isnan(rez[0]) else I,\
                    rez[1] if not np.isnan(rez[1]) else I,\
                    rez[2] if not np.isnan(rez[2]) else I,],dtype=numbers_type[1])*alfs[obj]

                


def MagnetikVoltageTorch(cordinates,dl,x,y,z,alfs,I,dtype,trig,k,obj,device):
    """
    Расчёт напряжённости от одного проводника\n
    cordinates - координаты элементрных участков проводника\n
    dl - длинна элементарных участков\n
    x,y,z - координаты точки в которой определяем напряжённость поля\n
    alfs - фаза тока в расматриваемом проводнике\n
    I - ток в расматриваем проводнике\n
    trig - изменение по координате Z\n
    k - индекс точки в пространстве\n
    obj - индекс обьекта\n
    device - устройсто для вычислений
    """
    #print(cordinates[obj].device)
    t = dl[obj].size()[0]
    point = torch.tensor([x[k],y[k],z[k] if trig else z],dtype=dtype,device=device) #device
    rv = (point - cordinates[obj])[:t,:]
    r = 1/(4*np.pi*torch.norm(rv,dim=1)**3)
    r = torch.reshape(r, (t,1))
    dH = torch.cross(dl[obj], rv)*r
    rez = torch.sum(dH,dim=0)*I[obj]
    trig = torch.isnan(rez)
    rt = torch.tensor([rez[0] if not trig[0] else I,\
                        rez[1] if not trig[1] else I,\
                        rez[2] if not trig[2] else I,],dtype=dtype).numpy()*alfs[obj]

    return rt



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

def MutualInductTorch(tensor_list):
    """
    Расчёт взаимной индукции между двумя произвольно расположенными проводниками\n
     
    """
    if tensor_list[3].size()[0]<tensor_list[1].size()[0]:
        dl_1, dl_2 = tensor_list[1][1:-1,:],tensor_list[3][1:-1,:]
        t_1 = dl_1.size()[0]
        t_2 = dl_2.size()[0]
        
        Cordinates_1 = tensor_list[0][1:-2:]
        Cordinates_2 = tensor_list[2][1:-2,:]

    else:
        dl_1, dl_2 = tensor_list[3][1:-1,:],tensor_list[1][1:-1,:]
        t_1 = dl_1.size()[0]
        t_2 = dl_2.size()[0]
        
        Cordinates_1 = tensor_list[2][1:-2,:]
        Cordinates_2 = tensor_list[0][1:-2,:]

    M = 0

    for i in range(t_2):
        M += torch.sum(torch.sum(dl_1*dl_2[i,:],1)/torch.norm(Cordinates_1-Cordinates_2[i,:],dim=1))    
 
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
        r3 = np.sum(dl*dl[i,:],axis=1)
        M += np.sum(r3*r) 

    

    return (M+np.sum(np.linalg.norm(dl))/2*mu) *10**-7

def SameInductTorch(tensor_list,mu=1):
    """
    Расчёт собственной индукции м проводника\n
     
    """
    dl_1, dl_2 = tensor_list[1], tensor_list[3]
    t = dl_1.size()[0]
    Cordinates_1, Cordinates_2 = tensor_list[0][:t,:], tensor_list[2][0:t,:]

    #dr = torch.sum(dl,0)/t

    #own = torch.zeros(t,3,dtype=torch.float32,device = dl.device)
    M = 0
    for i in range(t):
        #own[i,:]+=dr
        #(Cordinates_1+Cordinates_2-Cordinates_1[i,:]-Cordinates_2[i,:]+own)/2
        M += torch.sum(torch.sum(dl_1*dl_2[i,:],1)/torch.norm(Cordinates_1-Cordinates_2[i,:],dim=1))
        #own[i,:]-=dr

    print(M*10**-7)
    print(torch.sum(torch.norm(dl_1))/2*mu*10**-7)
    return (M+torch.sum(torch.norm(dl_1))/2*mu) *10**-7

def provod(xn,yn,zn,xk,yk,zk,t):
    dx = (xk-xn)/(t-1)
    dy = (yk-yn)/(t-1)
    dz = (zk-zn)/(t-1)

    cordinates = np.zeros((t,3),dtype=numbers_type[1])
    dl = np.zeros((t-1,3),dtype=numbers_type[1])

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

def point_calc(sourses,areas, deg, DL, dxf=False):
    alfs, cordinates, dls,Is = [], [], [], []
    for i in sourses:
        if i[0] == "reactor":
            args, m, alf, I = i[1:]
            if m == 1:
                cordinate, dl = SolinoidTorch(*args,deg)
            elif m>1:
                cordinate, dl = Solinoid1Torch(*args,deg)
        elif i[0] == "conductor":
            args, alf, I = i[1:]
            cordinate, dl = Line(*args, DL=DL)
            
        alfs.append(alf)
        cordinates.append(cordinate)
        dls.append(dl)
        Is.append(I)

    if not dxf:
        for data in areas:
            r = 0
            (x, y), z = data.read_data()[1:-1]
            for j in range(len(alfs)):
                r += MagnetikVoltageTorch(cordinates,dls,[x],[y],z[0],alfs,Is,numbers_type[0],False,0,j,'cpu')

            data.result.setNumber(np.linalg.norm(r))
    else:
        rez = []
        for data in areas:
            r = 0
            (x, y), z = data[1:-1]
            for j in range(len(alfs)):
                r += MagnetikVoltageTorch(cordinates,dls,[x],[y],z[0],alfs,Is,numbers_type[0],False,0,j,'cpu')

            rez.append((x,y,z,str(round(np.linalg.norm(r),2))))
        return rez

        
def run_area_calc(sourses, area, deg, DL, callback_func = None):
    cordinates = []
    dls = []
    alfs = []
    Is = []

    tp, area, hz, step = area

    try:
        for i in sourses:
            if i[0] == "reactor":
                args, m, alf, I = i[1:]
                if m == 1:
                    cordinate, dl = SolinoidTorch(*args,deg)
                elif m>1:
                    cordinate, dl = Solinoid1Torch(*args,deg)
            elif i[0] == "conductor":
                args, alf, I = i[1:]
                #print(args, alf, I)
                cordinate, dl = Line(*args, DL=DL)
                #print(cordinate, dl)
                
            alfs.append(alf)
            cordinates.append(cordinate)
            dls.append(dl)
            Is.append(I)

        f = lambda x,y: (x//y+(1 if x>=0 else 0))*y if x%y!=0 else x

        if tp == "horizontal_area":   
            area = [f(i,step) for i in area]
            col = int((area[2]-area[0])/step)+1
            row = int((area[3]-area[1])/step)+1

            H_area = np.zeros((row*col,3),dtype=numbers_type[2])
            XY = np.zeros((2,row*col),dtype=numbers_type[1])

                    
            k=0
            for i in range(row):
                for j in range(col):
                    XY[0][k]=j*step+area[0]
                    XY[1][k] =i*step+area[1]
                    k+=1
            
            cb = [lambda: callback_func[0](XY,H_area),callback_func[1],callback_func[2]] if callback_func is not None else None
            PC = Paralel_Calc([cordinates, dls],[XY[0,:],XY[1,:],hz[0],alfs,Is,numbers_type[0],False],k,2.4,H_area, MagnetikVoltageTorch, cb)

            
            if callback_func is None:
                PC.start(join=True)
                return XY, H_area

            else:
                PC.start()

            
        elif tp == "vertical_area":
            d = ((area[2]-area[0])**2+(area[3]-area[1])**2)**0.5
            d = f(d,step)
            col = int(d/step)+1

            hz = (f(hz[0],step),f(hz[1],step))
            row = int((hz[1]-hz[0])/step)+1

            H_area = np.zeros((row*col,3),dtype=numbers_type[2])
            XYZ = np.zeros((3,row*col),dtype=numbers_type[1])

        
            k=0
            for i in range(row):
                for j in range(col):
                    m=step*j/d
                    XYZ[0][k]=(area[0]+area[2]*(m/(1-m)))/(1+(m/(1-m))) if (1-m)!= 0 else area[2]
                    XYZ[1][k] =(area[1]+area[3]*(m/(1-m)))/(1+(m/(1-m))) if (1-m)!= 0 else area[3]
                    XYZ[2][k] =i*step+hz[0]
                    k+=1
            
            cb =  [lambda: callback_func[0](XYZ,H_area),callback_func[1],callback_func[2]] if callback_func is not None else None
            PC = Paralel_Calc([cordinates, dls],[XYZ[0,:],XYZ[1,:],XYZ[2,:],alfs,Is,numbers_type[0],True],k,2.4,H_area, MagnetikVoltageTorch, cb)

            if callback_func is None:
                PC.start(join=True)
                return XYZ, H_area

            else:
                PC.start()

    except Exception as ex:
        print("run_area_calc",ex)
        
    """ elif tp == "O_calc_point":
        H_point = np.zeros(3,dtype=np.complex128)
        for obj in range(len(dls)):
            H_point += MagnetikVoltage(Is[obj],cordinates[obj], dls[obj],area[0],area[1],hz[0])*alfs[obj]
        H_area = np.linalg.norm(H_point)

        return str(round(H_area,2)) """

def excelData(Lines,R,L,dm,mt,Ir,Is,As,A0,Source_M,Rec_M):
    r,s = len(Lines), np.shape(Is)[0]

    Data = {}
    title = ["х1,м","у1,м","z1,м","х2,м","у2,м","z2,м","Ir,А","alf,град","d, мм","mt","R,Ом","L,Гн","Source_M,Гн"]
    for i in range(len(title)):
        Data[(0,i)] = title[i]

    for i in range(r):
        Data[(i+1,0)] = Lines[i][0][0]
        Data[(i+1,1)] = Lines[i][0][1]
        Data[(i+1,2)] = Lines[i][0][2]

        Data[(i+1,3)] = Lines[i][1][0]
        Data[(i+1,4)] = Lines[i][1][1]
        Data[(i+1,5)] = Lines[i][1][2]

        Data[(i+1,6)] = np.abs(Ir[i])
        Data[(i+1,7)] = np.angle(Ir[i],deg=True)

        Data[(i+1,8)] = dm[i]
        Data[(i+1,9)] = mt[i]

        Data[(i+1,10)] = R[i]
        Data[(i+1,11)] = L[i]

    for i in range(r):
        for j in range(s):
            Data[(i+1,j+13)] = np.real(Source_M[i][j])

    Data[(r+1,12)] = "Is,А"
    Data[(r+2,12)] = "alf,град"
    for j in range(s):
        Data[(r+1,j+13)] = np.abs(Is[j])
        Data[(r+2,j+13)] = np.angle(As[j],deg=True)

    n = 13+s
    Data[(0,n)] = "Rec_M,Гн"
    for i in range(r):
        for j in range(r):
            Data[(i+1,j+n+1)] = np.real(Rec_M[i][j])

    Data[(r+1,0)] = "А0"
    for i in range(np.shape(A0)[0]):
        for j in range(np.shape(A0)[1]):
            Data[(r+2+i,j)] = A0[i][j]

    return Data


def get_colors(arr,lim,cmap,norm):
    n = norm(vmin=lim[0], vmax=lim[1])
    return [cmap(n(i),bytes=True) for i in arr]


def receivers_calc(sousces, receivers, DL, da, MutualCashe, excel=False):
    pls, diam, materials = [],[],[]

    for pl in receivers:
        pls.append(pl[1][0])
        diam.append(pl[1][1])
        materials.append(pl[1][2])

    A0, Lines, R, L, _dm, _mt = getGraph(pls, diam, materials)

    S_alfs, S_cordinates, S_dls, S_Is = [],[],[],[]

    for i in sousces:
        if i[0] == "reactor":
            args, m, alf, I = i[1:]
            if m == 1:
                cordinate, dl = SolinoidTorch(*args,da)
            elif m>1:
                cordinate, dl = Solinoid1Torch(*args,da)
        elif i[0] == "conductor":
            args, alf, I = i[1:]
            cordinate, dl = Line(*args, DL=DL)
            
        S_alfs.append(alf)
        S_cordinates.append(cordinate)
        S_dls.append(dl)
        S_Is.append(I)

    R_cordinates, R_dls = [],[]
    for i in Lines:
        cordinate, dl = Line(i, DL=DL)
        R_cordinates.append(cordinate)
        R_dls.append(dl)
    r, s = len(R_dls), len(S_dls)
    Source_M = np.zeros((r,s),dtype=numbers_type[2])
    M = np.zeros((r,r),dtype=numbers_type[2])
    Zd = np.zeros(r,dtype=numbers_type[2])
    
    
    #free_mmr = distribution_memory([S_cordinates+R_cordinates,S_dls+R_dls],coef=2.3)
    #print(free_mmr)
    device = torch.cuda.current_device()
    S_cordinates = [i.to(device) for i in S_cordinates]
    R_cordinates = [i.to(device) for i in R_cordinates]

    S_dls = [i.to(device) for i in S_dls]
    R_dls = [i.to(device) for i in R_dls]
    #tensors_list_gpu[j][i] = self.tensors_list[j][i].to(device)

    t1 = time()
    for i in range(r):
        for j in range(s):
            key = (sousces[j][0:2], Lines[i], (DL,da))
            if key not in MutualCashe:
                rez = float(MutualInductTorch([R_cordinates[i],R_dls[i],S_cordinates[j],S_dls[j]]))
                MutualCashe[key] = rez
            else:
                rez = MutualCashe[key]

            Source_M[i][j] = rez


    t2 = time()
    print(t2-t1)
    t1 = time()
    for i in range(r):
        for j in range(i,r):
            if i==j: 
                Zd[i] = R[i]+ 1j*L[i]*2*np.pi*50
            else:
                key1 = (Lines[i], Lines[j], (DL,da))
                key2 = (Lines[j], Lines[i], (DL,da))
                if key1 in MutualCashe:
                    rez = MutualCashe[key1]
                elif key2 in MutualCashe:
                    rez = MutualCashe[key2]
                else:
                    rez = float(MutualInductTorch([R_cordinates[i],R_dls[i],R_cordinates[j],R_dls[j]]))
                    MutualCashe[key1] = rez

                M[i][j] = rez
                M[j][i] = rez


    t2 = time()
    print(t2-t1)
    I = np.array(S_Is,dtype=numbers_type[2])
    Alf = np.array(S_alfs,dtype=numbers_type[2])
    E = np.dot(Source_M*1j*2*np.pi*50,I*Alf)
    
    #dZ = np.diag(np.diagonal(Z))
    dZ = np.diag(Zd)
    W = M*1j*2*np.pi*50
    Z = W+dZ
    #W = Z-dZ
    A = A0[:-1,:]
    At = A.transpose()
    dY=np.linalg.inv(dZ)
    Yy=np.dot(np.dot(A,dY),At)
    J=np.dot(np.dot(A,dY),E)
    JE=np.hstack([J, E])
    KI=np.dot(A,np.dot(W,dY).transpose())
    YZ=np.vstack([np.hstack([Yy, KI]), np.hstack([At, Z])])
    H=np.linalg.solve(YZ,JE)
    
    Id = np.abs(H[-r:])

    data = excelData(Lines,R,L,_dm,_mt,H[-r:],I,Alf,A0,Source_M,M)
    if excel:
        return Id, Lines, setTextPos, get_colors, data
    else:
        return Id, Lines, setTextPos, get_colors


        

if __name__ == '__main__':
    #cordinates_1,dl_1 = provod(0,0,  0, 1,0,  0,1000)
    #print(SameInduct(cordinates_1,dl_1))
    #cordinates_2,dl_2 = provod(0,0.1,0, 1,0.1,0,1000)
    #cordinates_1,dl_1 = Solinoid1Torch(0,0,0,1,0.001,1,1,0,0.1)
    #cordinates_2,dl_2 = Solinoid1Torch(0,0,1,1,0.001,1,1,0,0.1)
    #cordinates_1,dl_1 = Solinoid1Torch(0,0,1.33,1.1175,1.115,1400,14,0.024,1)

    """ cordinates_1,dl_1 = Solinoid1Torch(0,0,0,1,0.001,1,1,0,0.1)
    cordinates_2,dl_2 = Solinoid1Torch(0,0,1,1,0.001,1,1,0,0.1)
    cordinates_1 = torch.from_numpy(cordinates_1).to(0)
    dl_1 = torch.from_numpy(dl_1).to(0)
    cordinates_2 = torch.from_numpy(cordinates_2).to(0)
    dl_2 = torch.from_numpy(dl_2).to(0)
    print(MutualInductTorch([cordinates_1,dl_1,cordinates_2,dl_2])) """

    cordinates_1,dl_1,cordinates_2,dl_2 = Solinoid1Torch(0,0,1.33,1.1175,1.115,1400,14,0.024,1,dp=0.01)
    #cordinates_1,dl_1,cordinates_2,dl_2 = Solinoid1Torch(0,0,0,1,0.001,1,1,0,0.1,dp=0.01)
    cordinates_1 = torch.from_numpy(cordinates_1).to(0)
    dl_1 = torch.from_numpy(dl_1).to(0)
    cordinates_2 = torch.from_numpy(cordinates_2).to(0)
    dl_2 = torch.from_numpy(dl_2).to(0)
    print(SameInductTorch([cordinates_1,dl_1,cordinates_2,dl_2]))


    