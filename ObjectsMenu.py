# pylint: disable=E0611
# pylint: disable=E1101
#pyi-makespec --onefile --icon=icon.ico --noconsole VEZRead.py
from PyQt5.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,\
     QLineEdit, QItemDelegate, QComboBox,QColorDialog, QSpacerItem,QSizePolicy,\
     QTableWidget, QCheckBox, QGridLayout, QTableWidgetItem, QSpinBox, QListView,\
     QRadioButton, QButtonGroup
from PyQt5.QtGui import  QValidator, QColor, QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt

from main_calculate import SolenParam
import numpy as np


class MyValidator(QValidator):
    """ Позволяет вводить только числа """
    def __init__(self, var, parent,to=False,minus=False):
        QValidator.__init__(self, parent)
        self.minus = minus
        self.var = var
        self.to = to
        self.s = set(['0','1','2','3','4','5','6','7','8','9','.',',',''])

    def validate(self, s, pos): 
        """ проверяет привильная ли строка """   
        i=-1
        t1 = 0
        t2 = False
        t3 = 0
        for i in range(len(s)):
            if self.minus and i==0 and s[i] =="-":
                t3 += 1
                
            elif self.minus and i!=0 and s[i] =="-":
                i=-1
                break

            if self.to and i==2:
                if s[i] !="." and s[i] !="," and self.var == "duble":
                    i=-1
                    break
                elif self.var == "int":
                    i=-1
                    break
            if s[i] == ".":
                if self.var =="int":
                    i=-1
                    break
                elif self.var =="duble":
                    t1 += 1
            if s[i] == ",":
                if self.var =="int":
                    i=-1
                    break
                elif self.var =="duble":
                    t1 += 1
                    t2 = True
            if t1>1:
                i=-1
                break
            if s[i] not in self.s and not (self.minus and s[i]=="-"):
                i-=1
                break

        if s=='-':
            t2=True
        
        if i == len(s)-1:
            if t2:
                return (QValidator.Intermediate, s, pos) 
            else:
                return (QValidator.Acceptable, s, pos)
        else:
            return (QValidator.Invalid, s, pos)

    def fixup(self, s):
        """ форматирует неправильную строку """
        s1=''
        if s=="-":return ""
        t = False
        for i in s:
            if i in self.s or (self.minus and i=="-"):
                if  (i=="." or i==","):
                    if not t:
                        s1+="."
                        t = True
                else:
                    s1+=i
        s=s1
        return s

class DownloadDelegate(QItemDelegate):
    """ Переопределение поведения ячейки таблицы """
    def __init__(self, tp, parent=None, disable={"table2":True}):
        super(DownloadDelegate, self).__init__(parent)
        self.tp = tp
        self.disable = disable

    def createEditor(self, parent, option, index):
        lineedit=QLineEdit(parent)
        if self.tp=="cord":
            lineedit.setValidator(MyValidator("duble",lineedit,minus=True))
            return lineedit#QItemDelegate.createEditor(self, parent, option, index)
        elif self.tp=="fmax":
            if index.column()<2:
                return
            else:
                if self.disable["table2"]:
                    lineedit.setValidator(MyValidator("duble",lineedit,minus=True))
                    return lineedit#QItemDelegate.createEditor(self, parent, option, index)
                else:
                    return
        elif self.tp=="contour":
            if index.column()==1:
                lineedit.setValidator(MyValidator("duble",lineedit,minus=False))
                return lineedit

class Save_Widget(QWidget):
    def __init__(self, sp, func, parent=None):
        super(Save_Widget,self).__init__(parent)

        self.sp = sp
        self.func = func

        self.setFixedSize(250,300)

        self.setWindowTitle("Сохранить")
        
        self.list = QListView()
        self.ski = QStandardItemModel()

        self.radio_button_1 = QRadioButton('В новый файл')
        self.radio_button_1.setChecked(True)

        self.radio_button_2 = QRadioButton('В сущ. файл')

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.radio_button_1)
        self.button_group.addButton(self.radio_button_2)

        self.btn_ok = QPushButton('Ok')
        self.btn_ok.clicked.connect(self.Return)

        V_box = QVBoxLayout()
        H_box1 = QHBoxLayout()
        H_box2 = QHBoxLayout()

        H_box1.addWidget(self.radio_button_1)
        H_box1.addWidget(self.radio_button_2)

        H_box2.addItem(QSpacerItem(2, 2, QSizePolicy.Expanding, QSizePolicy.Minimum))
        H_box2.addWidget(self.btn_ok)


        V_box.addLayout(H_box1)
        V_box.addWidget(self.list)
        V_box.addLayout(H_box2)

        self.setLayout(V_box)

        
        self.items = []

        for i in sp:
            if i[2] == "H_calc_area":
                it = QStandardItem(QIcon('images/rectangle.png'),i[1])
                #elif i[2] == "V_calc_area":
                #it = QStandardItem(QIcon('images/line.jpg'),i[1])
            elif i[2] == "O_calc_point":
                it = QStandardItem(QIcon('images/point.jpg'),i[1])

            else:
                continue

            it.setCheckable(True)
            it.setCheckState(False)
            
            self.ski.appendRow(it)
            self.items.append(it)
        
        self.list.setModel(self.ski)

        

    def Return(self):
        sp = [self.sp[i][0] for i in range(len(self.items)) if self.items[i].checkState() == Qt.Checked]
        t = self.button_group.checkedButton().text() == 'В новый файл'
        self.close()
        
        self.func(sp,t)

class IntDataPoint:
    def __init__(self, who, atrr=""):
        self._atrr = atrr
        self._who = who

    @property
    def number(self):
        if len(self._atrr) == 0:
            raise Exception(f"Значение '{self._who}' не введено")
        return int(self._atrr)
    
    def setNumber(self,f):
        try:
            if f % 1 != 0: raise Exception
            int(f)
        except Exception:
            raise Exception(f"Значение '{self._who}' не коректно")
        else:
            self._atrr = str(f)

    @property
    def text(self):
        return self._atrr

    def setText(self,text):
        self._atrr = text

class FloatDataPoint:
    def __init__(self, who, koef=1, atrr=""):
        self._atrr = atrr
        self._who = who
        self._koef = koef

    @property
    def number_gui(self):
        return self.number*self._koef

    @property
    def number(self):
        if len(self._atrr) == 0:
            raise Exception(f"Значение '{self._who}' не введено")
        return float(self._atrr)
    
    def setNumber_gui(self,f):
        self._atrr = str(round(self._setNumber(f)/self._koef,3))

    def setNumber(self,f):
        self._atrr = str(round(self._setNumber(f),3))

    def _setNumber(self,f):
        try:
            float(f)
        except Exception:
            raise Exception(f"Значение '{self._who}' не коректно")
        else:
            return f

    @property
    def text(self):
        return self._atrr

    def setText(self,text):
        self._atrr = text

class TableDataPoint:
    def __init__(self, who, cols=1, koef=(1,), atrr=[]):
        self._atrr = atrr
        self._who = who
        self._koef = koef
        self._cols = cols

    @property
    def number(self):
        arr = []
        try:
            for r in self._atrr:
                if self._cols == 1:
                    row = arr
                else: 
                    row = []
                for i in range(self._cols):
                    row.append(float(r) if self._cols == 1 else float(r[i]))

                if self._cols != 1:
                    arr.append(row)
        except Exception:
            raise Exception(f"Значение '{self._who}' не введено")
        else:
            return arr

    @property
    def number_gui(self):
        arr = []
        for i in self.number:
            a = []
            for j in range(self._cols):
                a.append(i[j]*self._koef[j])
            arr.append(a)
        return arr

    def _setNumber(self,arr,trig):
        try:
            if trig:
                koef = self._koef
            else:
                koef = [1]*self._cols
            _atrr = []
            for r in arr:
                if self._cols == 1:
                    row = _atrr
                else: 
                    row = []
                for i in range(self._cols):
                    a = float(r) if self._cols == 1 else float(r[i])
                    row.append(str(r) if self._cols == 1 else str(round(r[i]/koef[i],3)))

                if self._cols != 1:
                    _atrr.append(row)
        except Exception:
            raise Exception(f"Значение '{self._who}' не коректно")
        else:
            self._atrr = _atrr

    def setNumber(self,arr):
        self._setNumber(arr,False)
    def setNumber_gui(self,arr):
        self._setNumber(arr,True)

    @property
    def text(self):
        return self._atrr

    def setText(self,arr):      
        self._atrr = arr
       

