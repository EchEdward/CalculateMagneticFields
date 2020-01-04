import numpy as np
import torch
from threading import Thread, Event
from queue import Queue, LifoQueue
from time import time
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
import scipy.interpolate
from scipy.optimize import fsolve,broyden1
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo
import sys

def Cuda_Memory_Control():
    # Check how cuda do control memory
    try:
        nvmlInit()
        device = torch.cuda.current_device()
        h = nvmlDeviceGetHandleByIndex(0)
        info_1 = nvmlDeviceGetMemoryInfo(h)

        t = torch.ones(1,dtype=torch.float32,device=device)
        t_size_2 = torch.cuda.memory_allocated(device)
        reserv_mr_2 = torch.cuda.memory_cached(device)

        info_2 = nvmlDeviceGetMemoryInfo(h)

        del t

        t_size_3 = torch.cuda.memory_allocated(device)
        reserv_mr_3 = torch.cuda.memory_cached(device)
        info_3 = nvmlDeviceGetMemoryInfo(h)

        const_memory = info_1.free - info_2.free - t_size_2 - reserv_mr_2
        check_free_memory = info_3.free - info_2.free #- reserv_mr_3 - t_size_3

        if check_free_memory*0.95 <= const_memory <= check_free_memory*1.05:
            # Memory will clear after finish calculate
            result = (const_memory, False)
        else:
            # Memory won't clear after finish calculate
            result = (const_memory, True)

    except Exception:
        # Other problem when you can't use cuda
        result = (0, None)

    return result

cuda_memory_control = Cuda_Memory_Control()


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

def distribution_memory(arr,start=0,coef=1):
    device = torch.cuda.current_device()
    h = nvmlDeviceGetHandleByIndex(0)
    info = nvmlDeviceGetMemoryInfo(h)

    busy_memory = torch.cuda.memory_allocated(device)
    reserv_memory = torch.cuda.memory_cached(device)

    free_memory = info.free + reserv_memory - busy_memory

    if cuda_memory_control[1] is not None  and not cuda_memory_control[1]:
        free_memory-=cuda_memory_control[1]

    #free_memory -= 220/1024**2
   
    Trig = []
    stp = []
    used_memory = 0

    cols = len(arr)
    rows = len(arr[0])

    for i in range(start,rows):
        for j in range(cols):
            if type(arr[j][i]) == np.ndarray:
                used_memory += arr[j][i].nbytes
            elif type(arr[j][i]) == torch.Tensor:
                used_memory += arr[j][i].numpy().nbytes #sys.getsizeof(arr[j][i].storage())
        if i == start:
            used_memory *= coef
        Trig.append(free_memory > used_memory)
        stp.append(used_memory/1024**2)
                
    print("free memory: ",(free_memory)/1024**2)
    print(Trig)
    print(stp)

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

    cordinates = torch.zeros(t,3,dtype=arr_type)
    dl = torch.zeros(t-1,3,dtype=arr_type)

    if dp is not None:
        cordinates_2 = torch.zeros(t,3,dtype=arr_type)
        dl_2 = torch.zeros(t-1,3,dtype=arr_type)

    t_arr_v = torch.arange(0,tvr,1,dtype=arr_type) 

    k=0
    for i in range(m):
        t_arr = torch.arange(0,ti[i],1,dtype=arr_type)

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
    if dp is None:
        return cordinates.numpy(), dl.numpy()
    else:
        dl_2 = cordinates_2[1:k,:] - cordinates_2[0:k-1,:]
        return cordinates.numpy(), dl.numpy(), cordinates_2.numpy(), dl_2.numpy()
    

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
    
    cordinates = torch.zeros(t,3,dtype=torch.float32)
    dl = torch.zeros(t-1,3,dtype=torch.float32)

    t_arr = torch.arange(0,t,1,dtype=torch.float32)
    cordinates[:,0] = r*torch.cos(2*np.pi*t_arr*n/t) + x
    cordinates[:,1] = r*torch.sin(2*np.pi*t_arr*n/t) + y
    cordinates[:,2] = h*t_arr/t + z

    dl = cordinates[1:t,:] - cordinates[0:t-1,:]
    
    return cordinates.numpy(), dl.numpy()


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


