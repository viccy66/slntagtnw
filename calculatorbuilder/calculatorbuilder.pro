#! [0]
HEADERS     = calculatorform.h
RESOURCES   = calculatorbuilder.qrc
SOURCES     = calculatorform.cpp \
              main.cpp
QT += core  gui  widgets uitools
#! [0]

target.path = $$[QT_INSTALL_EXAMPLES]/designer/calculatorbuilder
INSTALLS += target

TEMPLATE = app

TARGET = calculatorbuilder

FORMS += \
    calculatorform.ui \

CONFIG += c++17

QMAKE_CXXFLAGS += -fPIC

QMAKE_CXXFLAGS += -Wno-deprecated-declarations

QMAKE_CXXFLAGS += -Wno-unused-parameter

QMAKE_CXXFLAGS += -Wno-unused-variable