class MenuData:
    def __init__(self,type_object=None,init_data={}):
        #print(init_data)

        self._parent = None

        if type_object is None and len(init_data)>0:
            self.type_object = init_data['type_object']
            self.name = init_data['name']
        elif type_object is not None and len(init_data)==0:
            self.type_object = type_object
            self.name = ""
        else:
            raise Exception("Create MenuData is failed")

        if self.type_object == "one_point":
            self.one_point(init_data)
        elif self.type_object == "vertical_area":
            self.vertical_area(init_data)
        elif self.type_object == "horizontal_area":
            self.horizontal_area(init_data)
        elif self.type_object == "conductor":
            self.conductor(init_data)
        elif self.type_object == "reactor":
            self.reactor(init_data)

    
    def setParent(self,parent):
        self._parent = parent
        

    def one_point(self,d):
        self.line_color = d.get("line_color",'#000000')
        self.X = FloatDataPoint(f"Точка {self.name}, X",koef=1000, atrr=d.get("X",""))
        self.Y = FloatDataPoint(f"Точка {self.name}, Y",koef=-1000, atrr=d.get("Y",""))
        self.Z = FloatDataPoint(f"Точка {self.name}, Z", atrr=d.get("Z","1.8"))
        self.dl = FloatDataPoint(f"Точка {self.name}, dl", atrr=d.get("dl","0.01"))
        self.da = FloatDataPoint(f"Точка {self.name}, da", atrr=d.get("da","1"))
        self.result = FloatDataPoint(f"Точка {self.name}, результат", atrr=d.get("result","0.00"))


    def vertical_area(self,d):
        self.line_color = d.get("line_color",'#000000')
        self.X1 = FloatDataPoint(f"Вертикальное сечение {self.name}, X1",koef=1000, atrr=d.get("X1",""))
        self.X2 = FloatDataPoint(f"Вертикальное сечение {self.name}, X2",koef=1000, atrr=d.get("X2",""))
        self.Y1 = FloatDataPoint(f"Вертикальное сечение {self.name}, Y1",koef=-1000, atrr=d.get("Y1",""))
        self.Y2 = FloatDataPoint(f"Вертикальное сечение {self.name}, Y2",koef=-1000, atrr=d.get("Y2",""))
        self.Z1 = FloatDataPoint(f"Вертикальное сечение {self.name}, Z1", atrr=d.get("Z1","0"))
        self.Z2 = FloatDataPoint(f"Вертикальное сечение {self.name}, Z2", atrr=d.get("Z2","2"))
        self.dg = FloatDataPoint(f"Вертикальное сечение {self.name}, dg", atrr=d.get("dg","0.5"))
        self.dl = FloatDataPoint(f"Вертикальное сечение {self.name}, dl", atrr=d.get("dl","0.01"))
        self.da = FloatDataPoint(f"Вертикальное сечение {self.name}, da", atrr=d.get("da","1"))

    def horizontal_area(self,d):
        self.line_color = d.get("line_color",'#000000')
        self.X1 = FloatDataPoint(f"Горизонтальное сечение {self.name}, X1",koef=1000, atrr=d.get("X1",""))
        self.X2 = FloatDataPoint(f"Горизонтальное сечение {self.name}, X2",koef=1000, atrr=d.get("X2",""))
        self.Y1 = FloatDataPoint(f"Горизонтальное сечение {self.name}, Y1",koef=-1000, atrr=d.get("Y1",""))
        self.Y2 = FloatDataPoint(f"Горизонтальное сечение {self.name}, Y2",koef=-1000, atrr=d.get("Y2",""))
        self.Z = FloatDataPoint(f"Горизонтальное сечение {self.name}, Z", atrr=d.get("Z","1.8"))
        self.dg = FloatDataPoint(f"Горизонтальное сечение {self.name}, dg", atrr=d.get("dg","0.5"))
        self.dl = FloatDataPoint(f"Горизонтальное сечение {self.name}, dl", atrr=d.get("dl","0.01"))
        self.da = FloatDataPoint(f"Горизонтальное сечение {self.name}, da", atrr=d.get("da","1"))

    def conductor(self,d):
        self.line_color = d.get("line_color",'#000000')
        self.I = FloatDataPoint(f"Шина {self.name}, I", atrr=d.get("I",""))
        self.deg = FloatDataPoint(f"Шина {self.name}, deg", atrr=d.get("deg",""))

        self.tbl_XY = TableDataPoint(f"Шина {self.name}, XY", cols=2, koef=(1000,-1000), atrr=d.get("tbl_XY",[]))
        self.tbl_Z = TableDataPoint(f"Шина {self.name}, Z", atrr=d.get("tbl_Z",[]))
        self.tbl_fmax = TableDataPoint(f"Шина {self.name}, fmax", atrr=d.get("tbl_fmax",[]))

        self.lbl_fmax = FloatDataPoint(f"Шина {self.name}, common_fmax", atrr=d.get("lbl_fmax",""))
        self.chck_fmax = d.get("chck_fmax", False)

    def reactor(self,d): 
        self.body_color = d.get("body_color",'#ff0000')
        self.line_color = d.get("line_color",'#000000')
        self.I = FloatDataPoint(f"Реактор {self.name}, I", atrr=d.get("I",""))
        self.deg = FloatDataPoint(f"Реактор {self.name}, deg", atrr=d.get("deg",""))
        self.X = FloatDataPoint(f"Реактор {self.name}, X",koef=1000, atrr=d.get("X",""))
        self.Y = FloatDataPoint(f"Реактор {self.name}, Y",koef=-1000, atrr=d.get("Y",""))
        self.Z = FloatDataPoint(f"Реактор {self.name}, Z", atrr=d.get("Z",""))
        self.Rnar = FloatDataPoint(f"Реактор {self.name}, Rнар",koef=1000, atrr=d.get("Rnar",""))
        self.Rvn = FloatDataPoint(f"Реактор {self.name}, Rвн", atrr=d.get("Rvn",""))
        self.H = FloatDataPoint(f"Реактор {self.name}, h", atrr=d.get("H",""))
        self.W = IntDataPoint(f"Реактор {self.name}, витки", atrr=d.get("W",""))
        self.m = IntDataPoint(f"Реактор {self.name}, слои", atrr=d.get("m",""))
        self.dP = FloatDataPoint(f"Реактор {self.name}, dP", atrr=d.get("dP",""))
        self.Q = FloatDataPoint(f"Реактор {self.name}, Q", atrr=d.get("Q",""))
        self.Unom = FloatDataPoint(f"Реактор {self.name}, Unom", atrr=d.get("Unom",""))
        self.met = d.get("met","")
        self.Xl = FloatDataPoint(f"Реактор {self.name}, Xl", atrr=d.get("Xl",""))
        self.Inom = FloatDataPoint(f"Реактор {self.name}, Iном", atrr=d.get("Inom",""))

    def save(self):
        d = {}
        d["name"] = self.name
        d["type_object"] = self.type_object

        if self._parent is not None: self._parent.InitCords()

        if self.type_object == "reactor":
            d["body_color"] =self.body_color
            d["line_color"] = self.line_color
            d["I"] = self.I.text
            d["deg"] = self.deg.text
            d["X"] = self.X.text
            d["Y"] = self.Y.text
            d["Z"] = self.Z.text
            d["Rnar"] = self.Rnar.text
            d["Rvn"] = self.Rvn.text
            d["H"] = self.H.text
            d["W"] = self.W.text
            d["m"] = self.m.text
            d["dP"] = self.dP.text
            d["Q"] = self.Q.text
            d["Unom"] = self.Unom.text
            d["met"] = self.met
            d["Xl"] = self.Xl.text
            d["Inom"] = self.Inom.text
            return d
        
        elif self.type_object == "conductor":
            d["line_color"] = self.line_color
            d["I"] = self.I.text
            d["deg"] = self.deg.text
            d["lbl_fmax"] = self.lbl_fmax.text
            d["chck_fmax"] = self.chck_fmax

            d["tbl_XY"] = self.tbl_XY.text
            d["tbl_Z"] = self.tbl_Z.text
            d["tbl_fmax"] = self.tbl_fmax.text
            return d

        elif self.type_object == "horizontal_area":
            #print(self.X1.text,self.Y1.text,self.X2.text,self.Y2.text)
            d["line_color"] = self.line_color
            d["X1"] = self.X1.text
            d["Y1"] = self.Y1.text
            d["X2"] = self.X2.text
            d["Y2"] = self.Y2.text
            d["Z"] = self.Z.text
            d["dg"] = self.dg.text
            d["da"] = self.da.text
            d["dl"] = self.dl.text
            return d

        elif self.type_object == "vertical_area":
            d["line_color"] = self.line_color
            d["X1"] = self.X1.text
            d["Y1"] = self.Y1.text
            d["X2"] = self.X2.text
            d["Y2"] = self.Y2.text
            d["Z1"] = self.Z1.text
            d["Z2"] = self.Z2.text
            d["dg"] = self.dg.text
            d["da"] = self.da.text
            d["dl"] = self.dl.text
            return d

        elif self.type_object == "one_point":
            d["line_color"] = self.line_color
            d["X"] = self.X.text
            d["Y"] = self.Y.text
            d["Z"] = self.Z.text
            d["da"] = self.da.text
            d["dl"] = self.dl.text
            d["result"] = self.result.text
            return d


    @staticmethod
    def _border(a,b):
        return (min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[0]),max(a[3],b[1]))

    def borders(self):
        xmin, ymin, xmax, ymax  = float("inf"), float("inf"), -float("inf"), -float("inf") 

        if self.type_object == "one_point":
            xmin, ymin, xmax, ymax = self._border((xmin, ymin, xmax, ymax),(self.X.number_gui+25, -self.Y.number_gui+25))
            xmin, ymin, xmax, ymax = self._border((xmin, ymin, xmax, ymax),(self.X.number_gui-25, -self.Y.number_gui-25))
        elif self.type_object == "vertical_area":
            xmin, ymin, xmax, ymax = self._border((xmin, ymin, xmax, ymax),(self.X1.number_gui, -self.Y1.number_gui))
            xmin, ymin, xmax, ymax = self._border((xmin, ymin, xmax, ymax),(self.X2.number_gui, -self.Y2.number_gui))
        elif self.type_object == "horizontal_area":
            xmin, ymin, xmax, ymax = self._border((xmin, ymin, xmax, ymax),(self.X1.number_gui, -self.Y1.number_gui))
            xmin, ymin, xmax, ymax = self._border((xmin, ymin, xmax, ymax),(self.X2.number_gui, -self.Y2.number_gui))
        elif self.type_object == "conductor":
            for x,y in self.tbl_XY.number_gui:
                xmin, ymin, xmax, ymax = self._border((xmin, ymin, xmax, ymax),(x, -y))
        elif self.type_object == "reactor":
            r = self.Rnar.number_gui
            xmin, ymin, xmax, ymax = self._border((xmin, ymin, xmax, ymax),(self.X.number_gui+r, -self.Y.number_gui+r))
            xmin, ymin, xmax, ymax = self._border((xmin, ymin, xmax, ymax),(self.X.number_gui-r, -self.Y.number_gui-r))

        return (xmin, ymin, xmax, ymax)

    def read_data(self):
        if self._parent is not None: self._parent.InitCords()

        if self.type_object == "reactor":
            x, y, z = self.X.number, self.Y.number, self.Z.number
            Rnar = self.Rnar.number
            h = self.H.number
            n = self.W.number
            m = self.m.number
            fase = self.deg.number
            alf=np.cos(fase*np.pi/180)+1j*np.sin(fase*np.pi/180)
            I = self.I.number

            if m > 1 and self.Rvn.number >= Rnar:
                raise Exception(f"Внутренний радиус реактора {self.name} больше внешнего")
            elif m > 1:
                Rvn = self.Rvn.number          
                    
            if m > 1:
                a = (x,y,z,Rnar,h,n,m,(Rnar-Rvn)/(m-1))
            else:
                a = (x,y,z,Rnar,h,n)

            return (self.type_object,a, m, alf, I)

        elif self.type_object == "conductor":
            I = self.I.number
            fase = self.deg.number
            alf=np.cos(fase*np.pi/180)+1j*np.sin(fase*np.pi/180)
            cord = tuple([(i,j,k) for (i,j),k in zip(self.tbl_XY.number,self.tbl_Z.number)])
            if self.chck_fmax:
                fmax = tuple(self.tbl_fmax.number)
                a = (cord,fmax)
            else:
                a = (cord,)

            return (self.type_object,a, alf, I)

        elif self.type_object == "horizontal_area":
            area_calc = (self.X1.number,self.Y2.number,self.X2.number,self.Y1.number)
            dg = self.dg.number
            dl = self.dl.number
            da = self.da.number
            z = (self.Z.number,)

            return (self.type_object, area_calc, z, da, dl, dg)

        elif self.type_object == "vertical_area":
            area_calc = (self.X1.number,self.Y2.number,self.X2.number,self.Y1.number)
            dg = self.dg.number
            dl = self.dl.number
            da = self.da.number
            z = (self.Z1.number,self.Z2.number)

            return (self.type_object, area_calc, z, da, dl, dg)

        elif self.type_object == "one_point":
            area_calc = [self.X.number,self.Y.number]
            dg = 0.5
            dl = self.dl.number
            da = self.da.number
            z = (self.Z.number,)

            return (self.type_object, area_calc, z, da, dl, dg)




