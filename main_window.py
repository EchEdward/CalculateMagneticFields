# pylint: disable=E0611
# pylint: disable=E1101

from PyQt5.QtGui import QBrush, QImage, QPixmap, QPainter, QPen, QCursor,QPolygonF, QWheelEvent,QColor, QMouseEvent,\
     QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QGraphicsScene, QGraphicsView, QAction,\
     QPushButton, QGridLayout, QApplication, QVBoxLayout, QHBoxLayout, QGraphicsEllipseItem, QGraphicsItem,\
     QGraphicsItemGroup,QGraphicsSceneMouseEvent, QListView, QSplitter, QFrame, QSizePolicy, QTreeView,\
     QHeaderView, QCheckBox, QComboBox, QFileDialog, QTabWidget, QTableWidget, QSpinBox, QLabel, QTableWidgetItem,\
     QColorDialog
from PyQt5.QtCore import Qt, QPoint, QLineF,QPointF, QEvent, QPersistentModelIndex, QModelIndex

from DrawObjects import GraphicsCircleItem,GraphicsLineItem,GraphicsPolylineItem, GraphicsRectItem, OneCalcCircle
from ObjectsMenu import DownloadDelegate, Save_Widget

from main_calculate import run_area_calc


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib
from matplotlib.ticker import FuncFormatter
import matplotlib.font_manager as fm
arial_font = fm.FontProperties(fname = "Fonts/arial.ttf")

import numpy as np
import scipy.interpolate
from functools import partial

import dxf

import sys
import os
import pickle

import inspect



class GraphicsView(QGraphicsView):
    def __init__(self,get_obj_for_resize):
        super().__init__()
        self.get_obj_for_resize = get_obj_for_resize
        self.current_scale = 1

    def wheelEvent(self, QWheelEvent):
        """ Событие скрола """
        #super(Screen, self).wheelEvent(QWheelEvent)
        wheelcounter = QWheelEvent.angleDelta()
        listObjectsDict, calcObjectsDict = self.get_obj_for_resize()

        if wheelcounter.y()==120:
            self.scale(1.25,1.25)
            self.current_scale*=1.25
            for obj in listObjectsDict.values():
                if obj[0] == "name":
                    obj[3].hndl*=0.8 
                    obj[3].updateHandlesPos()
                    

            for obj in calcObjectsDict.values():
                if obj[0] == "name":
                    obj[3].hndl*=0.8 
                    obj[3].updateHandlesPos()
                    

        elif wheelcounter.y()==-120:
            self.scale(0.8,0.8)
            self.current_scale*=0.8
            for obj in listObjectsDict.values():
                if obj[0] == "name":
                    obj[3].hndl*=1.25 
                    obj[3].updateHandlesPos()

            for obj in calcObjectsDict.values():
                if obj[0] == "name":
                    obj[3].hndl*=1.25 
                    obj[3].updateHandlesPos()




    def mousePressEvent(self, mouseEvent):
        if mouseEvent.button() == 4: # номер кнопки колёсика
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setInteractive(False)

            click = QMouseEvent(QEvent.GraphicsSceneMousePress,mouseEvent.pos(), Qt.LeftButton,\
                        Qt.LeftButton, Qt.NoModifier)
            self.mousePressEvent(click)

        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        super().mouseReleaseEvent(mouseEvent)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setInteractive(True)
        


class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        QGraphicsScene.__init__(self, parent)
        
        #s = [632.151407, 582.222388, 5719.943627162954, 2459.169672]
        #self.setSceneRect(s[0], s[1], s[2]-s[0], s[3]-s[1])

        
# subclass
class CheckableComboBox(QComboBox):
    # once there is a checkState set, it is rendered
    # here we assume default Unchecked
    def __init__(self,parent=None):
        super(CheckableComboBox, self).__init__(parent)
        self.title_text = "Слои"
        self.model().itemChanged.connect(self.itemChecked)
        self.setEditable(True)
        self.displayedText = self.lineEdit()
        self.displayedText.setText(self.title_text)
        self.displayedText.setReadOnly(True)
        self.isCheckFunc = False

    def addItem(self, item):
        super(CheckableComboBox, self).addItem(item)
        item = self.model().item(self.count()-1,0)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(Qt.Unchecked)

    def getItem(self,text):
        try:
            item = self.model().item(self.findText(text),0)
            return item
        except Exception as ex:
            print(ex)
            return None
    def setItemState(self, text, state):
        try:
            item = self.model().item(self.findText(text),0)
            item.setCheckState(Qt.Checked if state else Qt.Unchecked)
        except Exception as ex:
            print(ex)
            

    def paintEvent(self,ev):
        self.displayedText.setText(self.title_text)
        super().paintEvent(ev)

    def setCheckEvent(self,func):
        self.Func = func


    def itemChecked(self, item):
        if self.isCheckFunc:
            self.Func(item.text(),True if item.checkState()==Qt.Checked else False)

    def ShowNewObj(self,text):
        try:
            item = self.model().item(self.findText(text),0)
            self.Func(item.text(),True if item.checkState()==Qt.Checked else False)
        except Exception as ex:
            print(ex)

    def removeItem(self, text):
        self.model().removeRow(self.findText(text))


    """ def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked) """



        
        
    

