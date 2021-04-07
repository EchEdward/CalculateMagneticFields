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

To provide electromagnetic compatibility of technical means of electric industry objects it's necessary to do some acts to check electromagnetic environment and if electromagnetic compatibility wasn't provided, it's necessary to do actions that will make required compatibility. In case designing of electric industry objects calculating are a singular way of definition electromagnetic environment.

Для обеспечения электромагниной совместимости технических средсв объектов электроэнергетики необходимо провести ряд действи по оценке текущей электомагнитной обстановки и при невозможности обеспечениия электромагниной совместимости провести ряд мероприятий по доведению текушей обстановки до требуемого состояния. При проектировании объектов электроэнергетики единственным способом определения электомагнитной обстановки является проведение ряда расчётов.

One of a conditions of electromagnetic compatibility is values of magnetic field strength near technical means don't have to be  more than admissible, what in case of designing creates necessary to calculate values of magnetic field strength. It was main reason of developing the app.

Одним из условий для электромагниной совместимости является не превышение допустимых значений напряженности магнитного поля  около технических средсв, что в рамках проектирования создаёт необходимость выполнения расчётов напряженности магнитного поля. Это было основной причиной создания данного приложения.

In this app for calculating of magnetic field strength, self and mutual inductance of free-form conductors and electric circuits is used following mathematical expressions:

В данном приложении для расчёта напряжённости магнитного поля, собственной и взаимной индуктивности от проводников произвольной формы а также расчёта электрических цепей используются следующие математические выражения:

![Alt Text](.github/images/MCF_formulas.jpg)

How we see, expressions for calculating of magnetic field strength, self and mutual inductance of free-form conductors is integral expressions, that makes volume of calculations very big. So calculating for some area in case lots of sources of magnetic field or calculating self and mutual inductance for lots of elements can spend too much time, that isn't convenient.

Как видно, выражения для расчёта напряжённости магнитного поля, собственной и взаимной индуктивности от проводников произвольной формы являются интегральными выражениями, что значительно увеличивает объём требуемых вычислений. Соотвественно вычисление по какой либо области при множестве источников магнтиного поля или вычисление собственно и взимной индуктивности множества элементов в большинстве случаев занимает длительное время, что достаточно неудобно в использовании.