class OnePoint(QWidget):
    def __init__(self,setCrl,getPos,setPos,parent=None,data=None):#
        super(OnePoint,self).__init__(parent)
        self.setCrl = setCrl
        self.getPos = getPos
        self.setPos = setPos

        self.setListName = lambda: 0

        self.setFixedSize(320,200)

        self.setWindowTitle("В одной точке")
        HspacerItem = [QSpacerItem(2, 2, QSizePolicy.Expanding, QSizePolicy.Minimum) for i in range(2)]
        VspacerItem = [QSpacerItem(2, 2, QSizePolicy.Minimum, QSizePolicy.Expanding) for i in range(2)]

        self.data = MenuData("one_point") if data is None else data
        self.data.setParent(self)

        self.name = QLineEdit()
        BoxLayoutB1 = QVBoxLayout()
        BoxLayoutB1.addWidget(QLabel("Название"))
        BoxLayoutB1.addWidget(self.name)

        BoxLayout1 = QHBoxLayout()
        self.line = QPushButton()
        self.line.setFixedWidth(23)
        self.line_color = QColor("black").name()
        self.line.setStyleSheet( " background-color: %s; " % self.line_color )
        self.line.clicked.connect(self.getColor)

        BoxLayout1.addWidget(QLabel("Цвет линии:"))
        BoxLayout1.addWidget(self.line)
        BoxLayout1.addItem(HspacerItem[0])

        BoxLayoutB1.addLayout(BoxLayout1)

        grid_layout = QGridLayout()

        self.Z = QLineEdit()
        self.Z.setValidator(MyValidator("duble",self.Z,minus=False))
        grid_layout.addWidget(QLabel("Z, м:"),2,0)
        grid_layout.addWidget(self.Z,2,1)


        self.X = QLineEdit()
        self.X.setValidator(MyValidator("duble",self.X,minus=True))
        grid_layout.addWidget(QLabel("X, м:"),0,0)
        grid_layout.addWidget(self.X,0,1)

        self.Y = QLineEdit()
        self.Y.setValidator(MyValidator("duble",self.Y,minus=True))
        grid_layout.addWidget(QLabel("Y, м:"),1,0)
        grid_layout.addWidget(self.Y,1,1)

        self.dl = QLineEdit()
        self.dl.setValidator(MyValidator("duble",self.dl,minus=False))
        grid_layout.addWidget(QLabel("dl проводника, м:"),0,2)
        grid_layout.addWidget(self.dl,0,3)

        self.da = QLineEdit()
        self.da.setValidator(MyValidator("duble",self.da,minus=False))
        grid_layout.addWidget(QLabel("da реактора, \u00B0:"),1,2)
        grid_layout.addWidget(self.da,1,3)


        self.ok = QPushButton("Ok")
        self.ok.clicked.connect(self.save_data)
        self.cancel = QPushButton("Отмена")
        self.cancel.clicked.connect(self.close)
        BoxLayoutB6 = QHBoxLayout()
        BoxLayoutB6.addItem(HspacerItem[1])
        BoxLayoutB6.addWidget(self.ok)
        BoxLayoutB6.addWidget(self.cancel)

        BoxLayoutB7 = QVBoxLayout()
        BoxLayoutB7.addLayout(BoxLayoutB1)
        BoxLayoutB7.addLayout(grid_layout)
        BoxLayoutB7.addLayout(BoxLayoutB6)

        self.setLayout(BoxLayoutB7)

        self.InitCords()

    
    def InitCords(self):
        cord = self.getPos()
        self.data.X.setNumber_gui(cord[0])
        self.data.Y.setNumber_gui(cord[1])



    def getColor(self):
        color = QColorDialog.getColor(initial=QColor(self.line_color),parent=self,\
                    title="Цвет контура",options=QColorDialog.ShowAlphaChannel)
        self.line_color = color.name()
        self.line.setStyleSheet( " background-color: %s; " % self.line_color )

    def save_data(self):
        self.data.line_color = self.line_color
        self.data.name = self.name.text()
        self.data.Z.setText(self.Z.text())

        self.data.X.setText(self.X.text())
        self.data.Y.setText(self.Y.text())

        self.data.dl.setText(self.dl.text())
        self.data.da.setText(self.da.text())

        self.close()
        self.setPos((self.data.X.number_gui,self.data.Y.number_gui))
        self.setCrl()
        self.setListName()

    def show(self, *args, **kwargs):
        try:
            self.name.setText(self.data.name)
            self.line_color = self.data.line_color if self.data.line_color != '' else QColor("black").name()
            self.line.setStyleSheet( " background-color: %s; " % self.line_color )
            self.Z.setText(self.data.Z.text)
            self.dl.setText(self.data.dl.text)
            self.da.setText(self.data.da.text)

            self.InitCords()

            self.X.setText(self.data.X.text)
            self.Y.setText(self.data.Y.text)

        except Exception as ex:
            print(ex)
        
        QWidget.show(self, *args, **kwargs)

