# CalculateMagneticFields 

## Scope of application 
**CalculateMagneticFields** - десктопное приложение, предназначенное для расчёта магнитного поля и наведённых токов в замкнутых контурах с использованием файлов *.dxf* для получения исходных данных и возврата результатов расчётов в системы CAD.

**CalculateMagneticFields** - the desktop application for calculating magnetic fields and induced currents in closed circuits with using *.dxf* files for getting initial data and returning of calculation results into CAD systems.


## Table of contents

  1. [Description](#Description)
  2. [Used technologies](#Used-technologies)
  3. [Installation](#Installation)
  4. [License](#License)

## Description

Для обеспечения электромагниной совместимости технических средсв объектов электроэнергетики необходимо провести ряд действи по оценке текущей электомагнитной обстановки и при невозможности обеспечениия электромагниной совместимости провести ряд мероприятий по доведению текушей обстановки до требуемого состояния. При проектировании объектов электроэнергетики единственным способом определения электомагнитной обстановки является проведение ряда расчётов.

Одним из условий для электромагниной совместимости является не превышение допустимых значений напряженности магнитного поля  около технических средсв, что в рамках проектирования создаёт необходимость выполнения расчётов напряженности магнитного поля. Это было основной причиной создания данного приложения.

electromagnetic compatibility (электромагниной совместимости)
electromagnetic environment (электромагнитная обстановка)

Требования к данной программе были следующими:
- расчёт напряженности магнитного поля в заданной горизонтальной плоскости с заданным шагом;
- расчёт напряженности магнитного поля в заданной вертикальной плоскости с заданным шагом;
- расчёт напряженности магнитного поля в заданных точках пространства;
- расчёт наводимых токов в замкнутых контрах любой конфиграции от источников магнитного поля;
- расчёт собственной и взаимной индуктивности от проводников произвольной формы.

В данном приложении для расчёта напряжённости магнитного поля, собственной и взаимной индуктивности от проводников произвольной формы а также расчёта электрических цепей используются следующие математические выражения:
![Alt Text](.github/images/MCF_formulas.jpg)
Как видно, выражения для расчёта напряжённости магнитного поля, собственной и взаимной индуктивности от проводников произвольной формы являются интегральными выражениями, что значительно увеличивает объём требуемых вычислений. Соотвественно вычисление по какой либо области при множестве источников магнтиного поля или вычисление собственно и взимной индуктивности множества элементов в большинстве случаев занимает длительное время, что достаточно неудобно в использовании.

Поэтому для оптимизации затрат времени испоьзуются вычисления на GPU. Это возможно при использовании GPU от NVIDIA с наличием CUDA ядер, среды разработки для создания высокопроизводительных приложений с ускорением на GPU [CUDA Toolkit](https://developer.nvidia.com/cuda-10.1-download-archive-update2), и пакета [PyTorch](https://pytorch.org/) для тензорных вычислений (например, NumPy) с сильным ускорением от графического процессора. При этом при отсутвии GPU приложение выполняет расчёты на СPU.

Перед выполнением расчётов на GPU необходимо перенести исходные из оперативной памяти компьютера в оперативню память GPU. Объем данной памяти много меньше чем объем оперативной памяти компьютера, и так же не имеет файлов подкачки. Так что необходимо отслеживать обьём памяти требуемый для выполнения вычислений. Поэтому выплоняемые вычисления разделяются на множество задач, которые распределяются решаются следующим образом:

![Alt Text](.github/images/MCF_5.jpg)

Как видно из схемы при наличии GPU все вычисления на которые у GPU хватает памяти вычислеться на ней, а оставшиеся отправляются на расчёт CPU, при этом когда GPU решает все задачи CPU возвращает максимальное количество задач в GPU. При этом при отсутвии GPU приложение выполняет расчёты только на СPU. Так как помимо данного приложения память GPU могут испооьзовать и другие приложения, необходимо следить обьемом досутпной памяти, так как её переполнение приводик к ошибке. Для этого испоьзуется библиотека [Pynvml](https://pypi.org/project/pynvml/8.0.3/) которая позволяет мониторить различные параметры GPU.

GUI приложения разработан при помощи библиотеки [PyQt5](https://pypi.org/project/PyQt5/5.9/).

![Alt Text](.github/images/MCF_1.jpg)

![Alt Text](.github/images/MCF_2.jpg)

![Alt Text](.github/images/MCF_3.jpg)


## Used technologies

- [Python 3.6.2](https://www.python.org/downloads/) - Python programming language interpreter.
- [CUDA Toolkit 10.1](https://developer.nvidia.com/cuda-10.1-download-archive-update2) - The NVIDIA® CUDA® Toolkit provides a development environment for creating high performance GPU-accelerated applications.
- [Numpy 1.15.0](https://pypi.org/project/numpy/1.15.0/) - general-purpose array-processing package designed to efficiently manipulate large multi-dimensional arrays of arbitrary records without sacrificing too much speed for small multi-dimensional arrays.
- [Scipy 1.5.4](https://pypi.org/project/scipy/1.5.4/) - open-source software for mathematics, science, and engineering.
- [Matplotlib 2.2.2](https://pypi.org/project/matplotlib/2.2.2/) - library for interactive graphing, scientific publishing, user interface development and web application servers targeting multiple user interfaces and hardcopy output formats.
- [PyQt5 5.9](https://pypi.org/project/PyQt5/5.9/) - Python binding of the cross-platform GUI toolkit Qt, implemented as a Python plug-in.
- [Openpyxl 2.4.8](https://pypi.org/project/openpyxl/2.4.8/) - Python library to read/write Excel 2010 xlsx/xlsm/xltx/xltm files.
- [PyTorch 1.3.0+cuda 10.1](https://download.pytorch.org/whl/cu101/torch-1.3.0-cp36-cp36m-win_amd64.whl) - PyTorch is a Python package that provides two high-level features: Tensor computation (like NumPy) with strong GPU acceleration and Deep neural networks built on a tape-based autograd system.
- [Ezdxf 0.14.2](https://pypi.org/project/ezdxf/0.14.2/) - Python package to create and modify DXF drawings, independent from the DXF version.
- [Pynvml 8.0.3](https://pypi.org/project/pynvml/8.0.3/) - Provides a Python interface to Nvidia GPU management and monitoring functions.



## Installation 
Для того чтобы использовать данное приложение необходимо установить компоненты с раздела [Used technologies](#Used-technologies). Первоначально установите интерпретатор Python, а затем при помощи пакетного менеджера *Pip* установите перечисленные пакеты. При применении версий пакетов отличных от предложенных работоспособность приложения не гарантируется.

For using the application necessity to install components from section [Used technologies](#Used-technologies). First of all install Python interpreter, and after that using package manager *Pip* to install listed packages. In case using versions of packages that differ from the proposed, correct work of the application is not ensured.

        pip install -r requirements.txt


## License 
Licensed under the [MIT](LICENSE.txt) license.	