So for optimization time spending GPU calculating are used. It is possible in case using GPU from NVIDIA with CUDA cores, a development environment for creating high performance GPU-accelerated applications by [CUDA Toolkit](https://developer.nvidia.com/cuda-10.1-download-archive-update2), [PyTorch](https://pytorch.org/) package that provides tensor computation (like NumPy) with strong GPU acceleration. In case absence of GPU, application runs calculations on CPU.

Поэтому для оптимизации затрат времени испоьзуются вычисления на GPU. Это возможно при использовании GPU от NVIDIA с наличием CUDA ядер, среды разработки для создания высокопроизводительных приложений с ускорением на GPU [CUDA Toolkit](https://developer.nvidia.com/cuda-10.1-download-archive-update2), и пакета [PyTorch](https://pytorch.org/) для тензорных вычислений (например, NumPy) с сильным ускорением от графического процессора. При этом при отсутвии GPU приложение выполняет расчёты на СPU.

Before running calculations on GPU it's necessary to move initial data from computer RAM into GPU RAM. Volume of GPU RAM usually less than computer RAM, and also doesn't have swap files. So it's necessary to check memory size that is needed for calculating. Thus performing calculations are separated on lots of tasks, which are distributed and solved following way:

Перед выполнением расчётов на GPU необходимо перенести исходные из оперативной памяти компьютера в оперативню память GPU. Объем данной памяти много меньше чем объем оперативной памяти компьютера, и так же не имеет файлов подкачки. Так что необходимо отслеживать обьём памяти требуемый для выполнения вычислений. Поэтому выплоняемые вычисления разделяются на множество задач, которые распределяются решаются следующим образом:

![Alt Text](.github/images/MCF_5.jpg)

How we see, in case GPU availability all tasks to which GPU has enough memory is calculated with GPU and other tasks are sent for calculating to CPU, when GPU solve all tasks CPU will send back maximum amount of tasks to GPU. In case GPU absence calculation is run only with СPU. As GPU memory can be used by other apps besides this application, so it's necessary check size of available memory, because its overflow will throw error. For it is used [Pynvml](https://pypi.org/project/pynvml/8.0.3/) library which allow to monitor different GPU parameters.

Как видно из схемы при наличии GPU все вычисления на которые у GPU хватает памяти вычислеться на ней, а оставшиеся отправляются на расчёт CPU, при этом когда GPU решает все задачи CPU возвращает максимальное количество задач в GPU. При этом при отсутвии GPU приложение выполняет расчёты только на СPU. Так как помимо данного приложения память GPU могут испооьзовать и другие приложения, необходимо следить обьемом досутпной памяти, так как её переполнение приводик к ошибке. Для этого испоьзуется библиотека [Pynvml](https://pypi.org/project/pynvml/8.0.3/) которая позволяет мониторить различные параметры GPU.

The application GUI was made with [PyQt5](https://pypi.org/project/PyQt5/5.9/) library. The application window has two main parts: part for showing current sources and receivers magnetic field and calculating areas, and also part for showing geometrical arrangement of elements and calculating results.

GUI приложения разработан при помощи библиотеки [PyQt5](https://pypi.org/project/PyQt5/5.9/). Окно приложения имеет две основыне области: область отображения текущих источников и приёмников магнитного поля и расчётных областей, а так же область отображения геометрического раположения элементов и результатов расчётов. 

![Alt Text](.github/images/MCF_1.jpg)

For showing of calculating results of magnetic field strength for some area is used [Matplotlib](https://pypi.org/project/matplotlib/2.2.2/) library which allow to create color plots for z = f(x, y) functions. Besides it in the right column we can set options (value of magnetic field strength and line color) for creating level lines which show zones that have magnetic field strength values more than in options.

Для отбражения результатов расчёта напряжённости магнитного поля для некторой области используем библиотеку [Matplotlib](https://pypi.org/project/matplotlib/2.2.2/) при помощи которой создаём цветовой график который позваляет отображать функции z = f(x, y). Помимо этого в колонке слева можно задать параметры (величину напряженности магнитного поля и цвет линии) для построения линий уровня которые отображают зоны в которых напряжённость магнитного поля превышает заданную величину.

![Alt Text](.github/images/MCF_2.jpg)

Calculating of induced currents in close circuits is done with [Numpy](https://pypi.org/project/numpy/1.15.0/) и [Scipy](https://pypi.org/project/scipy/1.5.4/) libraries. Showing of results also is done with plot, which shows geometrical arrangement of conductors and currents modules flowing in it, and also there is light indication for current value, which is shown with line color settings.

Расчёт наводимых токов в замкнутых контурах выполняем при помощи библиотек [Numpy](https://pypi.org/project/numpy/1.15.0/) и [Scipy](https://pypi.org/project/scipy/1.5.4/). Отображене результатов также производится на графике, который показывает геометрическое расположение проводников и модуль тока протекающего в нем, а также имеется цветовая индекация величины тока, котороя отображается при помощи задания цвета линиий.

![Alt Text](.github/images/MCF_3.jpg)

The application also can read initial data from *.dxf* files that are created by CAD and write result of calculatings into *.dxf*. For work with *.dxf* files is used [Ezdxf](https://pypi.org/project/ezdxf/0.14.2/) library. This way is very convenient, because instead input geometrical arrangement of elements, we can read them from *.dxf* and output of calculating results into *.dxf* allows to show them on drawings without hand work.

Ещё одной особенность данного приложения являтеся то, что исходные данные для расчётов можно выгружать из CAD систем при помощи файлов формата *.dxf* а так же возвращать в CAD результаты расчётов. Для работы *.dxf* файлами используется библиотека [Ezdxf](https://pypi.org/project/ezdxf/0.14.2/). Данный подход достаточно удобен так как вместо ввода координат расположения элементов,  их можно прочитать из файла *.dxf*. А возвражение результатов в CAD системы позваляет отображатать результы расчётов на чертежах без необходимости ввода их вручную.


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
Для того чтобы использовать данное приложение необходимо установить компоненты с раздела [Used technologies](#Used-technologies). Первоначально установите интерпретатор Python и CUDA Toolkit 10.1, а затем при помощи пакетного менеджера *Pip* запустите установку пакетов следующей командой:

        pip install -r requirements.txt
        
При применении версий пакетов отличных от предложенных работоспособность приложения не гарантируется.

For using the application necessity to install components from section [Used technologies](#Used-technologies). First of all install Python interpreter and CUDA Toolkit 10.1, and after that using package manager *Pip* will run following line:

        pip install -r requirements.txt

In case using versions of packages that differ from the proposed, correct work of the application is not ensured.


## License 
Licensed under the [MIT](LICENSE.txt) license.	