class CalcAreaV(QWidget):
    def __init__(self,setCrl,getPos,setPos,parent=None,data=None):
        super(CalcAreaV,self).__init__(parent)
        self.setCrl = setCrl
        self.getPos = getPos
        self.setPos = setPos

        self.setListName = lambda: 0

        self.setFixedSize(320,270)

        self.setWindowTitle("Вертикальная область")
        HspacerItem = [QSpacerItem(2, 2, QSizePolicy.Expanding, QSizePolicy.Minimum) for i in range(2)]
        VspacerItem = [QSpacerItem(2, 2, QSizePolicy.Minimum, QSizePolicy.Expanding) for i in range(2)]

        self.data = MenuData("vertical_area") if data is None else data
        self.data.setParent(self)

        self.name = QLineEdit()
        BoxLayoutB1 = QVBoxLayout()
        BoxLayoutB1.addWidget(QLabel("Название"))
        BoxLayoutB1.addWidget(self.name)

        BoxLayout1 = QHBoxLayout()
        self.line = QPushButton()
        self.line.setFixedWidth(23)
        self.line_color = QColor("black").name()
        self.line.setStyleSheet( " background-color: %s; " % self.line_color )
        self.line.clicked.connect(self.getColor)

        BoxLayout1.addWidget(QLabel("Цвет линии:"))
        BoxLayout1.addWidget(self.line)
        BoxLayout1.addItem(HspacerItem[0])

        BoxLayoutB1.addLayout(BoxLayout1)

        grid_layout = QGridLayout()

        self.Z1 = QLineEdit()
        self.Z1.setValidator(MyValidator("duble",self.Z1,minus=False))
        grid_layout.addWidget(QLabel("Z1, м:"),0,0)
        grid_layout.addWidget(self.Z1,0,1)

        self.Z2 = QLineEdit()
        self.Z2.setValidator(MyValidator("duble",self.Z2,minus=False))
        grid_layout.addWidget(QLabel("Z2, м:"),1,0)
        grid_layout.addWidget(self.Z2,1,1)

        self.X1 = QLineEdit()
        self.X1.setValidator(MyValidator("duble",self.X1,minus=True))
        grid_layout.addWidget(QLabel("X1, м:"),2,0)
        grid_layout.addWidget(self.X1,2,1)

        self.Y1 = QLineEdit()
        self.Y1.setValidator(MyValidator("duble",self.Y1,minus=True))
        grid_layout.addWidget(QLabel("Y1, м:"),3,0)
        grid_layout.addWidget(self.Y1,3,1)

        self.X2 = QLineEdit()
        self.X2.setValidator(MyValidator("duble",self.X2,minus=True))
        grid_layout.addWidget(QLabel("X2, м:"),4,0)
        grid_layout.addWidget(self.X2,4,1)

        self.Y2 = QLineEdit()
        self.Y2.setValidator(MyValidator("duble",self.Y2,minus=True))
        grid_layout.addWidget(QLabel("Y2, м:"),5,0)
        grid_layout.addWidget(self.Y2,5,1)

        self.dg = QLineEdit()
        self.dg.setValidator(MyValidator("duble",self.dg,minus=False))
        grid_layout.addWidget(QLabel("Шаг сетки расчета, м:"),0,2)
        grid_layout.addWidget(self.dg,0,3)

        self.dl = QLineEdit()
        self.dl.setValidator(MyValidator("duble",self.dl,minus=False))
        grid_layout.addWidget(QLabel("dl проводника, м:"),1,2)
        grid_layout.addWidget(self.dl,1,3)

        self.da = QLineEdit()
        self.da.setValidator(MyValidator("duble",self.da,minus=False))
        grid_layout.addWidget(QLabel("da реактора, \u00B0:"),2,2)
        grid_layout.addWidget(self.da,2,3)


        self.ok = QPushButton("Ok")
        self.ok.clicked.connect(self.save_data)
        self.cancel = QPushButton("Отмена")
        self.cancel.clicked.connect(self.close)
        BoxLayoutB6 = QHBoxLayout()
        BoxLayoutB6.addItem(HspacerItem[1])
        BoxLayoutB6.addWidget(self.ok)
        BoxLayoutB6.addWidget(self.cancel)

        BoxLayoutB7 = QVBoxLayout()
        BoxLayoutB7.addLayout(BoxLayoutB1)
        BoxLayoutB7.addLayout(grid_layout)
        BoxLayoutB7.addLayout(BoxLayoutB6)

        self.setLayout(BoxLayoutB7)

        self.InitCords()

    def InitCords(self):
        cord = self.getPos()
        self.data.X1.setNumber_gui(cord[0])
        self.data.Y1.setNumber_gui(cord[1])
        self.data.X2.setNumber_gui(cord[2])
        self.data.Y2.setNumber_gui(cord[3])


    def getColor(self):
        color = QColorDialog.getColor(initial=QColor(self.line_color),parent=self,\
                    title="Цвет контура",options=QColorDialog.ShowAlphaChannel)
        self.line_color = color.name()
        self.line.setStyleSheet( " background-color: %s; " % self.line_color )

    def save_data(self):
        self.data.line_color = self.line_color
        self.data.name = self.name.text()
        self.data.Z1.setText(self.Z1.text())
        self.data.Z2.setText(self.Z2.text())
        self.data.X1.setText(self.X1.text())
        self.data.Y1.setText(self.Y1.text())
        self.data.X2.setText(self.X2.text())
        self.data.Y2.setText(self.Y2.text())
        self.data.dg.setText(self.dg.text())
        self.data.dl.setText(self.dl.text())
        self.data.da.setText(self.da.text())

        self.close()
        self.setPos((self.data.X1.number_gui,self.data.Y1.number_gui,self.data.X2.number_gui,self.data.Y2.number_gui))
        self.setCrl()
        self.setListName()

    def show(self, *args, **kwargs):
        try:
            self.name.setText(self.data.name)
            self.line_color = self.data.line_color if self.data.line_color != '' else QColor("black").name()
            self.line.setStyleSheet( " background-color: %s; " % self.line_color )
            self.Z1.setText(self.data.Z1.text)
            self.Z2.setText(self.data.Z2.text)
            self.dg.setText(self.data.dg.text)
            self.dl.setText(self.data.dl.text)
            self.da.setText(self.data.da.text)

            self.InitCords()

            self.X1.setText(self.data.X1.text)
            self.Y1.setText(self.data.Y1.text)
            self.X2.setText(self.data.X2.text)
            self.Y2.setText(self.data.Y2.text)
            

        except Exception as ex:
            print(ex)
        
        QWidget.show(self, *args, **kwargs)