class Thread_Calc(Thread):
    def __init__(self,tsk_for,tensors_list,common_list,queue_list,coef_mmr,Result,Feedback = None):
        Thread.__init__(self)
        self.tsk_for = tsk_for
        self.qu_cpu, self.qu_gpu, self.number_of_tasks = queue_list
        self.tensors_list, self.common_list = tensors_list, common_list
        self.coef_mmr = coef_mmr
        self.Result = Result
        self.call = False
        if Feedback is not None:
            self.call = True
            self.back = Feedback[0]
            self.message_widget = Feedback[1]

        self.event = Event()
        #print(self.event)
    
    def run(self):
        if self.tsk_for == "cpu":
            self.cpu_start()
        elif self.tsk_for == "gpu":
            self.gpu_start()

    def stop(self):       
        self.event.set()

    def cpu_start(self):
        cpu_start = False
        while not self.event.is_set():
            task_Trig, k, obj = self.qu_cpu.get()

            if task_Trig == "End" and cpu_start:
                if self.call:
                    self.back("cpu")
                break

            elif task_Trig == "Cancel" and cpu_start:
                break

            elif task_Trig == "Work" and cpu_start:
                self.Result[k,:] += MagnetikVoltageTorch(self.tensors_list,self.common_list,k,obj,"cpu")
                if self.call:
                    self.message_widget.setValue(number_task-(self.qu_gpu.qsize()+self.qu_cpu.qsize()))

            elif task_Trig == "Start":
                cpu_start = True
                if self.call:
                    number_task = self.qu_gpu.qsize() + self.qu_cpu.qsize()

            else:
                self.qu_cpu.put((task_Trig, k, obj))

    def gpu_start(self):
        while not self.event.is_set():
            task_Trig, k, obj = self.qu_gpu.get()
            if task_Trig == "Start":
                if torch.cuda.is_available():
                    device = torch.cuda.current_device()
                    free_mmr = distribution_memory(self.tensors_list,coef=self.coef_mmr)

                    objs = len(free_mmr)
                    tensors_list_gpu = [[None for i in range(objs)] for j in range(len(self.tensors_list))]
                    re = -1

                    for i in range(objs):
                        re += 1
                        if free_mmr[i]:
                            for j in range(len(self.tensors_list)):
                                tensors_list_gpu[j][i] = self.tensors_list[j][i].to(device)
                        else:
                            break
                    else:
                        re+=1

                    if re == objs:
                        self.qu_gpu.put(("End",None,None))
                        self.qu_cpu.put(("End",None,None))
                        self.qu_cpu.put(("Start",None,None))

                        for i in range(self.number_of_tasks):
                            for j in range(objs):
                                self.qu_gpu.put(("Work",i,j))
                    
                    elif re == 0:
                        self.qu_gpu.put(("End",None,None))
                        self.qu_cpu.put(("End",None,None))

                        for i in range(self.number_of_tasks):
                            for j in range(objs):
                                self.qu_cpu.put(("Work",i,j))
                        
                        self.qu_cpu.put(("Start",None,None))

                    elif 0 < re < objs:
                        self.qu_gpu.put(("Rewrite",None,None))
                        #qu_cpu.put(("End",None,None))

                        for i in range(self.number_of_tasks):
                            for j in range(objs):
                                if j < re:
                                    self.qu_gpu.put(("Work",i,j))
                                else:
                                    self.qu_cpu.put(("Work",i,j))

                        self.qu_cpu.put(("Start",None,None))


                else:
                    self.qu_gpu.put(("End",None,None))
                    self.qu_cpu.put(("End",None,None))

                    for i in range(self.number_of_tasks):
                        for j in range(objs):
                            self.qu_cpu.put(("Work",i,j))

                    self.qu_cpu.put(("Start",None,None))
                
                if self.call:
                    number_task = self.qu_gpu.qsize()+self.qu_cpu.qsize()
                    self.message_widget.setRange(0, number_task)
                

            if task_Trig == "Rewrite":
                tensors_list_gpu = [[None for i in range(objs)] for j in range(len(self.tensors_list))]

                free_mmr = distribution_memory(self.tensors_list,start=re, coef=self.coef_mmr)

                start = re
                re -= 1
                
                for i in range(start,objs):
                    re += 1
                    if free_mmr[i-start]:
                        for j in range(len(self.tensors_list)):
                            tensors_list_gpu[j][i] = self.tensors_list[j][i].to(device)
                    else:
                        break
                else:
                    re+=1

                tasks = []

                if re <= objs:
                    if self.qu_cpu.qsize() != 0:
                        while True:
                            g = self.qu_cpu.get()
                            if g[0] == "End":
                                break
                            tasks.append(g)

                        if re == objs:
                            self.qu_gpu.put(("End",None,None))
                            self.qu_cpu.put(("End",None,None))

                            for i in tasks:
                                self.qu_gpu.put(i)
                        else:
                            self.qu_gpu.put(("Rewrite",None,None))
                            self.qu_cpu.put(("End",None,None))

                            for i in tasks:
                                if i[2]>=re:
                                    self.qu_cpu.put(i)
                                else:
                                    self.qu_cpu.put(i)
                    else:
                        self.qu_gpu.put(("End",None,None))
                    
            elif task_Trig == "End" :
                if self.call:
                    self.back("gpu")
                break
            
            elif task_Trig == "Cancel" :
                break

            elif task_Trig == "Work":
                if self.call:
                    self.message_widget.setValue(number_task-(self.qu_gpu.qsize()+self.qu_cpu.qsize()))
                    self.Result[k,:] += MagnetikVoltageTorch(tensors_list_gpu,self.common_list,k,obj,device)
   