class Screen(QMainWindow):
    def __init__(self):
        super().__init__()

        desktop = QApplication.desktop()
        wd = desktop.width()
        hg = desktop.height()
        ww = 1000
        wh = 500
        if ww>wd: ww = int(0.7*wd)
        if wh>hg: wh = int(0.7*hg)
        x = (wd-ww)//2
        y = (hg-wh)//2
        self.setGeometry(x, y, ww, wh)

        try:
            self.path_home = os.path.expanduser("~\\Desktop\\")
        except Exception:
            self.path_home = ""

        LeftPanelFrame = QFrame() 
        LeftPanelFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #LeftPanelFrame.setMinimumSize(QSize(0, 100))

        

        self.listObjects = QTreeView()
        self.calcObjects = QTreeView()

        self.listObjectsCheck = QCheckBox("Скрыть/показать")


        self.CheckListlayers = CheckableComboBox()
        self.CheckListlayers.setCheckEvent(self.OnOffLayers)

        self.CheckListAreas = CheckableComboBox()
        #self.CheckListAreas.setCheckEvent(self.OnOffLayers)
                
        
        ListObjectsHeader = QHeaderView(Qt.Horizontal)

        self.listObjects.header().resizeSection(0, 10)

        self.listObjects.doubleClicked.connect(self.OpenObjMenu)
        self.listObjects.clicked[QModelIndex].connect(self.SelectObjects)

        self.calcObjects.doubleClicked.connect(self.OpenCalcMenu)
        self.calcObjects.clicked[QModelIndex].connect(self.SelectCalc)

        BoxLayout2 = QHBoxLayout()
        BoxLayout2_1 = QVBoxLayout()
        BoxLayout2_1.addWidget(self.CheckListlayers)
        BoxLayout2_1.addWidget(self.listObjectsCheck)
        BoxLayout2_1.addWidget(self.listObjects)
        BoxLayout2_1.addWidget(self.CheckListAreas)
        BoxLayout2_1.addWidget(self.calcObjects)
        BoxLayout2.addLayout(BoxLayout2_1)
        LeftPanelFrame.setLayout(BoxLayout2) 


        SceneFrame = QFrame() 
        SceneFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 
        #SceneFrame.setMinimumSize(QSize(0, 100))

        self.listObjectsDict = {}

        self.scene = GraphicsScene(self) #QGraphicsScene()
        self.view = GraphicsView(self.get_obj_for_resize)
        self.view.setMouseTracking(True)
 

        self.view.setAlignment( Qt.AlignLeft | Qt.AlignTop )
 
        self.view.setScene(self.scene)

        self.view.current_scale = 1

        self.tab = QTabWidget()
        self.tab.addTab(self.view,"Модель")
        self.fig = plt.figure(dpi=75)
        self.Canv = FigureCanvas(self.fig)
        


        self.table_contour = QTableWidget()
        self.table_contour.setColumnCount(3)
        #self.table_contour.setRowCount(2)
        self.table_contour.setColumnWidth(0,30)
        self.table_contour.setColumnWidth(1,70)
        self.table_contour.setColumnWidth(2,70)
        self.table_contour.setHorizontalHeaderLabels(["","H, А/м","Цвет"])
        self.table_contour.setMaximumWidth(200)
        self.table_contour.setItemDelegate(DownloadDelegate("contour",self))
        self.table_contour.cellClicked[int,int].connect(self.SetColorTContour) #partial(self.OpenFig,2)
        self.table_contour.cellChanged.connect(self.SetCountur)
        self.d_contur = {}
        self.make_contur = None
        self.old_rows = 0

        self.tbc_rows = QSpinBox()
        self.tbc_rows.setRange(0,999)
        self.tbc_rows.setSingleStep(1)
        self.tbc_rows.setValue(0)
        self.tbc_rows.editingFinished.connect(self.ResizeTablesContour)

        BoxLayout3 = QVBoxLayout()
        BoxLayout3.addWidget(QLabel("Линии уровня"))
        BoxLayout3.addWidget(self.tbc_rows)
        BoxLayout3.addWidget(self.table_contour)

        BoxLayout4 = QHBoxLayout()
        BoxLayout4.addWidget(self.Canv,1)
        BoxLayout4.addLayout(BoxLayout3,0)
        Rez_widget = QWidget()
        Rez_widget.setLayout(BoxLayout4)
        self.tab.addTab(Rez_widget,"Результаты")


        BoxLayout1 = QHBoxLayout()
        BoxLayout1.addWidget(self.tab)
        SceneFrame.setLayout(BoxLayout1) 

        
 
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Файл')

        OpenDXFAction = QAction('Открыть .dxf', self)
        OpenDXFAction.setShortcut('Ctrl+O')
        OpenDXFAction.triggered.connect(self.load_dxf_file) 
        fileMenu.addAction(OpenDXFAction)

        OpenSelfAction = QAction('Открыть', self)
        #OpenSelfAction.setShortcut('Ctrl+O')
        OpenSelfAction.triggered.connect(self.LoadCalcData) 
        fileMenu.addAction(OpenSelfAction)

        SaveObjAction = QAction('Сохранить', self)
        SaveObjAction.setShortcut('Ctrl+S')
        SaveObjAction.triggered.connect(self.SaveCalcData) 
        fileMenu.addAction(SaveObjAction)


        RunCalcAction = QAction('Расчёт', self)
        RunCalcAction.setShortcut('Ctrl+R')
        RunCalcAction.triggered.connect(lambda:self.Run_calc_area(tc=None)) 
        fileMenu.addAction(RunCalcAction)
 
        #self.button = QPushButton('Сохранить', self)
        #self.button.clicked.connect()

        CorrectMenu = menubar.addMenu('&Правка')

        NewReactorAction = QAction('Добавить реактор', self)
        NewReactorAction.setShortcut('Ctrl+R')
        NewReactorAction.triggered.connect(lambda: self.AddObj("reactor")) 
        CorrectMenu.addAction(NewReactorAction)

        NewWireAction = QAction('Добавить шину', self)
        NewWireAction.setShortcut('Ctrl+W')
        NewWireAction.triggered.connect(lambda: self.AddObj("conductor")) 
        CorrectMenu.addAction(NewWireAction)

        DelObjectAction = QAction('Удалить объект', self)
        DelObjectAction.setShortcut('Ctrl+D')
        DelObjectAction.triggered.connect(self.DelObj) 
        CorrectMenu.addAction(DelObjectAction)

        NewHorizCalcAction = QAction('Горизонтальная область расчёта', self)
        NewHorizCalcAction.setShortcut('Ctrl+H')
        NewHorizCalcAction.triggered.connect(lambda: self.AddCalcObj("H_calc_area")) 
        CorrectMenu.addAction(NewHorizCalcAction)

        NewVertCalcAction = QAction('Вертикальная область расчёта', self)
        NewVertCalcAction.setShortcut('Ctrl+G')
        NewVertCalcAction.triggered.connect(lambda: self.AddCalcObj("V_calc_area")) 
        CorrectMenu.addAction(NewVertCalcAction)

        NewPointCalcAction = QAction('Расчётная точка в пространстве', self)
        NewPointCalcAction.setShortcut('Ctrl+J')
        NewPointCalcAction.triggered.connect(lambda: self.AddCalcObj("O_calc_point")) 
        CorrectMenu.addAction(NewPointCalcAction)

        DelCalcAction = QAction('Удалить параметры расчёта', self)
        DelCalcAction.setShortcut('Ctrl+K')
        DelCalcAction.triggered.connect(self.DelCalcObj) 
        CorrectMenu.addAction(DelCalcAction)


        ResultMenu = menubar.addMenu('&Результаты')

        SaveInDXFAction = QAction('Сохранить в dxf', self)
        #SaveInDXFAction.setShortcut('Ctrl+R')
        SaveInDXFAction.triggered.connect(self.SaveInDXFstart) 
        ResultMenu.addAction(SaveInDXFAction)

        SavePlotAction = QAction('Сохранить график', self)
        #SaveInDXFAction.setShortcut('Ctrl+R')
        SavePlotAction.triggered.connect(self.SavePlot) 
        ResultMenu.addAction(SavePlotAction)


        Splitter1 = QSplitter(Qt.Horizontal) 
        Splitter1.addWidget(LeftPanelFrame)
        Splitter1.addWidget(SceneFrame)
        Splitter1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        Splitter1.setStretchFactor(1, 4) 
 
        

        
        vbox = QVBoxLayout(self)
        vbox.addWidget(Splitter1)
        self.central_widget = QWidget()
        self.central_widget.setLayout(vbox)
        self.setCentralWidget(self.central_widget) 

        self.listObjectsDict = {}
        self.linksObjectsDict = {}
        self.calcObjectsDict = {}
        self.LayersDict = {}
        self.LayersDict["Main"] = [True,set()]
        self.CheckListlayers.addItem("Main")
        self.CheckListlayers.setItemState("Main",True)
        self.CheckListlayers.isCheckFunc = True
        self.obj_id=0
        self.calc_id=0

        self.listObjectsModel = QStandardItemModel(0, 2)
        self.listObjectsModel.itemChanged.connect(self.ChangeCheckObjects)
        self.listObjectsModel.setHorizontalHeaderLabels(["","Имя"])
        self.current_obj_index = None

        self.listObjects.setModel(self.listObjectsModel)
        self.listObjects.setColumnWidth(0, 40)

        self.calcObjectsModel = QStandardItemModel(0, 2)
        self.calcObjectsModel.itemChanged.connect(self.ChangeCheckCalc)
        self.calcObjectsModel.setHorizontalHeaderLabels(["","Имя"])
        self.current_calc_index = None

        self.calcObjects.setModel(self.calcObjectsModel)
        self.calcObjects.setColumnWidth(0, 40)

    def SavePlot(self):
        try:
            fname = QFileDialog.getSaveFileName(self, 'Сохранить файл', self.path_home,'*.jpg;;*.png;;*.pdf;;*.svg;;*.eps')

            #self.fig.set_size_inches(4, 4,forward=True) # Изменяем размер сохраняемого графика
            self.fig.savefig(fname[0], format=fname[1][2:], dpi=300) # Cохраняем графики
        except Exception as ex:
            print(ex)


    def SaveInDXFstart(self):
        sp = []
        for j,i in self.calcObjectsDict.items():
            if i[0]=="name":
                if i[3].menu.data["obj_type"] != "V_calc_area":
                    sp.append([j,i[3].menu.data["name"],i[3].menu.data["obj_type"]])


        self.w = Save_Widget(sp,lambda a,b:self.SaveInDXFfinish(a,b))
        self.w.show()
        


    def SaveInDXFfinish(self,sp,tsf):
        
        fname = QFileDialog.getSaveFileName(self, 'Сохранить файл', self.path_home,'*.dxf')[0]
        
        #print(sp)
        #print(tsf)

        self.Run_calc_area(tc=1,dnn=sp,fname=(fname,tsf))
        

                    


    def SetColorTContour(self,row,col):
        if col == 2:
            color = QColorDialog.getColor(initial=self.table_contour.item(row,col).background().color(),\
                                            parent=self,title="Цвет контура",options=QColorDialog.ShowAlphaChannel)

            if color.isValid():
                self.table_contour.item(row,2).setBackground(color)
                #print(color.greenF())
                #print(color.name())
                self.SetCountur(row,1)

    def SetCountur(self,row,col,tc=None):
        state = self.table_contour.item(row,0).checkState()
        sp_levels = []
        #ax1.clabel(cs)
        #countur_date = cs.allsegs

        if state == Qt.Checked:
            if col==0:
                self.d_contur[row][0] = True

            try:
                if col==0 or col==1:
                    c = self.table_contour.item(row,2).background().color()
                    l = self.table_contour.item(row,1).text()

                    if self.d_contur[row][1] is None and l!='' and self.make_contur is not None:
                        self.d_contur[row][1] = self.make_contur(float(l),c.name())  #= lambda l, c: ax1.contour(xi, zi, hi, levels = l, colors = c )

                        if tc is None:
                            self.Canv.draw()
                        elif tc == 1:
                            sp_levels.append([l,(c.red(),c.green(),c.blue()),self.d_contur[row][1].allsegs])


                    elif self.d_contur[row][1] is not None and l!='' and self.make_contur is not None:
                        ds = self.make_contur(float(l),c.name())

                        if tc is None:
                            self.Canv.draw()

                        for c in self.d_contur[row][1].collections:
                            c.remove()
                        
                        if tc is None:
                            self.Canv.draw()
                        elif tc == 1:
                            sp_levels.append([l,(c.red(),c.green(),c.blue()),ds.allsegs])

                        self.d_contur[row][1] = ds

            except Exception as ex:
                print(ex)
                 
        elif state == Qt.Unchecked and col==0:
            self.d_contur[row][0] = False
            if self.d_contur[row][1] is not None:
                for c in self.d_contur[row][1].collections:
                    c.remove()
                self.d_contur[row][1] = None
                self.Canv.draw()

        if tc == 1:
            return sp_levels 


    def ResizeTablesContour(self):
        try:
            new_rows = self.tbc_rows.value()
            
            if new_rows>self.old_rows:
                #x = float(self.table_cord.item(self.old_rows-1,0).text())
                #y = float(self.table_cord.item(self.old_rows-1,1).text())
                self.table_contour.setRowCount(new_rows)
                for i in range(self.old_rows,new_rows):
                    self.d_contur[i] = [False, None]
                    item = QTableWidgetItem("")
                    item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    item.setCheckState(Qt.Unchecked)
                    self.table_contour.setItem(i,0, item)
                    self.table_contour.setItem(i,1, QTableWidgetItem(""))
                    self.table_contour.setItem(i,2, QTableWidgetItem(""))
                    self.table_contour.item(i,2).setBackground(QColor(255,0,0))
                     
            elif new_rows<self.old_rows:
                for i in range(new_rows,self.old_rows):
                    self.table_contour.item(i,0).setCheckState(Qt.Unchecked)
                    del self.d_contur[i]

                self.table_contour.setRowCount(new_rows)


            self.old_rows = new_rows
        except Exception as ex:
            print(ex)

    def ShowCanvas(self,SpaceCord,H_area,area_calc,z,tp, tc=None):
        self.fig.clear()
        sp_levels = []
     
        if tp == "H_calc_area":
            X,Y = SpaceCord

            xi, yi = np.linspace(X.min(), X.max(), 100), np.linspace(Y.min(), Y.max(), 100)
            xi, yi = np.meshgrid(xi, yi)

            rbf = scipy.interpolate.Rbf(X, Y, H_area, function='linear')
            zi = rbf(xi, yi)

            ax = self.fig.add_subplot(111) #
            

            im=ax.imshow(zi, vmin=H_area.min(), vmax=H_area.max(), origin='lower',extent=[X.min(), X.max(), Y.min(), Y.max()]) #
            cl = self.fig.colorbar(im)
            cl.set_label('H, А/м',verticalalignment = "top", x=-20) #, rotation=270 #,position=(20,0)

            self.make_contur = lambda l, c: ax.contour(xi, yi, zi, levels = l, colors = c )

            for k in self.d_contur:
                self.d_contur[k][1]=None
                if tc is None:
                    self.SetCountur(k,0)
                elif tc == 1:
                    sp_levels += self.SetCountur(k,0,tc=tc)

            
            
            ax.set_xlabel(u'X, м') # Подпись оси х ,fontsize=self.shr_gr
            ax.set_ylabel(u'Y, м') # Подпись оси у ,fontsize=self.shr_gr
            #ax.set_title("Тест\n") #,fontsize=self.shr_gr

            if tc is None:
                self.Canv.draw() # Выводим график в виджет
                self.tab.setCurrentIndex(1) # Делаем активной созданую закладку

            elif tc == 1:
                return sp_levels

        
        elif tp == "V_calc_area" and tc is None:
            X,Y,Z = SpaceCord

            if area_calc[2]-area_calc[0]>=area_calc[3]-area_calc[1]:
                 
                ax1 = self.fig.gca()
                
                
                # Создание графика
                xi, zi = np.linspace(X.min(), X.max(), 100), np.linspace(Z.min(), Z.max(), 100)
                xi, zi = np.meshgrid(xi, zi)

                rbf = scipy.interpolate.Rbf(X, Z, H_area, function='linear')
                hi = rbf(xi, zi)

                im = ax1.imshow(hi, vmin=H_area.min(), vmax=H_area.max(), origin='lower',extent=[X.min(), X.max(), Z.min(), Z.max()],aspect="auto") #
                self.make_contur = lambda l, c: ax1.contour(xi, zi, hi, levels = l, colors = c )

                for k in self.d_contur:
                    self.d_contur[k][1]=None
                    self.SetCountur(k,0)

                if area_calc[3]-area_calc[1]>0.05:
                    ax2 = ax1.twiny()
                    ax2.set_xlim([Y.min(),Y.max()])
                    ax2.set_xlabel(u'Y, м\n') # Подпись оси у ,fontsize=self.shr_gr
               
                ax1.set_xlabel(u'X, м') # Подпись оси х ,fontsize=self.shr_gr
                ax1.set_ylabel(u'Z, м') # Подпись оси у ,fontsize=self.shr_gr
                
            else:
                if area_calc[2]-area_calc[0]>0.05:
                    ax1 = self.fig.gca()
                    ax2 = ax1.twiny()
                else:
                    ax2 = self.fig.gca()

                xi, zi = np.linspace(Y.min(), Y.max(), 100), np.linspace(Z.min(), Z.max(), 100)
                xi, zi = np.meshgrid(xi, zi)

                rbf = scipy.interpolate.Rbf(Y, Z, H_area, function='linear')
                hi = rbf(xi, zi)

                im = ax2.imshow(hi, vmin=H_area.min(), vmax=H_area.max(), origin='lower',
                        extent=[Y.min(), Y.max(), Z.min(), Z.max()],aspect="auto")
                self.make_contur = lambda l, c: ax2.contour(xi, zi, hi, levels = l, colors = c)

                for k in self.d_contur:
                    self.d_contur[k][1]=None
                    self.SetCountur(k,0)
                
                if area_calc[2]-area_calc[0]>0.05:
                    ax1.set_xlim([X.min(),X.max()])
                    ax1.set_xlabel(u'X, м') 
                
                ax2.set_xlabel(u'Y, м\n')
                ax2.set_ylabel(u'Z, м') # Подпись оси у ,fontsize=self.shr_gr

            cl = self.fig.colorbar(im)
            cl.set_label('H, А/м',verticalalignment = "top", x=-20) #, rotation=270 #,position=(20,0)

            

            self.Canv.draw() # Выводим график в виджет

            self.tab.setCurrentIndex(1) 
        


    def Run_calc_area(self, tc=None, dnn=None,fname=None):
        lst = []
        if tc==1:
            sp_obj = []
        
        try:
            for i in self.listObjectsDict.values():
                if i[0]=="name":
                    if i[3].menu.data["obj_type"] == "reactor" and not i[4]:
                        x, y, r = i[3].getPos()
                        i[3].menu.data["X"], i[3].menu.data["Y"], i[3].menu.data['Rnar'] = str(round(x/1000,3)), str(round(y/1000,3)), str(round(r/1000,3))
                        lst.append(i[3].menu.data)

                        if tc==1:
                            sp_obj.append(["reactor",x, y, r])
                        
                    elif i[3].menu.data["obj_type"] == "conductor" and not i[4]:
                        cord = i[3].getPos()
                        for j in range(len(cord)):
                            i[3].menu.data["tbl_cord"][j][0] = str(round(cord[j][0]/1000,3))
                            i[3].menu.data["tbl_cord"][j][1] = str(round(-cord[j][1]/1000,3))
                        lst.append(i[3].menu.data)

                        if tc==1:
                            sp_obj.append(["conductor",cord])

            if tc is None:
                for j,i in self.calcObjectsDict.items():
                    if i[0]=="name":
                        if i[4]:
                            if i[3].menu.data["obj_type"] == "H_calc_area":
                                cord = i[3].getPos()
                                area_calc = [cord[0]/1000,-cord[3]/1000,cord[2]/1000,-cord[1]/1000]
                                dg = float(i[3].menu.data["dg"])
                                dl = float(i[3].menu.data["dl"])
                                da = float(i[3].menu.data["da"])
                                z = (float(i[3].menu.data["Z"]),)
                                tp = "H_calc_area"
                                break
                            elif i[3].menu.data["obj_type"] == "V_calc_area":
                                cord = i[3].getPos()
                                area_calc = [cord[0]/1000,-cord[3]/1000,cord[2]/1000,-cord[1]/1000]
                                dg = float(i[3].menu.data["dg"])
                                dl = float(i[3].menu.data["dl"])
                                da = float(i[3].menu.data["da"])
                                z = (float(i[3].menu.data["Z1"]),float(i[3].menu.data["Z2"]))
                                tp = "V_calc_area"
                                break

                            elif i[3].menu.data["obj_type"] == "O_calc_point":
                                cord = i[3].getPos()
                                area_calc = [cord[0]/1000,-cord[1]/1000]
                                dg = 0.5
                                dl = float(i[3].menu.data["dl"])
                                da = float(i[3].menu.data["da"])
                                z = (float(i[3].menu.data["Z"]),)
                                tp = "O_calc_point"
                                break

                

                if (tp == "H_calc_area" or tp == "V_calc_area") and tc is None:
                    SpaceCord, H_area = run_area_calc(tp,lst,area_calc,z,dg,dl,da)
                    self.ShowCanvas(SpaceCord,H_area,area_calc,z,tp)
                
                elif tp == "O_calc_point" and tc is None:
                    self.calcObjectsDict[j][3].menu.data["result"] = run_area_calc(tp,lst,area_calc,z,dg,dl,da)
                    self.scene.update()

            elif tc==1:
                CalcDict = {i : self.calcObjectsDict[i] for i in dnn}
                sp_points = []
                sp_levels = []
                for j,i in CalcDict.items():
                    if i[0]=="name":
                        if i[3].menu.data["obj_type"] == "H_calc_area":
                            cord = i[3].getPos()
                            area_calc = [cord[0]/1000,-cord[3]/1000,cord[2]/1000,-cord[1]/1000]
                            dg = float(i[3].menu.data["dg"])
                            dl = float(i[3].menu.data["dl"])
                            da = float(i[3].menu.data["da"])
                            z = (float(i[3].menu.data["Z"]),)
                            tp = "H_calc_area"

                            SpaceCord, H_area = run_area_calc(tp,lst,area_calc,z,dg,dl,da)
                            sp_levels += self.ShowCanvas(SpaceCord,H_area,area_calc,z,tp,tc=1)

                        elif i[3].menu.data["obj_type"] == "O_calc_point":
                            cord = i[3].getPos()
                            area_calc = [cord[0]/1000,-cord[1]/1000]
                            dg = 0.5
                            dl = float(i[3].menu.data["dl"])
                            da = float(i[3].menu.data["da"])
                            z = (float(i[3].menu.data["Z"]),)
                            tp = "O_calc_point"

                            rez = run_area_calc(tp,lst,area_calc,z,dg,dl,da) + ' А/м'

                            sp_points.append([cord[0],-cord[1], rez])

                dxf.SaveInDXF(sp_points,sp_levels,sp_obj,fname)

            

        except Exception as ex:
            print('aaaaa',ex)

    def get_obj_for_resize(self):
        return self.listObjectsDict, self.calcObjectsDict

    def OpenObjMenu(self,modelindex):
        try:
            id_obj = self.linksObjectsDict[QPersistentModelIndex(modelindex)]
            if self.listObjectsDict[id_obj][0] == "name":
                self.listObjectsDict[id_obj][3].menu.show()
        except Exception as ex:
            print(ex)

    def OpenCalcMenu(self,modelindex):
        id_obj = QPersistentModelIndex(modelindex)
        if self.calcObjectsDict[id_obj][0] == "name":
            self.calcObjectsDict[id_obj][3].menu.show()

    def SelectObjects(self,modelindex):
        self.current_obj_index = modelindex
    def SelectCalc(self,modelindex):
        self.current_calc_index = modelindex

    def ChangeCheckObjects(self,modelindex):
        try:
            self.current_obj_index = modelindex.index()
            row = self.listObjectsDict[self.linksObjectsDict[QPersistentModelIndex(self.current_obj_index)]]
            if row[0]=="check":
                if row[3].checkState() == Qt.Checked:
                    self.scene.addItem(self.listObjectsDict[row[2]][3])
                    self.listObjectsDict[row[2]][4] = False
                elif row[3].checkState() == Qt.Unchecked:
                    self.scene.removeItem(self.listObjectsDict[row[2]][3])
                    self.listObjectsDict[row[2]][4] = True
        except Exception as ex:
            print(ex)


    def ChangeCheckCalc(self,modelindex):
        #ChekItem.setCheckState(check)
        self.current_calc_index = modelindex.index()
        curren_obj = QPersistentModelIndex(self.current_calc_index)
        try:
            row = self.calcObjectsDict[curren_obj]
            if row[0]=="check":
                if row[1].checkState() == Qt.Checked:
                    self.scene.addItem(self.calcObjectsDict[row[2]][3])
                    self.calcObjectsDict[row[2]][4] = True
                    for i in self.calcObjectsDict:
                        r = self.calcObjectsDict[i]
                        if curren_obj != i and r[0] == "check":
                            if r[1].checkState() == Qt.Checked:
                                r[1].setCheckState(Qt.Unchecked)
                                self.calcObjectsDict[r[2]][4] = False

                    if self.calcObjectsDict[row[2]][3].menu.data["obj_type"] == "O_calc_point":
                        self.calcObjectsDict[row[2]][3].CalcWhenShow()

                elif row[1].checkState() == Qt.Unchecked:
                    self.scene.removeItem(self.calcObjectsDict[row[2]][3])
                    self.calcObjectsDict[row[2]][4] = False
        except Exception as ex:
            print(ex)
        
    def OnOffLayers(self,key,state):
        #print(key,state)
        try:
            self.LayersDict[key][0] = state
            for i in self.LayersDict[key][1]:
                if state:
                    if not self.listObjectsDict[i][5]:
                        self.listObjectsDict[i][5] = state
                        if self.listObjectsDict[i][4]:
                            self.listObjectsDict[i][4] = False
                            #print(self.listObjectsDict[i][3].hndl)
                            self.scene.addItem(self.listObjectsDict[i][3])

                        check_id = self.listObjectsDict[i][2]
                        a = self.listObjectsDict[check_id][1].clone()
                        b = self.listObjectsDict[i][1].clone()
                        self.listObjectsModel.appendRow([a,b])
                        self.linksObjectsDict[QPersistentModelIndex(a.index())] = check_id
                        self.linksObjectsDict[QPersistentModelIndex(b.index())] = i

                        self.listObjectsDict[check_id][3] = a
                        self.listObjectsDict[i][6] = b

                        self.listObjectsDict[i][3].menu.setListName = (lambda ListItem, Circle :(lambda :ListItem.setText(Circle.menu.data["name"])))(b, self.listObjectsDict[i][3])

                        b.setText(self.listObjectsDict[i][3].menu.data["name"])                  

                else:
                    if self.listObjectsDict[i][5]:
                        self.listObjectsDict[i][5] = state
                        if not self.listObjectsDict[i][4]:
                            self.listObjectsDict[i][4] = True
                            self.scene.removeItem(self.listObjectsDict[i][3])

                        check_id = self.listObjectsDict[i][2]

                        del self.linksObjectsDict[QPersistentModelIndex(self.listObjectsDict[i][6].index())]
                        del self.linksObjectsDict[QPersistentModelIndex(self.listObjectsDict[check_id][3].index())]

                        self.listObjectsModel.removeRow(self.listObjectsDict[i][6].row())
           
        except Exception as ex:
            print(ex)

    def DelObj(self):
        try:
            if self.current_obj_index is None: return
            link = self.linksObjectsDict[QPersistentModelIndex(self.current_obj_index)]
            if self.listObjectsDict[link][0] == "name":
                name_id = link
                check_id = self.listObjectsDict[link][2]
            else:
                check_id = link
                name_id = self.listObjectsDict[link][2]

            if self.listObjectsDict[name_id][4]:
                self.scene.removeItem(self.listObjectsDict[name_id][3])

            del self.linksObjectsDict[QPersistentModelIndex(self.listObjectsDict[name_id][6].index())]
            del self.linksObjectsDict[QPersistentModelIndex(self.listObjectsDict[check_id][3].index())]

            self.listObjectsModel.removeRow(self.listObjectsDict[name_id][6].row())

            del self.listObjectsDict[name_id]
            del self.listObjectsDict[check_id]

            for k in self.LayersDict:    
                self.LayersDict[k][1].discard(name_id)
        except Exception as ex:
            print(ex)


    def DelCalcObj(self,al=False):
        try:
            if not al:
                if self.current_calc_index is None: return
                link = QPersistentModelIndex(self.current_calc_index)
                if self.calcObjectsDict[link][0] == "name":
                    name_id = link
                    check_id = self.calcObjectsDict[link][2]
                else:
                    check_id = link
                    name_id = self.calcObjectsDict[link][2]


                
                if self.calcObjectsDict[name_id][4]:
                    self.scene.removeItem(self.calcObjectsDict[name_id][3])

                self.calcObjectsModel.removeRow(self.calcObjectsDict[name_id][1].row())

                del self.calcObjectsDict[name_id]
                del self.calcObjectsDict[check_id]

            else:
                for name_id in self.calcObjectsDict:
                    if self.calcObjectsDict[name_id][0] == "name":
                        check_id = self.calcObjectsDict[name_id][2]

                        if self.calcObjectsDict[name_id][4]:
                            self.scene.removeItem(self.calcObjectsDict[name_id][3])

                        self.calcObjectsModel.removeRow(self.calcObjectsDict[name_id][1].row())

                self.calcObjectsDict = {}        
            
        except Exception as ex:
            print(ex)


    def SaveCalcData(self):
        try:
            lst = {}
            calc = []
            for i,j in self.listObjectsDict.items():
                if j[0] == "name":
                    j[3].menu.InitCords()
                    lst[i] = j[3].menu.data

            for i in self.calcObjectsDict.values():
                if i[0] == "name":
                    i[3].menu.InitCords()
                    calc.append(i[3].menu.data)


            fname = QFileDialog.getSaveFileName(self, 'Сохранить файл', self.path_home,'*.pkl')[0]
            with open( fname, "wb" ) as f:
                pickle.dump({"obj":lst,"calc":calc,"layers":self.LayersDict}, f)
        except Exception as ex:
            print(ex)
        else:
            print("good save")

    def LoadCalcData(self):
        try:
            fname = QFileDialog.getOpenFileName(self, 'Открыть файл', self.path_home,'*.pkl')[0]
            with open(fname, "rb" ) as f:
                data  = pickle.load(f)

            self.CheckListlayers.isCheckFunc = False
            #print(1/self.view.current_scale)
            self.view.scale(1/self.view.current_scale,1/self.view.current_scale)

            
            for key in self.LayersDict:
                self.OnOffLayers(key,False)
                self.CheckListlayers.removeItem(key)

            self.listObjectsDict = {}
            self.linksObjectsDict = {}

            self.DelCalcObj(al=True)

            self.obj_id = max([int(key[5:]) for key in data["obj"]])+1

            wV = self.view.size().width()
            hV = self.view.size().height()

            xmax, ymax, xmin, ymin  = -float("inf"), -float("inf"), float("inf"), float("inf")

            for i in data["obj"].values():
                if i["obj_type"]=="reactor":
                    xmax = max(xmax,float(i["X"])+float(i["Rnar"]))
                    ymax = max(ymax,float(i["Y"])+float(i["Rnar"]))
                    xmin = min(xmin,float(i["X"])-float(i["Rnar"]))
                    ymin = min(ymin,float(i["Y"])-float(i["Rnar"]))
                    

                elif i["obj_type"]=="conductor":
                    for j in i["tbl_cord"]:
                        xmax = max(xmax,float(j[0]))
                        ymax = max(ymax,float(j[1]))
                        xmin = min(xmin,float(j[0]))
                        ymin = min(ymin,float(j[1]))

            scl_layers = min(wV/(xmax-xmin)/1000,hV/(ymax-ymin)/1000) if xmax>-float("inf") and xmin<float("inf") and ymax>-float("inf") and ymin<float("inf") else 1         
            self.LayersDict = data["layers"]
            for key in data["layers"]:
                self.CheckListlayers.addItem(key)

            for i in data["obj"]:
                if data["obj"][i]["obj_type"]=="reactor":
                    pen=QPen(QColor(data["obj"][i]['line_color']), 0, Qt.SolidLine)
                    cl = QColor(data["obj"][i]['body_color'])
                    cl.setAlpha(100)
                    brush=QBrush(cl)
                    Circle = GraphicsCircleItem((float(data["obj"][i]["X"])*1000,-float(data["obj"][i]["Y"])*1000,float(data["obj"][i]["Rnar"])*1000),pen,brush)
                    Circle.menu.data=data["obj"][i]

                    Circle.hndl*=1/scl_layers  
                    Circle.updateHandlesPos()

                    ListItem = QStandardItem(QIcon('images/reactor.png'),data["obj"][i]["name"])
                    ChekItem = QStandardItem("")
                    check = (Qt.Checked if True else Qt.Unchecked)
                    ChekItem.setCheckable(True)
                    ChekItem.setCheckState(check)
                    ChekItem.setEditable(False)
                    # Переименовывание строки списка из меню обьекта
                    
                    LinkList = i
                    LinkCheck = "check_"+i[5:]
                    
                    self.listObjectsDict[LinkList]=["name",ListItem,LinkCheck,Circle,True,False,None]
                    self.listObjectsDict[LinkCheck]=["check",ChekItem,LinkList,None]

                
                elif data["obj"][i]["obj_type"]=="conductor":
                    pen=QPen(QColor(data["obj"][i]['line_color']), 0, Qt.SolidLine)
                    points = [[float(xy[0])*1000, -float(xy[1])*1000] for xy in data["obj"][i]["tbl_cord"]]
                    Polyline = GraphicsPolylineItem(points,pen)
                    Polyline.menu.data = data["obj"][i]

                    Polyline.hndl*=1/scl_layers  
                    Polyline.updateHandlesPos()

                    ListItem = QStandardItem(QIcon('images/conductor.png'),data["obj"][i]["name"])
                    check = (Qt.Checked if True else Qt.Unchecked)
                    ChekItem = QStandardItem("")
                    ChekItem.setCheckable(True)
                    ChekItem.setCheckState(check)
                    ChekItem.setEditable(False)
                    # Переименовывание строки списка из меню обьекта

                    LinkList = i
                    LinkCheck = "check_"+i[5:]

                    self.listObjectsDict[LinkList]=["name",ListItem,LinkCheck,Polyline,True,False,None]
                    self.listObjectsDict[LinkCheck]=["check",ChekItem,LinkList,None]

            self.view.scale(scl_layers,scl_layers)
            self.view.current_scale = scl_layers
            if xmax>-float("inf") and xmin<float("inf") and ymax>-float("inf") and ymin<float("inf"):
                self.view.centerOn(0.5*(xmin+xmax)*1000,-0.5*(ymin+ymax)*1000)



            self.CheckListlayers.isCheckFunc = True

            for i in data["calc"]:
                if i['obj_type'] == "H_calc_area":
                    CalcArea = GraphicsRectItem((float(i["X1"])*1000,-float(i["Y1"])*1000,float(i["X2"])*1000,-float(i["Y2"])*1000))
                    CalcArea.menu.data = i
                    CalcItem = QStandardItem(QIcon('images/rectangle.png'),CalcArea.menu.data['name']) 
                elif i['obj_type'] == "V_calc_area":
                    CalcArea = GraphicsLineItem((float(i["X1"])*1000,-float(i["Y1"])*1000,float(i["X2"])*1000,-float(i["Y2"])*1000))
                    CalcArea.menu.data = i
                    CalcItem = QStandardItem(QIcon('images/line.jpg'),CalcArea.menu.data['name']) 
                elif i['obj_type'] == "O_calc_point":
                    CalcArea = OneCalcCircle((float(i["X"])*1000,-float(i["Y"])*1000),lambda:self.Run_calc_area())
                    CalcArea.menu.data = i
                    CalcItem = QStandardItem(QIcon('images/point.jpg'),CalcArea.menu.data['name']) 
                    
                CalcArea.hndl*=1/scl_layers 
                CalcArea.updateHandlesPos()
                
                
                check = (Qt.Checked if False else Qt.Unchecked)
                ChekItem = QStandardItem("")
                ChekItem.setCheckable(True)
                ChekItem.setCheckState(check)
                ChekItem.setEditable(False)

                CalcArea.menu.setListName = (lambda CalcItem, CalcArea :(lambda :CalcItem.setText(CalcArea.menu.data["name"])))(CalcItem, CalcArea)
                self.calcObjectsModel.appendRow([ChekItem,CalcItem])
                
                LinkList = QPersistentModelIndex(CalcItem.index())
                LinkCheck = QPersistentModelIndex(ChekItem.index())
                self.calcObjectsDict[LinkList]=["name",CalcItem,LinkCheck,CalcArea,False,False]
                self.calcObjectsDict[LinkCheck]=["check",ChekItem,LinkList]

            self.calc_id = len(data["calc"])

        except Exception as ex:
            print(ex)

    def AddObj(self, obj_type):
        
        rect  = self.view.mapToScene(self.view.rect()).boundingRect()
        wd, hg = rect.width()/4, rect.height()/4
        cx,cy = rect.center().x(),rect.center().y()
        
        self.obj_id+=1
        if obj_type == "conductor":
            Obj = GraphicsPolylineItem([[cx-wd,cy-hg],[cx+wd,cy+hg]])

            Obj.menu.data["name"] = "conductor_"+str(self.obj_id)
            ListItem = QStandardItem(QIcon('images/conductor.png'),"conductor_"+str(self.obj_id))

        elif obj_type == "reactor":
            Obj = GraphicsCircleItem((cx,cy,wd))

            Obj.menu.data["name"] = "reactor_"+str(self.obj_id)
            ListItem = QStandardItem(QIcon('images/reactor.png'),"reactor_"+str(self.obj_id))

        
        Obj.hndl*=1/self.view.current_scale  
        Obj.updateHandlesPos()

        ChekItem = QStandardItem("")
        check = (Qt.Checked if True else Qt.Unchecked)
        ChekItem.setCheckable(True)
        ChekItem.setCheckState(check)
        ChekItem.setEditable(False)
        # Переименовывание строки списка из меню обьекта
        
        LinkList = "name_"+str(self.obj_id)
        LinkCheck = "check_"+str(self.obj_id)
        
        self.listObjectsDict[LinkList]=["name",ListItem,LinkCheck,Obj,True,False,None]
        self.listObjectsDict[LinkCheck]=["check",ChekItem,LinkList,None]

        self.LayersDict["Main"][1].add(LinkList)
        self.CheckListlayers.ShowNewObj("Main")

        
    def AddCalcObj(self, obj_type):
        rect  = self.view.mapToScene(self.view.rect()).boundingRect()
        wd, hg = rect.width()/4, rect.height()/4
        cx,cy = rect.center().x(),rect.center().y()
        
        self.calc_id+=1
        if obj_type == "H_calc_area":
            CalcArea = GraphicsRectItem((cx-wd,cy-hg,cx+wd,cy+hg))
            
            CalcArea.menu.data["name"] = "horizontal_"+str(self.calc_id)
            CalcItem = QStandardItem(QIcon('images/rectangle.png'),"horizontal_"+str(self.calc_id))
        elif obj_type == "V_calc_area":
            CalcArea = GraphicsLineItem((cx-wd,cy-hg,cx+wd,cy+hg))

            CalcArea.menu.data["name"] = "vertical_"+str(self.calc_id)
            CalcItem = QStandardItem(QIcon('images/line.jpg'),"vertical_"+str(self.calc_id))
        elif obj_type == "O_calc_point":
            CalcArea = OneCalcCircle((cx,cy), lambda:self.Run_calc_area())

            CalcArea.menu.data["name"] = "point_"+str(self.calc_id)
            CalcItem = QStandardItem(QIcon('images/point.jpg'),"point_"+str(self.calc_id))
            
        CalcArea.hndl*=1/self.view.current_scale 
        CalcArea.updateHandlesPos()
        

        check = (Qt.Checked if False else Qt.Unchecked)
        ChekItem = QStandardItem("")
        ChekItem.setCheckable(True)
        ChekItem.setCheckState(check)
        ChekItem.setEditable(False)

        CalcArea.menu.setListName = (lambda CalcItem, CalcArea :(lambda :CalcItem.setText(CalcArea.menu.data["name"])))(CalcItem, CalcArea)
        self.calcObjectsModel.appendRow([ChekItem,CalcItem])
        
        LinkList = QPersistentModelIndex(CalcItem.index())
        LinkCheck = QPersistentModelIndex(ChekItem.index())
        self.calcObjectsDict[LinkList]=["name",CalcItem,LinkCheck,CalcArea,False,False]
        self.calcObjectsDict[LinkCheck]=["check",ChekItem,LinkList]



    def load_dxf_file(self):
        fname = QFileDialog.getOpenFileName(self, 'Открыть файл', self.path_home,'*.dxf')[0] # Обрати внимание на последний элемент
        name = os.path.splitext(os.path.split(fname)[1])[0]

        self.CheckListlayers.isCheckFunc = False

        #print(1/self.view.current_scale)
        self.view.scale(1/self.view.current_scale,1/self.view.current_scale)


        for key in self.LayersDict:
            self.OnOffLayers(key,False)
            self.CheckListlayers.removeItem(key)

        self.listObjectsDict = {}
        self.linksObjectsDict = {}

        self.DelCalcObj(al=True)


        self.LayersDict = {}
        self.LayersDict["Main"] = [False,set()]
        self.CheckListlayers.addItem("Main")
        self.CheckListlayers.setItemState("Main",False)


        self.obj_id = 0
        self.calc_id = 0

        layers = dxf.OpenFile(fname)

        wV = self.view.size().width()
        hV = self.view.size().height()


        xmax, ymax, xmin, ymin  = -float("inf"), -float("inf"), float("inf"), float("inf")

        fc = lambda a,b: (min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3]))

        for i in layers.values():
            xmin, ymin, xmax, ymax = fc((i["size"][0],i["size"][1],i["size"][2],i["size"][3]),(xmin, ymin, xmax, ymax))

        #scl_layers = min([min(wV/(i["size"][2]-i["size"][0]),hV/(i["size"][3]-i["size"][1])) for i in layers.values()])
        scl_layers = min(wV/(xmax-xmin),hV/(ymax-ymin)) if xmax>-float("inf") and xmin<float("inf") and ymax>-float("inf") and ymin<float("inf") else 1 
        
        dict_calc_obj ={}
        for i in layers:

            if layers[i]["type"] == 'objects':
                self.CheckListlayers.addItem(i)
                self.LayersDict[i] = [False,set()]

                for j in layers[i]["circle"]:
                    self.obj_id+=1
                    l=layers[i]["circle"][j]
                    Circle = GraphicsCircleItem((l[0][0],-l[0][1],l[1]))

                    Circle.hndl*=1/scl_layers  
                    Circle.updateHandlesPos()
                    Circle.menu.data["name"] = j

                    ListItem = QStandardItem(QIcon('images/reactor.png'),j)
                    ChekItem = QStandardItem("")
                    check = (Qt.Checked if True else Qt.Unchecked)
                    ChekItem.setCheckable(True)
                    ChekItem.setCheckState(check)
                    ChekItem.setEditable(False)
                    # Переименовывание строки списка из меню обьекта
                    

                    LinkList = "name_"+str(self.obj_id)
                    LinkCheck = "check_"+str(self.obj_id)
                    
                    self.listObjectsDict[LinkList]=["name",ListItem,LinkCheck,Circle,True,False,None]
                    self.listObjectsDict[LinkCheck]=["check",ChekItem,LinkList,None]

                    self.LayersDict[i][1].add(LinkList)


                for j in layers[i]["lwpolyline"]:
                    self.obj_id+=1
                    l=layers[i]["lwpolyline"][j]
                    points = [[xy[0], -xy[1]] for xy in l]
                    Polyline = GraphicsPolylineItem(points)

                    Polyline.hndl*=1/scl_layers  
                    Polyline.updateHandlesPos()
                    Polyline.menu.data["name"] = j

                    ListItem = QStandardItem(QIcon('images/conductor.png'),j)
                    check = (Qt.Checked if True else Qt.Unchecked)
                    ChekItem = QStandardItem("")
                    ChekItem.setCheckable(True)
                    ChekItem.setCheckState(check)
                    ChekItem.setEditable(False)
                    # Переименовывание строки списка из меню обьекта

                    LinkList = "name_"+str(self.obj_id)
                    LinkCheck = "check_"+str(self.obj_id)

                    self.listObjectsDict[LinkList]=["name",ListItem,LinkCheck,Polyline,True,False,None]
                    self.listObjectsDict[LinkCheck]=["check",ChekItem,LinkList,None]

                    self.LayersDict[i][1].add(LinkList)
            dict_calc_obj.update([(k,["H_calc_area",v]) for k,v in layers[i]["rectangle"].items()] if layers[i]["type"]=='areas' else [])
            dict_calc_obj.update([(k,["V_calc_area",v]) for k,v in layers[i]["line"].items()] if layers[i]["type"]=='areas' else [])
            dict_calc_obj.update([(k,["O_calc_point",v]) for k,v in layers[i]["point"].items()] if layers[i]["type"]=='areas' else [])

        self.view.scale(scl_layers,scl_layers)
        self.view.current_scale = scl_layers
        if xmax>-float("inf") and xmin<float("inf") and ymax>-float("inf") and ymin<float("inf"):
            self.view.centerOn(0.5*(xmin+xmax),-0.5*(ymin+ymax))

        self.CheckListlayers.isCheckFunc = True

        
        for j,i in dict_calc_obj.items():
            if i[0] == "H_calc_area":
                CalcArea = GraphicsRectItem((i[1][0],-i[1][3],i[1][2],-i[1][1])) 
                CalcItem = QStandardItem(QIcon('images/rectangle.png'),j) 
            elif i[0] == "V_calc_area":
                CalcArea = GraphicsLineItem((i[1][0],-i[1][1],i[1][2],-i[1][3]))
                CalcItem = QStandardItem(QIcon('images/line.jpg'),j) 
            elif i[0] == "O_calc_point":
                CalcArea = OneCalcCircle((i[1][0],-i[1][1]), lambda:self.Run_calc_area())
                CalcItem = QStandardItem(QIcon('images/point.jpg'),j) 

            CalcArea.menu.data['name'] = j   
            CalcArea.hndl*=1/scl_layers 
            CalcArea.updateHandlesPos()
            
            
            check = (Qt.Checked if False else Qt.Unchecked)
            ChekItem = QStandardItem("")
            ChekItem.setCheckable(True)
            ChekItem.setCheckState(check)
            ChekItem.setEditable(False)

            CalcArea.menu.setListName = (lambda CalcItem, CalcArea :(lambda :CalcItem.setText(CalcArea.menu.data["name"])))(CalcItem, CalcArea)
            self.calcObjectsModel.appendRow([ChekItem,CalcItem])
            
            LinkList = QPersistentModelIndex(CalcItem.index())
            LinkCheck = QPersistentModelIndex(ChekItem.index())
            self.calcObjectsDict[LinkList]=["name",CalcItem,LinkCheck,CalcArea,False,False]
            self.calcObjectsDict[LinkCheck]=["check",ChekItem,LinkList]

        self.calc_id = len(dict_calc_obj)
        

        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Screen()
    ex.show()
    sys.exit(app.exec_())