class CalcAreaH(QWidget):
    def __init__(self,setCrl,getPos,setPos,parent=None, data=None):
        super(CalcAreaH,self).__init__(parent)
        self.setCrl = setCrl
        self.getPos = getPos
        self.setPos = setPos

        self.setListName = lambda: 0

        self.setFixedSize(320,250)

        self.setWindowTitle("Горизонтальная область")
        HspacerItem = [QSpacerItem(2, 2, QSizePolicy.Expanding, QSizePolicy.Minimum) for i in range(2)]
        VspacerItem = [QSpacerItem(2, 2, QSizePolicy.Minimum, QSizePolicy.Expanding) for i in range(2)]

        self.data = MenuData("horizontal_area") if data is None else data
        self.data.setParent(self)

        self.name = QLineEdit()
        BoxLayoutB1 = QVBoxLayout()
        BoxLayoutB1.addWidget(QLabel("Название"))
        BoxLayoutB1.addWidget(self.name)

        BoxLayout1 = QHBoxLayout()
        self.line = QPushButton()
        self.line.setFixedWidth(23)
        self.line_color = QColor("black").name()
        self.line.setStyleSheet( " background-color: %s; " % self.line_color )
        self.line.clicked.connect(self.getColor)

        BoxLayout1.addWidget(QLabel("Цвет линии:"))
        BoxLayout1.addWidget(self.line)
        BoxLayout1.addItem(HspacerItem[0])

        BoxLayoutB1.addLayout(BoxLayout1)

        grid_layout = QGridLayout()

        self.Z = QLineEdit()
        self.Z.setValidator(MyValidator("duble",self.Z,minus=False))
        grid_layout.addWidget(QLabel("Z, м:"),0,0)
        grid_layout.addWidget(self.Z,0,1)

        self.X1 = QLineEdit()
        self.X1.setValidator(MyValidator("duble",self.X1,minus=True))
        grid_layout.addWidget(QLabel("X1, м:"),1,0)
        grid_layout.addWidget(self.X1,1,1)

        self.Y1 = QLineEdit()
        self.Y1.setValidator(MyValidator("duble",self.Y1,minus=True))
        grid_layout.addWidget(QLabel("Y1, м:"),2,0)
        grid_layout.addWidget(self.Y1,2,1)

        self.X2 = QLineEdit()
        self.X2.setValidator(MyValidator("duble",self.X2,minus=True))
        grid_layout.addWidget(QLabel("X2, м:"),3,0)
        grid_layout.addWidget(self.X2,3,1)

        self.Y2 = QLineEdit()
        self.Y2.setValidator(MyValidator("duble",self.Y2,minus=True))
        grid_layout.addWidget(QLabel("Y2, м:"),4,0)
        grid_layout.addWidget(self.Y2,4,1)

        self.dg = QLineEdit()
        self.dg.setValidator(MyValidator("duble",self.dg,minus=False))
        grid_layout.addWidget(QLabel("Шаг сетки расчета, м:"),0,2)
        grid_layout.addWidget(self.dg,0,3)

        self.dl = QLineEdit()
        self.dl.setValidator(MyValidator("duble",self.dl,minus=False))
        grid_layout.addWidget(QLabel("dl проводника, м:"),1,2)
        grid_layout.addWidget(self.dl,1,3)

        self.da = QLineEdit()
        self.da.setValidator(MyValidator("duble",self.da,minus=False))
        grid_layout.addWidget(QLabel("da реактора, \u00B0:"),2,2)
        grid_layout.addWidget(self.da,2,3)


        self.ok = QPushButton("Ok")
        self.ok.clicked.connect(self.save_data)
        self.cancel = QPushButton("Отмена")
        self.cancel.clicked.connect(self.close)
        BoxLayoutB6 = QHBoxLayout()
        BoxLayoutB6.addItem(HspacerItem[1])
        BoxLayoutB6.addWidget(self.ok)
        BoxLayoutB6.addWidget(self.cancel)

        BoxLayoutB7 = QVBoxLayout()
        BoxLayoutB7.addLayout(BoxLayoutB1)
        BoxLayoutB7.addLayout(grid_layout)
        BoxLayoutB7.addLayout(BoxLayoutB6)

        self.setLayout(BoxLayoutB7)

        self.InitCords()


    def InitCords(self):
        cord = self.getPos()
        self.data.X1.setNumber_gui(cord[0])
        self.data.Y1.setNumber_gui(cord[1])
        self.data.X2.setNumber_gui(cord[2])
        self.data.Y2.setNumber_gui(cord[3])
        #print(self.data.X1.text,self.data.Y1.text,self.data.X2.text,self.data.Y2.text)

    def getColor(self):
        color = QColorDialog.getColor(initial=QColor(self.line_color),parent=self,\
                    title="Цвет контура",options=QColorDialog.ShowAlphaChannel)
        self.line_color = color.name()
        self.line.setStyleSheet( " background-color: %s; " % self.line_color )

    def save_data(self):
        self.data.line_color = self.line_color
        self.data.name = self.name.text()
        self.data.Z.setText(self.Z.text())
        self.data.X1.setText(self.X1.text())
        self.data.Y1.setText(self.Y1.text())
        self.data.X2.setText(self.X2.text())
        self.data.Y2.setText(self.Y2.text())
        self.data.dg.setText(self.dg.text())
        self.data.dl.setText(self.dl.text())
        self.data.da.setText(self.da.text())

        #print(self.data.X1.text,self.data.Y1.text,self.data.X2.text,self.data.Y2.text)

        self.close()
        self.setPos((self.data.X1.number_gui,self.data.Y1.number_gui,self.data.X2.number_gui,self.data.Y2.number_gui))
        self.setCrl()
        self.setListName()

    def show(self, *args, **kwargs):
        try:
            self.name.setText(self.data.name)
            self.line_color = self.data.line_color if self.data.line_color != '' else QColor("black").name()
            self.line.setStyleSheet( " background-color: %s; " % self.line_color )
            self.Z.setText(self.data.Z.text)
            self.dg.setText(self.data.dg.text)
            self.dl.setText(self.data.dl.text)
            self.da.setText(self.data.da.text)

            self.InitCords()

            self.X1.setText(self.data.X1.text)
            self.Y1.setText(self.data.Y1.text)
            self.X2.setText(self.data.X2.text)
            self.Y2.setText(self.data.Y2.text)
            

        except Exception as ex:
            print(ex)
        
        QWidget.show(self, *args, **kwargs)