class Paralel_Calc():
    def __init__(self,tensors_list,common_list,tasks,coef_mmr,Result,Feedback = None):
        self.tensors_list, self.common_list = tensors_list, common_list
        self.coef_mmr = coef_mmr
        self.Result = Result
        self.tasks = tasks
        self.qu_cpu = LifoQueue()
        self.qu_gpu = LifoQueue()
        self.qu_gpu.put(("Start",None,None))

        if Feedback is not None:
            self.Feedback = [self.call_back(Feedback),Feedback[1]]
            self.Feedback[1].canceled.connect(lambda: self.stop())


    def start(self, join=False):
        self.p1 = Thread_Calc("cpu", self.tensors_list, self.common_list,[self.qu_cpu, self.qu_gpu, self.tasks], self.coef_mmr, self.Result,self.Feedback)
        self.p2 = Thread_Calc("gpu", self.tensors_list, self.common_list,[self.qu_cpu, self.qu_gpu, self.tasks], self.coef_mmr, self.Result,self.Feedback)
        self.p1.start()
        self.p2.start()
        if join:
            self.p1.join()
            self.p2.join() 

        print("start")

    def stop(self):
        print("end0")
        self.p1.stop()
        print("end1")
        self.p2.stop()
        print("end2")

    def call_back(self,call_func,cpu = False, gpu = False):
        """ Вызов функции по завершению расчёта """
        def Call(device):
            nonlocal cpu, gpu, call_func
            if device == "cpu":
                cpu = True
            if device == "gpu":
                gpu = True
            if cpu and gpu:
                call_func[1].reset()
                call_func[0]()
        return Call
                


def MagnetikVoltageTorch(tensor_list,common_list,k,obj,device):
    x,y,z,alfs,I,trig = common_list
    cordinates, dl = tensor_list
    """
    Расчёт напряжённости от одного проводника\n
    I - ток в расматриваем проводнике\n
    cordinates - координаты элементрных участков проводника\n
    dl - длинна элементарных участков\n
    x,y,z - координаты точки в которой определяем напряжённость поля\n
    """
    t = dl[obj].size()[0]
    point = torch.tensor([x[k],y[k],z[k] if trig else z],dtype=torch.float32).to(device)
    rv = (point - cordinates[obj])[:t,:]
    r = 1/(4*np.pi*torch.norm(rv,dim=1)**3)
    r = torch.reshape(r, (t,1))
    dH = torch.cross(dl[obj], rv)*r
    rez = torch.sum(dH,dim=0)*I[obj]
    trig = torch.isnan(rez)
    rt = torch.tensor([rez[0] if not trig[0] else I,\
                        rez[1] if not trig[1] else I,\
                        rez[2] if not trig[2] else I,],dtype=torch.float32).numpy()*alfs[obj]

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
    dl_1, dl_2 = tensor_list[1],tensor_list[3]
    t_1 = dl_1.size()[0]
    t_2 = dl_2.size()[0]
    
    Cordinates_1 = tensor_list[0][:t_1,:]
    Cordinates_2 = tensor_list[2][:t_2,:]

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
        


