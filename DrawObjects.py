# pylint: disable=E0611
# pylint: disable=E1101
from PyQt5.QtCore import Qt, QRectF, QPointF, QRect, QLineF
from PyQt5.QtGui  import QBrush, QPainterPath, QPainter, QColor, QPen, QPolygonF,QFontMetrics,QFont, QPainter

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem,\
                             QGraphicsLineItem, QGraphicsItem,QApplication

from ObjectsMenu import Reactor, Conductor, CalcAreaH, CalcAreaV, OnePoint, Recconductor

import math

class GraphicsLineItem(QGraphicsLineItem):
    """ Класс реализующий интерактивный обьект линии """
    
    handleOne    = 1
    handleTwo    = 2


    hndl = +8
    #handleSize  = handle #+8.0 #Размеры точек управления размерами фигуры
    #handleSpace = -handle/2 #-4.0 #Размеры точек управления размерами фигуры


    handleCursors = {
        handleOne:    Qt.SizeAllCursor,
        handleTwo:    Qt.SizeAllCursor,
    }

    pen=QPen(QColor(0, 0, 0), 0, Qt.DashLine)
    brush=QBrush(QColor(255, 0, 0, 100))
    

    def __init__(self, cord,pen=pen,brush=brush,data=None):
        """ Инициализируйте форму. """

        super().__init__(cord[0],cord[1],cord[2],cord[3])
        self.handles = {}
        self.handleSelected = None
        self.mousePressPos  = None
        self.mousePressRect = None
        self.delta = None
        self.look_object = False

        self.pen=pen
        self.brush=brush

        # Если установлено значение true, этот элемент будет принимать 
        # события при наведении курсора.
        self.setAcceptHoverEvents(True)                                # <---

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        self.menu = CalcAreaV(self.setCrl, self.getPos, self.setPos,data=data)
        self.setCrl()
        self.updateHandlesPos()

    def dragable(self,trig):
        self.setFlag(QGraphicsItem.ItemIsMovable, trig)

    @property
    def handleSize(self):
        return self.hndl

    @property
    def handleSpace(self):
        return -self.hndl/2

    def setCrl(self):
        try:
            self.pen=QPen(QColor(self.menu.data.line_color), 0, Qt.DashLine)
            #print("testcolor")
        except Exception as ex:
            print(ex)


    def handleAt(self, point):
        """ Возвращает маркер изменения размера ниже заданной точки. """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    def hoverMoveEvent(self, moveEvent):
        """ Выполняется, когда мышь перемещается по фигуре (NOT PRESSED). """
        self.look_object = True
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)


    def hoverLeaveEvent(self, moveEvent):
        """ Выполняется, когда мышь покидает фигуру (NOT PRESSED). """
        self.look_object = False
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        """ Выполняется при нажатии мыши на элемент. """
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            self.mousePressPos  = mouseEvent.pos()
            dx1 = self.line().x1()-self.mousePressPos.x()
            dy1 = self.line().y1()-self.mousePressPos.y()
            dx2 = self.line().x2()-self.mousePressPos.x()
            dy2 = self.line().y2()-self.mousePressPos.y()
            self.delta = (dx1,dy1,dx2,dy2)
            self.mousePressRect = self.boundingRect()
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """ Выполняется, когда мышь перемещается над элементом при нажатии. """ 
        if self.handleSelected is not None:
            self.interactiveResize(mouseEvent.pos())
        else:
            super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """ Выполняется, когда мышь освобождается от элемента. """
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos  = None
        self.delta = None
        self.mousePressRect = None
        self.update()

    def mouseDoubleClickEvent(self,mouseEvent):
        """ Запуск события назначенного на двойной клик мыши """
        print("я работаю")
        super().mouseDoubleClickEvent(mouseEvent)

        
    def boundingRect(self):
        """ Возвращает ограничивающий прямоугольник фигуры 
            (включая маркеры изменения размера). """ 
        o = self.handleSize + self.handleSpace
        x1 = min(self.line().x1(),self.line().x2())
        x2 = max(self.line().x1(),self.line().x2())
        y1 = min(self.line().y1(),self.line().y2())
        y2 = max(self.line().y1(),self.line().y2())
        return QRectF(QPointF(x1-o,y1-o),QPointF(x2+o,y2+o))

    def updateHandlesPos(self):
        """ Обновите текущие маркеры изменения размера 
            в соответствии с размером и положением фигуры. """
        s = self.handleSize
        
        self.handles[self.handleOne]    = QRectF(self.line().x1()-s/2, self.line().y1()-s/2, s, s)
        self.handles[self.handleTwo]   = QRectF(self.line().x2()-s/2, self.line().y2()-s/2, s, s)



    def interactiveResize(self, mousePos):
        """ Выполните форму интерактивного изменения размера. """
        line         = self.line()

        self.prepareGeometryChange()

        if self.handleSelected == self.handleOne:
            dx,dy = self.delta[:2]
            self.setLine(mousePos.x()+dx,mousePos.y()+dy,line.x2(),line.y2())
            
        elif self.handleSelected == self.handleTwo:
            dx,dy = self.delta[2:]
            self.setLine(line.x1(),line.y1(),mousePos.x()+dx,mousePos.y()+dy)

        self.updateHandlesPos()

    def BoundingPoligon(self,line):
        """ Возращает полигон, ограничивающий фигуру """
        o = self.handleSize + self.handleSpace
        alf = math.radians(line.angle())

        x1t = line.x1()-o*(math.cos(alf)+math.cos(alf-math.pi/2))
        x2t = line.x2()+o*(math.cos(alf)-math.cos(alf-math.pi/2))

        x1b = line.x1()-o*(math.cos(alf)+math.cos(alf+math.pi/2))
        x2b = line.x2()+o*(math.cos(alf)-math.cos(alf+math.pi/2))

        y1t = line.y1()+o*(math.sin(alf)+math.sin(alf-math.pi/2))
        y2t = line.y2()-o*(math.sin(alf)-math.sin(alf-math.pi/2))

        y1b = line.y1()+o*(math.sin(alf)+math.sin(alf+math.pi/2))
        y2b = line.y2()-o*(math.sin(alf)-math.sin(alf+math.pi/2))
        
        return QPolygonF([QPointF(x1t,y1t),QPointF(x2t,y2t),QPointF(x2b,y2b),QPointF(x1b,y1b)])


    def shape(self):
        """ Возвращает форму этого элемента в виде QPainterPath в локальных координатах. """
        
        path = QPainterPath()
        #path.addRect(self.boundingRect())
        path.addPolygon(self.BoundingPoligon(self.line()))
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path


    def paint(self, painter, option, widget=None):
        """ Нарисуйте узел в графическом представлении. """
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawLine(self.line())
        #painter.drawPolygon(self.BoundingPoligon(self.line()))


        if self.look_object:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(255, 0, 0, 255)))
            painter.setPen(QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for handle, rect in self.handles.items():
                if self.handleSelected is None or handle == self.handleSelected:
                    painter.drawEllipse(rect)


    def getPos(self):
        """ Получение координат линии """
        a = self.mapToScene(self.line().p1())
        b = self.mapToScene(self.line().p2())
        return (a.x(),a.y(),b.x(),b.y())

    def setColorObject(self,pen=None,brush=None):
        """ Изменение цвета обьекта """
        if pen: self.pen=pen
        if brush: self.brush=brush
        self.update()

    def mouseDoubleClickEvent(self, mouseEvent):
        self.menu.show()

    def setPos(self,cord):
        p1 = self.mapFromScene(cord[0],cord[1])
        p2 = self.mapFromScene(cord[2],cord[3])
        self.setLine(QLineF(p1,p2))
        self.updateHandlesPos()
        self.update()

class GraphicsPolylineItem(QGraphicsItem):
    """ Класс реализующий интерактивный объект полилинию """
    obj_type = "polyline"
    hndl = +8
    #handleSize  = handle #+8.0 #Размеры точек управления размерами фигуры
    #handleSpace = -handle/2 #-4.0 #Размеры точек управления размерами фигуры


    pen=QPen(QColor(0, 0, 0), 0, Qt.SolidLine)
    brush=QBrush(QColor(255, 0, 0, 100))

    def __init__(self, scord,pen=pen,brush=brush,data=None,calc_func=None):
        """ Инициализируйте форму. """
        self.handleCursors = {i+1:Qt.SizeAllCursor for i in range(len(scord))}
        self.points = scord

        super().__init__()

        self.handles = {}
        self.handleSelected = None
        self.mousePressPos  = None
        self.mousePressRect = None
        self.delta = None
        self.look_object = False

        self.pen=pen
        self.brush=brush

        self.calc_func = calc_func
        self.re_calc = True

        # Если установлено значение true, этот элемент будет принимать 
        # события при наведении курсора.
        self.setAcceptHoverEvents(True)                                # <---

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        self.menu = Conductor(self.setCrl, self.getPos, self.setPos,data=data)
        self.setCrl()
        self.updateHandlesPos()

    def dragable(self,trig):
        self.setFlag(QGraphicsItem.ItemIsMovable, trig)

    def CalcWhenShow(self):
        if self.calc_func is not None and self.re_calc:
            self.calc_func("sourses")

    @property
    def handleSize(self):
        return self.hndl

    @property
    def handleSpace(self):
        return -self.hndl/2

    def setCrl(self):
        try:
            self.pen=QPen(QColor(self.menu.data.line_color), 0, Qt.SolidLine)
            #print("testcolor")
        except Exception as ex:
            print(ex)


    def handleAt(self, point):
        """ Возвращает маркер изменения размера ниже заданной точки. """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

        

    def hoverMoveEvent(self, moveEvent):
        print("gegegege")
        """ Выполняется, когда мышь перемещается по фигуре (NOT PRESSED). """
        self.look_object = True
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)


    def hoverLeaveEvent(self, moveEvent):
        """ Выполняется, когда мышь покидает фигуру (NOT PRESSED). """
        self.look_object = False
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)


    def mousePressEvent(self, mouseEvent):
        #print("bbb")
        """ Выполняется при нажатии мыши на элемент. """
        self.handleSelected = self.handleAt(mouseEvent.pos())
        self.mousePressPos  = mouseEvent.pos()
        self.delta = [[i[0]-self.mousePressPos.x(),i[1]-self.mousePressPos.y()] for i in self.points]
        if self.handleSelected:
            self.mousePressRect = self.boundingRect()
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """ Выполняется, когда мышь перемещается над элементом при нажатии. """ 
        #super().mouseMoveEvent(mouseEvent)
        self.interactiveResize(mouseEvent.pos())
        self.update()
        


    def mouseReleaseEvent(self, mouseEvent):
        """ Выполняется, когда мышь освобождается от элемента. """
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        #self.mousePressPos  = None
        #self.delta = None
        #self.mousePressRect = None
        self.update()

        if self.calc_func is not None and self.re_calc:
            self.calc_func("sourses")

    def mouseDoubleClickEvent(self,mouseEvent):
        """ Запуск события назначенного на двойной клик мыши """
        print("я работаю")
        super().mouseDoubleClickEvent(mouseEvent)
  
    def boundingRect(self):
        """ Возвращает ограничивающий прямоугольник фигуры 
            (включая маркеры изменения размера). """ 
        o = self.handleSize + self.handleSpace
        x = [i[0] for i in self.points]
        y = [i[1] for i in self.points]

        return QRectF(QPointF(min(x)-o,min(y)-o),QPointF(max(x)+o,max(y)+o))


    def updateHandlesPos(self):
        """ Обновите текущие маркеры изменения размера 
            в соответствии с размером и положением фигуры. """
        s = self.handleSize
        for i in range(len(self.points)):
            self.handles[i+1] = QRectF(self.points[i][0]-s/2, self.points[i][1]-s/2, s, s)

    def interactiveResize(self, mousePos):
        """ Выполните форму интерактивного изменения размера. """
        if self.handleSelected is not None:
            i = self.handleSelected-1
            self.prepareGeometryChange()
            (dx,dy) = self.delta[i]
            self.points[i] = [mousePos.x()+dx,mousePos.y()+dy]
            self.updateHandlesPos()
        else:
            self.prepareGeometryChange() # важная штука
            self.points = [[mousePos.x()+dx,mousePos.y()+dy] for dx,dy in self.delta]
            self.updateHandlesPos()

    def BoundingPoligon(self,line):
        #print("gegegege")
        """ Возращает полигон, ограничивающий фигуру """
        o = self.handleSize + self.handleSpace
        alf = math.radians(line.angle())

        x1t = line.x1()-o*(math.cos(alf)+math.cos(alf-math.pi/2))
        x2t = line.x2()+o*(math.cos(alf)-math.cos(alf-math.pi/2))

        x1b = line.x1()-o*(math.cos(alf)+math.cos(alf+math.pi/2))
        x2b = line.x2()+o*(math.cos(alf)-math.cos(alf+math.pi/2))

        y1t = line.y1()+o*(math.sin(alf)+math.sin(alf-math.pi/2))
        y2t = line.y2()-o*(math.sin(alf)-math.sin(alf-math.pi/2))

        y1b = line.y1()+o*(math.sin(alf)+math.sin(alf+math.pi/2))
        y2b = line.y2()-o*(math.sin(alf)-math.sin(alf+math.pi/2))
        
        return QPolygonF([QPointF(x1t,y1t),QPointF(x2t,y2t),QPointF(x2b,y2b),QPointF(x1b,y1b)])

    def shape(self):
        """ Возвращает форму этого элемента в виде QPainterPath в локальных координатах. """
        path = QPainterPath()
        for i in range(1,len(self.points)):
            p = self.BoundingPoligon(QLineF(QPointF(self.points[i-1][0],self.points[i-1][1]),\
                            QPointF(self.points[i][0],self.points[i][1])))
            path.addPolygon(p)
        #path.addRect(self.boundingRect())
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path



    def paint(self, painter, option, widget=None):
        """ Нарисуйте узел в графическом представлении. """
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        #print(self.points,"move")
        #print(self.brush.color().name())
        """ p = [QPointF(i[0],i[1]) for i in self.points]
        d  = lambda p:painter.drawPolyline(*p)
        d(p) """

        for i in range(1,len(self.points)):
            painter.drawLine(QPointF(self.points[i-1][0],self.points[i-1][1]),\
                            QPointF(self.points[i][0],self.points[i][1]))

        if self.look_object:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(255, 0, 0, 255)))
            painter.setPen(QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for handle, rect in self.handles.items():
                if self.handleSelected is None or handle == self.handleSelected:
                    painter.drawEllipse(rect)

    def getPos(self):
        """ Получение координат полилинии """
        #[[i.mapToScene.x(),i.mapToScene.y()] for i in self.points]
        #a = [[i.x(),i.y()] for i in [self.mapToScene(j[0],j[1]) for j in self.points]] #QPointF(j[0],j[1])
        return self.points
        #return a

    def setPos(self,cord):
        #print("set pos conductor")
        self.points = cord
        self.handleCursors = {i+1:Qt.SizeAllCursor for i in range(len(cord))}
        self.updateHandlesPos()
        self.update()

        if self.calc_func is not None:
            self.calc_func("sourses")


    def setColorObject(self,pen=None,brush=None):
        """ Изменение цвета обьекта """
        if pen: self.pen=pen
        if brush: self.brush=brush
        self.update()

    def mouseDoubleClickEvent(self, mouseEvent):
        self.menu.show()


class RecPolylineItem(QGraphicsItem):
    """ Класс реализующий интерактивный объект полилинию """
    obj_type = "recpolyline"
    hndl = +8
    #handleSize  = handle #+8.0 #Размеры точек управления размерами фигуры
    #handleSpace = -handle/2 #-4.0 #Размеры точек управления размерами фигуры


    pen=QPen(QColor(0, 0, 0), 0, Qt.SolidLine)
    brush=QBrush(QColor(255, 0, 0, 100))

    def __init__(self, scord,pen=pen,brush=brush,data=None):#,calc_func=None
        """ Инициализируйте форму. """
        self.handleCursors = {i+1:Qt.SizeAllCursor for i in range(len(scord))}
        self.points = scord

        super().__init__()

        self.handles = {}
        self.handleSelected = None
        self.mousePressPos  = None
        self.mousePressRect = None
        self.delta = None
        self.look_object = False

        self.pen=pen
        self.brush=brush

        #self.calc_func = calc_func
        self.re_calc = True

        # Если установлено значение true, этот элемент будет принимать 
        # события при наведении курсора.
        self.setAcceptHoverEvents(True)                                # <---

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        self.menu = Recconductor(self.setCrl, self.getPos, self.setPos,data=data)
        self.setCrl()
        self.updateHandlesPos()

    def dragable(self,trig):
        self.setFlag(QGraphicsItem.ItemIsMovable, trig)

    """ def CalcWhenShow(self):
        if self.calc_func is not None and self.re_calc:
            self.calc_func("receivers") """

    @property
    def handleSize(self):
        return self.hndl

    @property
    def handleSpace(self):
        return -self.hndl/2

    def setCrl(self):
        try:
            self.pen=QPen(QColor(self.menu.data.line_color), 0, Qt.SolidLine)
            #print("testcolor")
        except Exception as ex:
            print(ex)


    def handleAt(self, point):
        """ Возвращает маркер изменения размера ниже заданной точки. """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

        

    def hoverMoveEvent(self, moveEvent):
        """ Выполняется, когда мышь перемещается по фигуре (NOT PRESSED). """
        self.look_object = True
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)


    def hoverLeaveEvent(self, moveEvent):
        """ Выполняется, когда мышь покидает фигуру (NOT PRESSED). """
        self.look_object = False
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)


    def mousePressEvent(self, mouseEvent):
        #print("bbb")
        """ Выполняется при нажатии мыши на элемент. """
        self.handleSelected = self.handleAt(mouseEvent.pos())
        self.mousePressPos  = mouseEvent.pos()
        self.delta = [[i[0]-self.mousePressPos.x(),i[1]-self.mousePressPos.y()] for i in self.points]
        if self.handleSelected:
            self.mousePressRect = self.boundingRect()
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """ Выполняется, когда мышь перемещается над элементом при нажатии. """ 
        #super().mouseMoveEvent(mouseEvent)
        self.interactiveResize(mouseEvent.pos())
        self.update()
        
    def mouseReleaseEvent(self, mouseEvent):
        """ Выполняется, когда мышь освобождается от элемента. """
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        #self.mousePressPos  = None
        #self.delta = None
        #self.mousePressRect = None
        self.update()

        """ if self.calc_func is not None and self.re_calc:
            self.calc_func("sourses") """

    def mouseDoubleClickEvent(self,mouseEvent):
        """ Запуск события назначенного на двойной клик мыши """
        print("я работаю")
        super().mouseDoubleClickEvent(mouseEvent)
  
    def boundingRect(self):
        """ Возвращает ограничивающий прямоугольник фигуры 
            (включая маркеры изменения размера). """ 
        o = self.handleSize + self.handleSpace
        x = [i[0] for i in self.points]
        y = [i[1] for i in self.points]

        return QRectF(QPointF(min(x)-o,min(y)-o),QPointF(max(x)+o,max(y)+o))


    def updateHandlesPos(self):
        """ Обновите текущие маркеры изменения размера 
            в соответствии с размером и положением фигуры. """
        s = self.handleSize
        for i in range(len(self.points)):
            self.handles[i+1] = QRectF(self.points[i][0]-s/2, self.points[i][1]-s/2, s, s)

    def interactiveResize(self, mousePos):
        """ Выполните форму интерактивного изменения размера. """
        if self.handleSelected is not None:
            i = self.handleSelected-1
            self.prepareGeometryChange()
            (dx,dy) = self.delta[i]
            self.points[i] = [mousePos.x()+dx,mousePos.y()+dy]
            self.updateHandlesPos()
        else:
            self.prepareGeometryChange() # важная штука
            self.points = [[mousePos.x()+dx,mousePos.y()+dy] for dx,dy in self.delta]
            self.updateHandlesPos()

    def BoundingPoligon(self,line):
        """ Возращает полигон, ограничивающий фигуру """
        o = self.handleSize + self.handleSpace
        alf = math.radians(line.angle())

        x1t = line.x1()-o*(math.cos(alf)+math.cos(alf-math.pi/2))
        x2t = line.x2()+o*(math.cos(alf)-math.cos(alf-math.pi/2))

        x1b = line.x1()-o*(math.cos(alf)+math.cos(alf+math.pi/2))
        x2b = line.x2()+o*(math.cos(alf)-math.cos(alf+math.pi/2))

        y1t = line.y1()+o*(math.sin(alf)+math.sin(alf-math.pi/2))
        y2t = line.y2()-o*(math.sin(alf)-math.sin(alf-math.pi/2))

        y1b = line.y1()+o*(math.sin(alf)+math.sin(alf+math.pi/2))
        y2b = line.y2()-o*(math.sin(alf)-math.sin(alf+math.pi/2))
        
        return QPolygonF([QPointF(x1t,y1t),QPointF(x2t,y2t),QPointF(x2b,y2b),QPointF(x1b,y1b)])

    def shape(self):
        """ Возвращает форму этого элемента в виде QPainterPath в локальных координатах. """
        path = QPainterPath()
        for i in range(1,len(self.points)):
            p = self.BoundingPoligon(QLineF(QPointF(self.points[i-1][0],self.points[i-1][1]),\
                            QPointF(self.points[i][0],self.points[i][1])))
            path.addPolygon(p)
        #path.addRect(self.boundingRect())
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path



    def paint(self, painter, option, widget=None):
        """ Нарисуйте узел в графическом представлении. """
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        #print(self.brush.color().name())
        """ p = [QPointF(i[0],i[1]) for i in self.points]
        d  = lambda p:painter.drawPolyline(*p)
        d(p) """

        for i in range(1,len(self.points)):
            painter.drawLine(QPointF(self.points[i-1][0],self.points[i-1][1]),\
                            QPointF(self.points[i][0],self.points[i][1]))

        if self.look_object:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(255, 0, 0, 255)))
            painter.setPen(QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for handle, rect in self.handles.items():
                if self.handleSelected is None or handle == self.handleSelected:
                    painter.drawEllipse(rect)

    def getPos(self):
        """ Получение координат полилинии """
        #[[i.mapToScene.x(),i.mapToScene.y()] for i in self.points]
        return self.points

    def setPos(self,cord):
        #print("set pos conductor")
        self.points = cord
        self.handleCursors = {i+1:Qt.SizeAllCursor for i in range(len(cord))}
        self.updateHandlesPos()
        self.update()

        """ if self.calc_func is not None:
            self.calc_func("receiver") """


    def setColorObject(self,pen=None,brush=None):
        """ Изменение цвета обьекта """
        if pen: self.pen=pen
        if brush: self.brush=brush
        self.update()

    def mouseDoubleClickEvent(self, mouseEvent):
        self.menu.show()   

class GraphicsCircleItem(QGraphicsEllipseItem):
    """ Класс реализующий интерактивный объект круг """
    obj_type = "circle"
    handleTopMiddle    = 2
    handleMiddleLeft   = 4
    handleMiddleRight  = 5
    handleBottomMiddle = 7


    hndl = +8
    #handleSize  = handle #+8.0 #Размеры точек управления размерами фигуры
    #handleSpace = -handle/2 #-4.0 #Размеры точек управления размерами фигуры

    handleCursors = {
        handleTopMiddle:    Qt.SizeVerCursor,
        handleMiddleLeft:   Qt.SizeHorCursor,
        handleMiddleRight:  Qt.SizeHorCursor,
        handleBottomMiddle: Qt.SizeVerCursor,
    }

    pen=QPen(QColor(0, 0, 0), 0, Qt.SolidLine)
    brush=QBrush(QColor(255, 0, 0, 100))
    
    def __init__(self, cord,pen=pen,brush=brush,data=None,calc_func=None):
        """ Инициализируйте форму. """
        if len(cord)==4:
            super().__init__(cord[0],cord[1],cord[2],cord[3])
        elif len(cord)==3:
            super().__init__(cord[0]-cord[2],cord[1]-cord[2],cord[2]*2,cord[2]*2)
        else:
            raise Exception("Argument cord have next types:(x,y,r) or (x,y,width,height)")
 
        self.handles = {}
        self.handleSelected = None
        self.mousePressPos  = None
        self.mousePressRect = None
        self.look_object = False

        self.pen=pen
        self.brush=brush

        self.calc_func = calc_func
        self.re_calc = True

        # Если установлено значение true, этот элемент будет принимать 
        # события при наведении курсора.
        self.setAcceptHoverEvents(True)                                # <---

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        # Инициируем меню
        self.menu = Reactor(self.setCrl, self.getPos, self.setPos,data=data)
        self.setCrl()
        self.updateHandlesPos()

    def dragable(self,trig):
        self.setFlag(QGraphicsItem.ItemIsMovable, trig)

    def CalcWhenShow(self):
        if self.calc_func is not None and self.re_calc:
            self.calc_func("sourses")

    @property
    def handleSize(self):
        return self.hndl

    @property
    def handleSpace(self):
        return -self.hndl/2

    def setCrl(self):
        try:
            c = QColor(self.menu.data.body_color)
            c.setAlpha(100)
            pen=QPen(QColor(self.menu.data.line_color), 0, Qt.SolidLine)
            brush=QBrush(c)
            self.setColorObject(pen=pen,brush=brush)
        except Exception as ex:
            print(ex)
    



    def handleAt(self, point):
        """ Возвращает маркер изменения размера ниже заданной точки. """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    def hoverMoveEvent(self, moveEvent):
        """ Выполняется, когда мышь перемещается по фигуре (NOT PRESSED). """
        self.look_object = True
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """ Выполняется, когда мышь покидает фигуру (NOT PRESSED). """
        self.look_object = False
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        """ Выполняется при нажатии мыши на элемент. """
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            self.mousePressPos  = mouseEvent.pos()
            self.mousePressRect = self.boundingRect()
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """ Выполняется, когда мышь перемещается над элементом при нажатии. """
        if self.handleSelected is not None:
            self.interactiveResize(mouseEvent.pos())
        else:
            super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """ Выполняется, когда мышь освобождается от элемента. """
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos  = None
        self.mousePressRect = None
        self.update()

        if self.calc_func is not None and self.re_calc:
            self.calc_func("sourses")

    """ def mouseDoubleClickEvent(self,mouseEvent):
        print("я работаю")
        super().mouseDoubleClickEvent(mouseEvent) """

        
    def boundingRect(self):
        """ Возвращает ограничивающий прямоугольник фигуры 
            (включая маркеры изменения размера). 
            Все рисунки должны бить внутри него """
        o = self.handleSize + self.handleSpace
        return self.rect().adjusted(-o, -o, o, o)

    def updateHandlesPos(self):
        """ Обновите текущие маркеры изменения размера 
            в соответствии с размером и положением фигуры. """
        s = self.handleSize
        b = self.boundingRect()
        self.handles[self.handleTopMiddle]    = QRectF(b.center().x() - s / 2, b.top(), s, s)
        self.handles[self.handleMiddleLeft]   = QRectF(b.left(), b.center().y() - s / 2, s, s)
        self.handles[self.handleMiddleRight]  = QRectF(b.right() - s, b.center().y() - s / 2, s, s)
        self.handles[self.handleBottomMiddle] = QRectF(b.center().x() - s / 2, b.bottom() - s, s, s)


    def interactiveResize(self, mousePos):
        """ Выполните форму интерактивного изменения размера. """
        offset       = self.handleSize + self.handleSpace
        rect         = self.rect() # Размеры без учёта маркеров

        point_center = rect.center()
        x1, y1, x2, y2  = rect.left(),rect.top(), rect.right(),rect.bottom()
        r = point_center.y()-y1
        

        self.prepareGeometryChange()


        if self.handleSelected == self.handleTopMiddle:
            fromY = self.mousePressRect.top()
            delta = y1-(fromY + mousePos.y() - self.mousePressPos.y())

            rect = QRectF(point_center.x()-r-delta+offset,\
                                point_center.y()-r-delta+offset,\
                                (r+delta-offset)*2,(r+delta-offset)*2)

            self.setRect(rect)

        

        elif self.handleSelected == self.handleMiddleLeft:
            fromX = self.mousePressRect.left()
            delta = x1-(fromX + mousePos.x() - self.mousePressPos.x())

            rect = QRectF(point_center.x()-r-delta+offset,\
                                point_center.y()-r-delta+offset,\
                                (r+delta-offset)*2,(r+delta-offset)*2)

            self.setRect(rect)

        elif self.handleSelected == self.handleMiddleRight:
            fromX = self.mousePressRect.right()
            delta = -x2+(fromX + mousePos.x() - self.mousePressPos.x())

            rect = QRectF(point_center.x()-r-delta+offset,\
                                point_center.y()-r-delta+offset,\
                                (r+delta-offset)*2,(r+delta-offset)*2)

            self.setRect(rect)

        

        elif self.handleSelected == self.handleBottomMiddle:
            fromY = self.mousePressRect.bottom()
            delta = -y2+(fromY + mousePos.y() - self.mousePressPos.y())

            rect = QRectF(point_center.x()-r-delta+offset,\
                                point_center.y()-r-delta+offset,\
                                (r+delta-offset)*2,(r+delta-offset)*2)

            self.setRect(rect)

        self.updateHandlesPos()
        

    def shape(self):
        #QApplication.font()
        """ rect = QFontMetrics(QFont("times", 48)).boundingRect("Test") #Определяем размеры текста
        try:
            print(rect)
            print(QRectF(rect))
            print(self.mapRectFromScene(QRectF(rect)))
        except Exception as ex:
            print(ex) """
        """ Возвращает форму этого элемента в виде QPainterPath в локальных координатах. """
        path = QPainterPath()
        path.addEllipse(self.rect())
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path

    def paint(self, painter, option, widget=None):
        """ Нарисуйте узел в графическом представлении. """
        
        o = self.handleSize + self.handleSpace
        # Рисуем круг
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawEllipse(self.rect())


        # Рисуем маркеры
        if self.look_object:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(255, 0, 0, 255)))
            painter.setPen(QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for handle, rect in self.handles.items():
                if self.handleSelected is None or handle == self.handleSelected:
                    painter.drawEllipse(rect)

        # Рисуем перекрестие
        painter.setPen(QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        point_center = self.rect().center()
        r = self.rect().width()/2
        painter.drawLine(point_center.x()-r*0.2,point_center.y(),point_center.x()+r*0.2,point_center.y())
        painter.drawLine(point_center.x(),point_center.y()-r*0.2,point_center.x(),point_center.y()+r*0.2)

        # Печатаем текст
        #rect = painter.boundingRect(QRectF(0,0,0,0),Qt.AlignCenter,"Test")
        #print(rect)
        #painter.drawText(point_center.x()+rect.x(),point_center.y()+r*0.2-rect.y()+o*2,"Test")

        self.setRect(self.rect())

        


    def getPos(self):
        """ Получение координат и радиуса элипса """
        r = self.mapRectToScene(self.rect()).getRect()
        return r[0]+r[2]/2,(r[1]+r[2]/2),r[2]/2

    def setColorObject(self,pen=None,brush=None):
        """ Изменение цвета обьекта """
        if pen: self.pen=pen
        if brush: self.brush=brush
        self.update()

    def mouseDoubleClickEvent(self, mouseEvent):
        self.menu.show()

    def setPos(self,cord):
        r = self.mapRectFromScene(QRectF(cord[0]-cord[2],cord[1]-cord[2],cord[2]*2,cord[2]*2))
        self.setRect(r)
        self.updateHandlesPos()
        self.update()

        if self.calc_func is not None:
            self.calc_func("sourses")
        

class GraphicsRectItem(QGraphicsRectItem):
    """ Класс реализующий интерактивный объект прямоугольника """


    handleTopLeft      = 1
    handleTopMiddle    = 2
    handleTopRight     = 3
    handleMiddleLeft   = 4
    handleMiddleRight  = 5
    handleBottomLeft   = 6
    handleBottomMiddle = 7
    handleBottomRight  = 8


    hndl = +8
    #handleSize  = handle #+8.0 #Размеры точек управления размерами фигуры
    #handleSpace = -handle/2 #-4.0 #Размеры точек управления размерами фигуры


    handleCursors = {
        handleTopLeft:      Qt.SizeFDiagCursor,
        handleTopMiddle:    Qt.SizeVerCursor,
        handleTopRight:     Qt.SizeBDiagCursor,
        handleMiddleLeft:   Qt.SizeHorCursor,
        handleMiddleRight:  Qt.SizeHorCursor,
        handleBottomLeft:   Qt.SizeBDiagCursor,
        handleBottomMiddle: Qt.SizeVerCursor,
        handleBottomRight:  Qt.SizeFDiagCursor,
    }

    pen=QPen(QColor(0, 0, 0), 0, Qt.DashLine)
    brush=QBrush(QColor(0, 0, 255, 10))

    def __init__(self, cord,pen=pen,brush=brush,data=None):
        """ Инициализируйте форму. """

        super().__init__(cord[0],cord[1],cord[2]-cord[0],cord[3]-cord[1])
        self.handles = {}
        self.handleSelected = None
        self.mousePressPos  = None
        self.mousePressRect = None
        self.look_object = False

        self.pen=pen
        self.brush=brush

        # Если установлено значение true, этот элемент будет принимать 
        # события при наведении курсора.
        self.setAcceptHoverEvents(True)                                # <---

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        # Инициируем меню
        self.menu = CalcAreaH(self.setCrl, self.getPos, self.setPos,data=data)
        self.setCrl()
        self.updateHandlesPos()

    def dragable(self,trig):
        self.setFlag(QGraphicsItem.ItemIsMovable, trig)

    @property
    def handleSize(self):
        return self.hndl

    @property
    def handleSpace(self):
        return -self.hndl/2

    def setCrl(self):
        try:
            #c = QColor(self.menu.data['body_color'])
            #c.setAlpha(100)
            pen=QPen(QColor(self.menu.data.line_color), 0, Qt.DashLine)
            #brush=QBrush(c)
            self.setColorObject(pen=pen)
        except Exception as ex:
            print(ex)

    def handleAt(self, point):
        """ Возвращает маркер изменения размера ниже заданной точки. """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    def hoverMoveEvent(self, moveEvent):
        """ Выполняется, когда мышь перемещается по фигуре (NOT PRESSED). """
        self.look_object = True
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """ Выполняется, когда мышь покидает фигуру (NOT PRESSED). """
        self.look_object = False
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        """ Выполняется при нажатии мыши на элемент. """
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            self.mousePressPos  = mouseEvent.pos()
            self.mousePressRect = self.boundingRect()
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """ Выполняется, когда мышь перемещается над элементом при нажатии. """ 
        if self.handleSelected is not None:
            self.interactiveResize(mouseEvent.pos())
        else:
            super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """ Выполняется, когда мышь освобождается от элемента. """
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos  = None
        self.mousePressRect = None
        self.update()

    def mouseDoubleClickEvent(self,mouseEvent):
        """ Запуск события назначенного на двойной клик мыши """
        print("я работаю")
        super().mouseDoubleClickEvent(mouseEvent)

    def boundingRect(self):
        """ Возвращает ограничивающий прямоугольник фигуры 
            (включая маркеры изменения размера). """
        o = self.handleSize + self.handleSpace
        return self.rect().adjusted(-o, -o, o, o)

    def updateHandlesPos(self):
        """ Обновите текущие маркеры изменения размера 
            в соответствии с размером и положением фигуры. """
        s = self.handleSize
        b = self.boundingRect()
        self.handles[self.handleTopLeft]      = QRectF(b.left(), b.top(), s, s)
        self.handles[self.handleTopMiddle]    = QRectF(b.center().x() - s / 2, b.top(), s, s)
        self.handles[self.handleTopRight]     = QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleMiddleLeft]   = QRectF(b.left(), b.center().y() - s / 2, s, s)
        self.handles[self.handleMiddleRight]  = QRectF(b.right() - s, b.center().y() - s / 2, s, s)
        self.handles[self.handleBottomLeft]   = QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomMiddle] = QRectF(b.center().x() - s / 2, b.bottom() - s, s, s)
        self.handles[self.handleBottomRight]  = QRectF(b.right() - s, b.bottom() - s, s, s)


    def interactiveResize(self, mousePos):
        """ Выполните форму интерактивного изменения размера. """
        offset       = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect         = self.rect()
        diff         = QPointF(0, 0)

        self.prepareGeometryChange()

        if self.handleSelected == self.handleTopLeft:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX   = fromX + mousePos.x() - self.mousePressPos.x()
            toY   = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setTop(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleTopMiddle:

            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setTop(toY)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleTopRight:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX   = fromX + mousePos.x() - self.mousePressPos.x()
            toY   = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setTop(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleMiddleLeft:

            fromX = self.mousePressRect.left()
            toX   = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setLeft(toX)
            rect.setLeft(boundingRect.left() + offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleMiddleRight:
            fromX = self.mousePressRect.right()
            toX   = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setRight(toX)
            rect.setRight(boundingRect.right() - offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleBottomLeft:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX   = fromX + mousePos.x() - self.mousePressPos.x()
            toY   = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setBottom(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleBottomMiddle:

            fromY = self.mousePressRect.bottom()
            toY   = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setBottom(toY)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleBottomRight:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX   = fromX + mousePos.x() - self.mousePressPos.x()
            toY   = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setBottom(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)

        self.updateHandlesPos()

    def shape(self):
        """ Возвращает форму этого элемента в виде QPainterPath в локальных координатах. """
        path = QPainterPath()
        path.addRect(self.rect())
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path

    def paint(self, painter, option, widget=None):
        """ Нарисуйте узел в графическом представлении. """
        o = self.handleSize + self.handleSpace
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawRect(self.rect())

        if self.look_object:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(255, 0, 0, 255)))
            painter.setPen(QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for handle, rect in self.handles.items():
                if self.handleSelected is None or handle == self.handleSelected:
                    painter.drawEllipse(rect)

        # Рисуем перекрестие
        painter.setPen(QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        point_center = self.rect().center()
        x = -self.rect().left()+point_center.x()
        y=  -self.rect().top()+point_center.y()
        r=min(x,y)
        painter.drawLine(point_center.x()-r*0.2,point_center.y(),point_center.x()+r*0.2,point_center.y())
        painter.drawLine(point_center.x(),point_center.y()-r*0.2,point_center.x(),point_center.y()+r*0.2)

        # Печатаем текст
        rect = painter.boundingRect(QRectF(0,0,0,0),Qt.AlignCenter,"Test")
        painter.drawText(point_center.x()+rect.x(),point_center.y()+r*0.2-rect.y()+o*2,"Test")



    def getPos(self):
        """ Получение координат и радиуса элипса """
        r = self.mapRectToScene(self.rect()).getCoords()
        return r

    def setColorObject(self,pen=None,brush=None):
        """ Изменение цвета обьекта """
        if pen: self.pen=pen
        if brush: self.brush=brush
        self.update()

    def mouseDoubleClickEvent(self, mouseEvent):
        self.menu.show()

    def setPos(self,cord):
        r = self.mapRectFromScene(QRectF(cord[0],cord[1],cord[2]-cord[0],cord[3]-cord[1]))
        self.setRect(r)
        self.updateHandlesPos()
        self.update()



class OneCalcCircle(QGraphicsEllipseItem):
    """ Класс реализующий интерактивный объект круг """
    obj_type = "circle"
    handleTopMiddle    = 2
    handleMiddleLeft   = 4
    handleMiddleRight  = 5
    handleBottomMiddle = 7

    hndl = +8

    pen=QPen(QColor(0, 0, 0), 0, Qt.SolidLine)
    brush=QBrush(QColor(0, 0, 255, 70))
    
    def __init__(self, cord,pen=pen,brush=brush,data=None,calc_func=None):
        """ Инициализируйте форму. """
        if len(cord)==2:
            super().__init__(cord[0]-self.hndl,cord[1]-self.hndl,self.hndl*2,self.hndl*2)
        else:
            raise Exception("Argument cord have next types:(x,y)")
 
        self.handles = {}
        self.handleSelected = None
        self.mousePressPos  = None
        self.mousePressRect = None
        self.look_object = False

        self.pen=pen
        self.brush=brush

        self.calc_func = calc_func
        self.re_calc = True

        # Если установлено значение true, этот элемент будет принимать 
        # события при наведении курсора.
        self.setAcceptHoverEvents(True)                                # <---

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        # Инициируем меню
        self.menu = OnePoint(self.setCrl, self.getPos, self.setPos,data=data)
        self.setCrl()
        self.updateHandlesPos()

    def dragable(self,trig):
        self.setFlag(QGraphicsItem.ItemIsMovable, trig)

        
    def CalcWhenShow(self):
        if self.calc_func is not None and self.re_calc:
            self.calc_func("areas",data=self.menu.data)

    @property
    def handleSize(self):
        return self.hndl

    @property
    def handleSpace(self):
        return -self.hndl/2

    def setCrl(self):
        try:
            pen=QPen(QColor(self.menu.data.line_color), 0, Qt.SolidLine)
            self.setColorObject(pen=pen)
        except Exception as ex:
            print(ex)

    def mouseMoveEvent(self, mouseEvent):
        """ Выполняется, когда мышь перемещается над элементом при нажатии. """ 
        self.re_calc = True
        super().mouseMoveEvent(mouseEvent)
        
    

    def mouseReleaseEvent(self, mouseEvent):
        """ Выполняется, когда мышь освобождается от элемента. """
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos  = None
        self.mousePressRect = None
        self.update()

        if self.calc_func is not None and self.re_calc:
            self.calc_func("areas",data=self.menu.data)

        
    def updateHandlesPos(self):
        #Обновите текущие маркеры изменения размера 
        #в соответствии с размером и положением фигуры.
        r = self.rect().center()
        self.setRect(QRectF(r.x()-self.hndl,r.y()-self.hndl,self.hndl*2,self.hndl*2))
      

    def shape(self):
        #Возвращает форму этого элемента в виде QPainterPath в локальных координатах.
        o = self.handleSize + self.handleSpace
        fnt = QFont('Arial',o*2.2)
        point_center = self.rect().center()
        r = self.rect().width()/2

        text_rect = QRectF(QFontMetrics(QFont('Arial',o*2.2)).boundingRect(self.menu.data.result.text)) #Определяем размеры текста
        text_rect.setRect(point_center.x()-text_rect.width()/2-o,point_center.y()-r-text_rect.height(),text_rect.width()+o*2,text_rect.height())
        self.text_rect = text_rect


        path = QPainterPath()
        path.addEllipse(self.rect())
        path.addRect(text_rect)
        
        
        return path

    def paint(self, painter, option, widget=None):
        """ Нарисуйте узел в графическом представлении. """
        
        o = self.handleSize + self.handleSpace
        # Рисуем круг
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawEllipse(self.rect())


        # Рисуем перекрестие
        painter.setPen(QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        point_center = self.rect().center()
        r = self.rect().width()/2
        painter.drawLine(point_center.x()-r*1.0,point_center.y()-r*1.0,point_center.x()+r*1.0,point_center.y()+r*1.0)
        painter.drawLine(point_center.x()+r*1.0,point_center.y()-r*1.0,point_center.x()-r*1.0,point_center.y()+r*1.0)

        
        fnt = QFont('Arial',o*2.2)
        painter.setFont(fnt)


        text_rect = painter.boundingRect(QRectF(0,0,0,0), Qt.AlignCenter,self.menu.data.result.text)
        text_rect.setRect(point_center.x()-text_rect.width()/2,point_center.y()-r-text_rect.height(),text_rect.width(),text_rect.height())

        painter.drawText(text_rect,self.menu.data.result.text)

        painter.drawRect(self.text_rect)
     


    def getPos(self):
        """ Получение координат и радиуса элипса """
        r = self.mapToScene(self.rect().center())
        return (r.x(), r.y())

    def setColorObject(self,pen=None,brush=None):
        """ Изменение цвета обьекта """
        if pen: self.pen=pen
        if brush: self.brush=brush
        self.update()

    def mouseDoubleClickEvent(self, mouseEvent):
        self.menu.show()

    def setPos(self,cord):
        r = self.mapRectFromScene(QRectF(cord[0]-self.hndl,cord[1]-self.hndl,self.hndl*2,self.hndl*2))
        self.setRect(r)
        #self.updateHandlesPos()
        self.update()

        if self.calc_func is not None:
            self.calc_func("areas",data=self.menu.data)



if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QGraphicsView,QGraphicsScene
    app = QApplication(sys.argv)

    grview = QGraphicsView()
    scene  = QGraphicsScene()
    scene.setSceneRect(0, 0, 800, 800)
    grview.setScene(scene)

    item = GraphicsLineItem((0, 0, 300, 150))
    scene.addItem(item)

    item = GraphicsPolylineItem([[0,0],[300,300],[300,600]])
    scene.addItem(item)

    item = OneCalcCircle((15, 15))
    #brush=QBrush(QColor(0, 255, 0, 100))
    #item.setColorObject(brush=brush)
    scene.addItem(item)

    item = GraphicsRectItem((0, 0, 300, 150))
    item.setRotation(50)
    scene.addItem(item)

    grview.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
    grview.show()
    sys.exit(app.exec_())