class Conductor(QWidget):
    def __init__(self,setCrl,getPos,setPos,parent=None, data= None):
        super(Conductor,self).__init__(parent)
        self.setCrl = setCrl
        self.getPos = getPos
        self.setPos = setPos

        self.setListName = lambda: 0

        self.setFixedSize(620,360)

        self.setWindowTitle("Проводник")
        HspacerItem = [QSpacerItem(2, 2, QSizePolicy.Expanding, QSizePolicy.Minimum) for i in range(2)]
        VspacerItem = [QSpacerItem(2, 2, QSizePolicy.Minimum, QSizePolicy.Expanding) for i in range(2)]

        self.data = MenuData("conductor") if data is None else data
        self.data.setParent(self)
        self.trig = (data is None)

        self.name = QLineEdit()
        BoxLayoutB1 = QVBoxLayout()
        BoxLayoutB1.addWidget(QLabel("Название"))
        BoxLayoutB1.addWidget(self.name)

        BoxLayout1 = QHBoxLayout()
        self.line = QPushButton()
        self.line.setFixedWidth(23)
        self.line_color = QColor("black").name()
        self.line.setStyleSheet( " background-color: %s; " % self.line_color )
        self.line.clicked.connect(self.getColor)

        BoxLayout1.addWidget(QLabel("Цвет линии:"))
        BoxLayout1.addWidget(self.line)
        BoxLayout1.addItem(HspacerItem[0])

        BoxLayoutB1.addLayout(BoxLayout1)

        BoxLayout2 = QVBoxLayout()
        BoxLayout3 = QVBoxLayout()
        BoxLayout4 = QVBoxLayout()
        BoxLayout5 = QHBoxLayout()
        BoxLayoutB2 = QHBoxLayout()
        

        self.I = QLineEdit()
        self.I.setValidator(MyValidator("duble",self.I,minus=False))
        BoxLayout2.addWidget(QLabel("Действующий ток, А:"))
        BoxLayout3.addWidget(self.I)

        self.deg = QLineEdit()
        self.deg.setValidator(MyValidator("duble",self.deg,minus=True))
        BoxLayout2.addWidget(QLabel("Фаза тока, \u00B0:"))
        BoxLayout3.addWidget(self.deg)

        self.table_cord = QTableWidget()
        self.table_cord.setColumnCount(3)
        self.table_cord.setColumnWidth(0,70)
        self.table_cord.setColumnWidth(1,70)
        self.table_cord.setColumnWidth(2,70)
        self.table_cord.setHorizontalHeaderLabels(["x","y","z"])
        self.table_cord.setItemDelegate(DownloadDelegate("cord",self))
        BoxLayout2.addWidget(QLabel("Координаты:"))
        BoxLayout2.addItem(VspacerItem[0])
        BoxLayout3.addWidget(self.table_cord)
        
        self.check_fmax = QCheckBox("Провисание")
        self.check_fmax.stateChanged.connect(self.check_fmax_event)

        self.d_zp = QSpinBox()
        self.d_zp.setRange(2,999)
        self.d_zp.setSingleStep(1)
        #self.d_zp.setSuffix(" м")
        self.d_zp.setValue(2)
        self.d_zp.editingFinished.connect(self.ResizeTables)
        BoxLayout6 = QHBoxLayout()
        BoxLayout6.addWidget(self.check_fmax)
        BoxLayout6.addWidget(self.d_zp)

        BoxLayout4.addLayout(BoxLayout6)

        self.fmax = QLineEdit()
        self.fmax.setValidator(MyValidator("duble",self.I,minus=False))

        self.btn_fmax = QPushButton("Всем")
        self.btn_fmax.clicked.connect(self.Set_fmax)
        BoxLayout5.addWidget(self.btn_fmax)
        BoxLayout5.addWidget(self.fmax)
        BoxLayout4.addLayout(BoxLayout5)

        self.table_fmax = QTableWidget()
        self.table_fmax.setColumnCount(3)
        self.table_fmax.setColumnWidth(0,70)
        self.table_fmax.setColumnWidth(1,70)
        self.table_fmax.setColumnWidth(2,70)
        self.table_fmax.setHorizontalHeaderLabels(["n","k","fmax"])
        self.disable = {"table2":False}
        self.table_fmax.setItemDelegate(DownloadDelegate("fmax",self,self.disable))

        BoxLayout4.addWidget(self.table_fmax)

        grid_layout = QGridLayout()
        grid_layout.addLayout(BoxLayout2,0,0)
        grid_layout.addLayout(BoxLayout3,0,1)
        grid_layout.addLayout(BoxLayout4,0,2)

        self.ok = QPushButton("Ok")
        self.ok.clicked.connect(self.save_data)
        self.cancel = QPushButton("Отмена")
        self.cancel.clicked.connect(self.close)
        BoxLayoutB6 = QHBoxLayout()
        BoxLayoutB6.addItem(HspacerItem[1])
        BoxLayoutB6.addWidget(self.ok)
        BoxLayoutB6.addWidget(self.cancel)

        BoxLayoutB7 = QVBoxLayout()
        BoxLayoutB7.addLayout(BoxLayoutB1)
        BoxLayoutB7.addLayout(grid_layout)
        BoxLayoutB7.addLayout(BoxLayoutB6)

        self.setLayout(BoxLayoutB7)

        
        self.fmax.setReadOnly(True)

        self.InitCords()

    def InitCords(self):
        self.get_table_cord = self.getPos()
        self.data.tbl_XY.setNumber_gui(self.get_table_cord)
        if self.trig:
            self.data.tbl_Z.setText([""]*len(self.get_table_cord))
            self.data.tbl_fmax.setText([""]*len(self.get_table_cord))
            self.trig = False
  
    def ResizeTables(self):
        try:
            new_rows = self.d_zp.value()
            self.table_cord.setRowCount(new_rows)
            self.table_fmax.setRowCount(new_rows-1)

            if new_rows>self.old_rows:
                x = float(self.table_cord.item(self.old_rows-1,0).text())
                y = float(self.table_cord.item(self.old_rows-1,1).text())
                
                for i in range(self.old_rows,new_rows):
                    x+=1
                    self.table_cord.setItem(i,0, QTableWidgetItem(str(round(x,3))))
                    self.table_cord.setItem(i,1, QTableWidgetItem(str(y)))
                    self.table_cord.setItem(i,2, QTableWidgetItem(("")))

                for i in range(self.old_rows-1,new_rows-1):
                    self.table_fmax.setItem(i,0, QTableWidgetItem(str(i+1)))
                    self.table_fmax.setItem(i,1, QTableWidgetItem(str(i+2)))
                    self.table_fmax.setItem(i,2, QTableWidgetItem(("")))

            self.old_rows = new_rows
        except Exception as ex:
            print(ex)

    def getColor(self):
            color = QColorDialog.getColor(initial=QColor(self.line_color),parent=self,\
                        title="Цвет контура",options=QColorDialog.ShowAlphaChannel)
            self.line_color = color.name()
            self.line.setStyleSheet( " background-color: %s; " % self.line_color )

    def save_data(self):
        try:
            self.data.line_color = self.line_color
            self.data.name = self.name.text()
            self.data.I.setText(self.I.text())
            self.data.deg.setText(self.deg.text())
            self.data.lbl_fmax.setText(self.fmax.text())
            self.data.chck_fmax = True if self.check_fmax.checkState()==Qt.Checked else False

            self.data.tbl_XY.setText([[self.table_cord.item(i, 0).text(),
                                            self.table_cord.item(i, 1).text()] for i in range(self.old_rows)])

            self.data.tbl_Z.setText([self.table_cord.item(i, 2).text() for i in range(self.old_rows)])

            self.data.tbl_fmax.setText([self.table_fmax.item(i, 2).text() for i in range(self.old_rows-1)])
            
            self.close()
            self.setPos(self.data.tbl_XY.number_gui)
            self.setCrl()
            self.setListName()
        except Exception as ex:
            print("save_data",ex)

    def show(self, *args, **kwargs):
        try:
            self.name.setText(self.data.name)
            self.line_color = self.data.line_color if self.data.line_color != '' else QColor("black").name()
            self.line.setStyleSheet( " background-color: %s; " % self.line_color )
            self.I.setText(self.data.I.text)
            self.deg.setText(self.data.deg.text)

            self.get_table_cord = self.getPos()

            self.cord_col = len(self.get_table_cord)
            self.old_rows = self.cord_col

            self.data.tbl_XY.setNumber_gui(self.get_table_cord)

            self.d_zp.setValue(self.cord_col)

            self.table_cord.setRowCount(self.cord_col)

            self.table_fmax.setRowCount(self.cord_col-1)

            tbl_XY = self.data.tbl_XY.text
            tbl_Z = self.data.tbl_Z.text
            tbl_fmax = self.data.tbl_fmax.text

            for i in range(self.cord_col):
                self.table_cord.setItem(i,0, QTableWidgetItem(tbl_XY[i][0]))
                self.table_cord.setItem(i,1, QTableWidgetItem(tbl_XY[i][1]))
                self.table_cord.setItem(i,2, QTableWidgetItem(tbl_Z[i]))

            for i in range(self.cord_col-1):
                self.table_fmax.setItem(i,0, QTableWidgetItem(str(i+1)))
                self.table_fmax.setItem(i,1, QTableWidgetItem(str(i+2)))
                self.table_fmax.setItem(i,2, QTableWidgetItem(tbl_fmax[i]))

        except Exception as ex:
            print(ex)
        
        QWidget.show(self, *args, **kwargs)

    def check_fmax_event(self,state):
        if state == Qt.Checked:
            self.disable["table2"] = True
            self.fmax.setReadOnly(False)
        else:
            self.disable["table2"] = False
            self.fmax.setReadOnly(True)

    def Set_fmax(self):
        text = self.fmax.text()
        for i in range(self.cord_col-1):
            self.table_fmax.setItem(i,2, QTableWidgetItem(text))