def run_area_calc(tp,lst, area, hz, step, DL, deg, callback_func = None):
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
                cordinate, dl = SolinoidTorch(*args)
            elif m>1:
                cordinate, dl = Solinoid1Torch(*args) #Torch
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


        for obj in range(len(dls)):
            cordinates[obj] = torch.from_numpy(cordinates[obj])
            dls[obj] = torch.from_numpy(dls[obj])
                
        k=0
        for i in range(row):
            for j in range(col):
                X[k] =j*step+area[0]
                Y[k] =i*step+area[1]
                k+=1

        PC = Paralel_Calc([cordinates, dls],[X,Y,hz[0],alfs,Is,False],k,2.4,H_area, [lambda: callback_func[0]((X,Y),H_area),callback_func[1]])

        
        if callback_func is None:
            PC.start(join=True)
            return (X,Y), H_area

        else:
            PC.start()

        
    elif tp == "V_calc_area":
        d = ((area[2]-area[0])**2+(area[3]-area[1])**2)**0.5
        d = f(d,step)
        col = int(d/step)+1

        hz = (f(hz[0],step),f(hz[1],step))
        row = int((hz[1]-hz[0])/step)+1

        H_area = np.zeros((row*col,3),dtype=np.complex64)
        X = np.zeros(row*col,dtype=np.float32)
        Y = np.zeros(row*col,dtype=np.float32)
        Z = np.zeros(row*col,dtype=np.float32)

        for obj in range(len(dls)):
            cordinates[obj] = torch.from_numpy(cordinates[obj])
            dls[obj] = torch.from_numpy(dls[obj])

        qu_cpu = LifoQueue()
        qu_gpu = LifoQueue()
        qu_gpu.put(("Start",None,None))
        f = Feedback([lambda: callback_func[0]((X,Y,Z),H_area),callback_func[1]] if callback_func is not None else lambda :print("я отработала"))
        
        k=0
        for i in range(row):
            for j in range(col):
                m=step*j/d
                X[k] = (area[0]+area[2]*(m/(1-m)))/(1+(m/(1-m))) if (1-m)!= 0 else area[2]
                Y[k] = (area[1]+area[3]*(m/(1-m)))/(1+(m/(1-m))) if (1-m)!= 0 else area[3]
                Z[k] = i*step+hz[0]
                k+=1

        p1 = Thread(target=Paralel_calk, args = ("cpu", [cordinates, dls], [X,Y,Z,alfs,Is,True], k, 2.4, qu_cpu, qu_gpu, H_area, [f,callback_func[1]]))
        p2 = Thread(target=Paralel_calk, args = ('gpu', [cordinates, dls], [X,Y,Z,alfs,Is,True], k, 2.4, qu_cpu, qu_gpu, H_area, [f,callback_func[1]]))
        p1.start()
        p2.start()

        callback_func[1].canceled.connect(lambda:CloseCalc(p1,p2,qu_cpu,qu_gpu))

        if callback_func is None:
            p1.join()
            p2.join()
            #H_area = np.linalg.norm(H_area,axis=1)
            return (X,Y,Z), H_area

        
    elif tp == "O_calc_point":
        H_point = np.zeros(3,dtype=np.complex128)
        for obj in range(len(dls)):
            H_point += MagnetikVoltage(Is[obj],cordinates[obj], dls[obj],area[0],area[1],hz[0])*alfs[obj]
        H_area = np.linalg.norm(H_point)

        return str(round(H_area,2))
    

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


    