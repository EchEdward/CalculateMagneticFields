import torch
import numpy as np
from threading import Thread, Event
from queue import Queue, LifoQueue
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo
import sys
from time import time

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


class Thread_Calc(Thread):
    def __init__(self,tsk_for,tensors_list,common_list,queue_list,coef_mmr,Result,calc_func,Feedback = None):
        Thread.__init__(self)
        self.tsk_for = tsk_for
        self.qu_cpu, self.qu_gpu, self.number_of_tasks = queue_list
        self.tensors_list, self.common_list = tensors_list, common_list
        self.coef_mmr = coef_mmr
        self.Result = Result
        self.calc_func = calc_func
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
                print("cpu_end")
                if self.call:
                    self.back("cpu")
                break

            elif task_Trig == "Cancel" and cpu_start:
                break

            elif task_Trig == "Work" and cpu_start:
                self.Result[k,:] +=  self.calc_func(*self.tensors_list,*self.common_list,k,obj,"cpu")
                if self.call:
                    #self.message_widget[2](number_task-(self.qu_gpu.qsize()+self.qu_cpu.qsize()))
                    self.setNewSignal(number_task-(self.qu_gpu.qsize()+self.qu_cpu.qsize()))

            elif task_Trig == "Start":
                self.lastIndTime = time()
                cpu_start = True
                if self.call:
                    number_task = self.qu_gpu.qsize() + self.qu_cpu.qsize()

            else:
                self.qu_cpu.put((task_Trig, k, obj))

    def gpu_start(self):
        while not self.event.is_set():
            task_Trig, k, obj = self.qu_gpu.get()
            if task_Trig == "Start":
                self.lastIndTime = time()
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
                                tensors_list_gpu[j][i] = self.tensors_list[j][i].to(device) #device
                                #tensors_list_gpu[j][i] = self.tensors_list[j][i].numpy()
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
                    self.message_widget[1](0, number_task)
                

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
                self.Result[k,:] +=  self.calc_func(*tensors_list_gpu,*self.common_list,k,obj,device)
                if self.call:
                    #self.message_widget[2](number_task-(self.qu_gpu.qsize()+self.qu_cpu.qsize()))
                    self.setNewSignal(number_task-(self.qu_gpu.qsize()+self.qu_cpu.qsize()))
                    
    def setNewSignal(self,val):
        t = time()
        if t-self.lastIndTime>0.5:
            self.message_widget[2](val)
            self.lastIndTime = t
   



class Paralel_Calc():
    def __init__(self,tensors_list,common_list,tasks,coef_mmr,Result,calc_func,Feedback = None):
        self.tensors_list, self.common_list = tensors_list, common_list
        self.coef_mmr = coef_mmr
        self.Result = Result
        self.tasks = tasks
        self.calc_func = calc_func
        self.qu_cpu = LifoQueue()
        self.qu_gpu = LifoQueue()
        self.qu_gpu.put(("Start",None,None))

        #Feedback = None
        if Feedback is not None:
            self.Feedback = [self.call_back(Feedback),Feedback[1],Feedback[2]]
            self.Feedback[1][0](lambda: self.stop())
        else:
            self.Feedback = None



    def start(self, join=False):
        self.p1 = Thread_Calc("cpu", self.tensors_list, self.common_list,[self.qu_cpu, self.qu_gpu, self.tasks], self.coef_mmr, self.Result,self.calc_func,self.Feedback)
        self.p2 = Thread_Calc("gpu", self.tensors_list, self.common_list,[self.qu_cpu, self.qu_gpu, self.tasks], self.coef_mmr, self.Result,self.calc_func,self.Feedback)
        self.p1.start()
        self.p2.start()
        if join:
            self.p1.join()
            self.p2.join() 


    def stop(self):
        self.p1.stop()
        self.p2.stop()

    def call_back(self,call_func,cpu = False, gpu = False):
        """ Вызов функции по завершению расчёта """
        def Call(device):
            nonlocal cpu, gpu, call_func
            if device == "cpu":
                cpu = True
            if device == "gpu":
                gpu = True
            if cpu and gpu:
                call_func[0]()
                if call_func[2] is not None:
                    call_func[2]()
        return Call