class Reactor(QWidget):
    def __init__(self,setCrl,getPos,setPos, parent=None, data=None):
        super(Reactor,self).__init__(parent)

        self.setFixedSize(620,240)
        self.setCrl = setCrl
        self.getPos = getPos
        self.setPos = setPos
        self.setWindowTitle("Реактор")
        self.setListName = lambda: 0
        
        HspacerItem = [QSpacerItem(2, 2, QSizePolicy.Expanding, QSizePolicy.Minimum) for i in range(2)]
        #VspacerItem = QSpacerItem(2, 2, QSizePolicy.Minimum, QSizePolicy.Expanding)
        
        self.data = MenuData("reactor") if data is None else data
        self.data.setParent(self)

        BoxLayout1 = QHBoxLayout()

        self.name = QLineEdit()
        BoxLayoutB1 = QVBoxLayout()
        BoxLayoutB1.addWidget(QLabel("Название"))
        BoxLayoutB1.addWidget(self.name)

        self.body = QPushButton()
        self.body.setFixedWidth(23)
        self.body_color = QColor("red").name()
        self.body.setStyleSheet( " background-color: %s; " % self.body_color )
        self.body.clicked.connect(lambda:self.getColor(1))

        self.line = QPushButton()
        self.line.setFixedWidth(23)
        self.line_color = QColor("black").name()
        self.line.setStyleSheet( " background-color: %s; " % self.line_color )
        self.line.clicked.connect(lambda:self.getColor(2))

        BoxLayout1.addWidget(QLabel("Цвет заливки:"))
        BoxLayout1.addWidget(self.body)
        BoxLayout1.addWidget(QLabel("Цвет контура:"))
        BoxLayout1.addWidget(self.line)
        BoxLayout1.addItem(HspacerItem[0])

        BoxLayoutB1.addLayout(BoxLayout1)

        BoxLayout2 = QVBoxLayout()
        BoxLayout3 = QVBoxLayout()
        BoxLayoutB2 = QHBoxLayout()
        

        self.I = QLineEdit()
        self.I.setValidator(MyValidator("duble",self.I,minus=False))
        BoxLayout2.addWidget(QLabel("Действующий ток, А:"))
        BoxLayout3.addWidget(self.I)

        self.deg = QLineEdit()
        self.deg.setValidator(MyValidator("duble",self.deg,minus=True))
        BoxLayout2.addWidget(QLabel("Фаза тока, \u00B0:"))
        BoxLayout3.addWidget(self.deg)

        self.X = QLineEdit()
        self.X.setValidator(MyValidator("duble",self.X,minus=True))
        BoxLayout2.addWidget(QLabel("X, м:"))
        BoxLayout3.addWidget(self.X)

        self.Y = QLineEdit()
        self.Y.setValidator(MyValidator("duble",self.Y,minus=True))
        BoxLayout2.addWidget(QLabel("Y, м:"))
        BoxLayout3.addWidget(self.Y)

        self.Z = QLineEdit()
        self.Z.setValidator(MyValidator("duble",self.Z,minus=False))
        BoxLayout2.addWidget(QLabel("Z, м:"))
        BoxLayout3.addWidget(self.Z)

        BoxLayoutB2.addLayout(BoxLayout2)
        BoxLayoutB2.addLayout(BoxLayout3)

        BoxLayout4 = QVBoxLayout()
        BoxLayout5 = QVBoxLayout()
        BoxLayoutB3 = QHBoxLayout()

        

        self.Rnar = QLineEdit()
        self.Rnar.setValidator(MyValidator("duble",self.Rnar,minus=False))
        BoxLayout4.addWidget(QLabel("Внешний радиус, м:"))
        BoxLayout5.addWidget(self.Rnar)

        self.Rvn = QLineEdit()
        self.Rvn.setValidator(MyValidator("duble",self.Rvn,minus=False))
        BoxLayout4.addWidget(QLabel("Внутренний радиус, м:"))
        BoxLayout5.addWidget(self.Rvn)

        self.H = QLineEdit()
        self.H.setValidator(MyValidator("duble",self.H,minus=False))
        BoxLayout4.addWidget(QLabel("Высота рекатора, м:"))
        BoxLayout5.addWidget(self.H)

        self.W = QLineEdit()
        self.W.setValidator(MyValidator("int",self.W,minus=False))
        BoxLayout4.addWidget(QLabel("Количество витков:"))
        BoxLayout5.addWidget(self.W)

        self.m = QLineEdit()
        self.m.setValidator(MyValidator("int",self.m,minus=False))
        BoxLayout4.addWidget(QLabel("Количество слоёв:"))
        BoxLayout5.addWidget(self.m)

        BoxLayoutB3 = QHBoxLayout()
        BoxLayoutB3.addLayout(BoxLayout4)
        BoxLayoutB3.addLayout(BoxLayout5)

        BoxLayout6 = QVBoxLayout()
        BoxLayout7 = QVBoxLayout()
        BoxLayout8 = QVBoxLayout()
        BoxLayout9 = QVBoxLayout()

        BoxLayout10 = QHBoxLayout()
        BoxLayout11 = QHBoxLayout()

        BoxLayout12 = QVBoxLayout()
        BoxLayout13 = QVBoxLayout()

        BoxLayout14 = QHBoxLayout()

        BoxLayoutB4 = QVBoxLayout()

        BoxLayout6.addWidget(QLabel("\u0394P, кВт:"))
        BoxLayout6.addWidget(QLabel("Q, Мвар:"))
        BoxLayout6.addWidget(QLabel("Uном, кВ:"))

        

        self.dP = QLineEdit()
        self.dP.setValidator(MyValidator("duble",self.dP,minus=False))
        self.Q = QLineEdit()
        self.Q.setValidator(MyValidator("duble",self.Q,minus=False))
        self.Unom = QLineEdit()
        self.Unom.setValidator(MyValidator("duble",self.Unom,minus=False))
        BoxLayout8.addWidget(self.dP)
        BoxLayout8.addWidget(self.Q)
        BoxLayout8.addWidget(self.Unom)

        BoxLayout10.addLayout(BoxLayout6)
        BoxLayout10.addLayout(BoxLayout8)
        BoxLayout12.addWidget(QLabel("Шунтирующий"))
        BoxLayout12.addLayout(BoxLayout10)

        BoxLayout14.addLayout(BoxLayout12)

        BoxLayout7.addWidget(QLabel("Жила:"))
        BoxLayout7.addWidget(QLabel("XL, Ом:"))
        BoxLayout7.addWidget(QLabel("Iном, А:"))

        self.met = QComboBox()
        self.met.addItems(["Алюминий","Медь"])
        self.Xl = QLineEdit()
        self.Xl.setValidator(MyValidator("duble",self.Xl,minus=False))
        self.Inom = QLineEdit()
        self.Inom.setValidator(MyValidator("duble",self.Inom,minus=False))
        BoxLayout9.addWidget(self.met)
        BoxLayout9.addWidget(self.Xl)
        BoxLayout9.addWidget(self.Inom)

        BoxLayout11.addLayout(BoxLayout7)
        BoxLayout11.addLayout(BoxLayout9)
        BoxLayout13.addWidget(QLabel("Токоограничивающий"))
        BoxLayout13.addLayout(BoxLayout11)

        BoxLayout14.addLayout(BoxLayout13)

        self.calc = QPushButton("Расч. кол. витков и слоёв")
        self.calc.clicked.connect(self.CalcReactorParam)
        
        BoxLayoutB4.addLayout(BoxLayout14)
        BoxLayoutB4.addWidget(self.calc)

        BoxLayoutB5 = QHBoxLayout()
        BoxLayoutB5.addLayout(BoxLayoutB2)
        BoxLayoutB5.addLayout(BoxLayoutB3)
        BoxLayoutB5.addLayout(BoxLayoutB4)
        
        self.ok = QPushButton("Ok")
        self.ok.clicked.connect(self.save_data)
        self.cancel = QPushButton("Отмена")
        self.cancel.clicked.connect(self.close)
        BoxLayoutB6 = QHBoxLayout()
        BoxLayoutB6.addItem(HspacerItem[1])
        BoxLayoutB6.addWidget(self.ok)
        BoxLayoutB6.addWidget(self.cancel)

        BoxLayoutB7 = QVBoxLayout()
        BoxLayoutB7.addLayout(BoxLayoutB1)
        BoxLayoutB7.addLayout(BoxLayoutB5)
        BoxLayoutB7.addLayout(BoxLayoutB6)

        self.setLayout(BoxLayoutB7)

        self.InitCords()

    def InitCords(self):
        d1,d2,d3 = self.getPos()
        self.data.X.setNumber_gui(d1)
        self.data.Y.setNumber_gui(d2)
        self.data.Rnar.setNumber_gui(d3)

    def getColor(self,key):
        if key==1:
            color = QColorDialog.getColor(initial=QColor(self.body_color),parent=self,\
                        title="Цвет заливки",options=QColorDialog.ShowAlphaChannel)
            self.body_color = color.name()
            self.body.setStyleSheet( " background-color: %s; " % self.body_color )
        elif key==2:
            color = QColorDialog.getColor(initial=QColor(self.line_color),parent=self,\
                        title="Цвет контура",options=QColorDialog.ShowAlphaChannel)
            self.line_color = color.name()
            self.line.setStyleSheet( " background-color: %s; " % self.line_color )

    def CalcReactorParam(self):
        Rnar = float(self.Rnar.text()) if self.Rnar.text() !='' else None
        Rvn = float(self.Rvn.text()) if self.Rvn.text() !='' else None
        H = float(self.H.text()) if self.H.text() !='' else None
        dP = float(self.dP.text()) if self.dP.text() !='' else None
        Q = float(self.Q.text()) if self.Q.text() !='' else None
        Xl = float(self.Xl.text()) if self.Xl.text() !='' else None
        Unom = float(self.Unom.text()) if self.Unom.text() !='' else None
        Inom = float(self.Inom.text()) if self.Inom.text() !='' else None
        met = self.met.currentText()
        rez = SolenParam(dP,met,Rnar,Rvn,H,50,Q,Unom,Xl,Inom)
        if rez != None:
            self.W.setText(str(rez[0]))
            self.m.setText(str(rez[1]))

    def save_data(self):
        try:
            self.data.name = self.name.text()
            self.data.body_color = self.body_color
            self.data.line_color = self.line_color
            self.data.I.setText(self.I.text())
            self.data.deg.setText(self.deg.text())
            self.data.X.setText(self.X.text())
            self.data.Y.setText(self.Y.text())
            self.data.Z.setText(self.Z.text())
            self.data.Rnar.setText(self.Rnar.text())
            self.data.Rvn.setText(self.Rvn.text())
            self.data.H.setText(self.H.text())
            self.data.W.setText(self.W.text())
            self.data.m.setText(self.m.text())
            self.data.dP.setText(self.dP.text())
            self.data.Q.setText(self.Q.text())
            self.data.Unom.setText(self.Unom.text())
            self.data.met = self.met.currentText()
            self.data.Xl.setText(self.Xl.text())
            self.data.Inom.setText(self.Inom.text())
            self.close()
            self.setPos((self.data.X.number_gui,self.data.Y.number_gui,self.data.Rnar.number_gui))
            self.setCrl()
            self.setListName()
        except Exception as ex:
            print(ex)

    def show(self, *args, **kwargs):
        try:
            self.name.setText(self.data.name)
            self.body_color = self.data.body_color if self.data.body_color != '' else QColor("red").name()
            self.body.setStyleSheet( " background-color: %s; " % self.body_color )
            self.line_color = self.data.line_color if self.data.line_color != '' else QColor("black").name()
            self.line.setStyleSheet( " background-color: %s; " % self.line_color )
            self.I.setText(self.data.I.text)
            self.deg.setText(self.data.deg.text)

            x11,y11,r11 = self.getPos()
            
            self.data.X.setNumber_gui(x11)
            self.data.Y.setNumber_gui(y11)
            self.data.Rnar.setNumber_gui(r11)

            self.X.setText(self.data.X.text)
            self.Y.setText(self.data.Y.text)
            self.Z.setText(self.data.Z.text)
            self.Rnar.setText(self.data.Rnar.text)
            self.Rvn.setText(self.data.Rvn.text)
            self.H.setText(self.data.H.text)
            self.W.setText(self.data.W.text)
            self.m.setText(self.data.m.text)
            self.dP.setText(self.data.dP.text)
            self.Q.setText(self.data.Q.text)
            self.Unom.setText(self.data.Unom.text)
            self.met.setCurrentText(self.data.met)
            self.Xl.setText(self.data.Xl.text)
            self.Inom.setText(self.data.I.text)
        except Exception as ex:
            print(ex)
        
        QWidget.show(self, *args, **kwargs)
    

        


if __name__ == '__main__':
    """ from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    ex = Save_Widget([],lambda a,b:print(a,b))
    ex.show()
    sys.exit(app.exec_()) """


        

        

        
        

