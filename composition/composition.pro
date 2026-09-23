SOURCES += main.cpp composition.cpp
HEADERS += composition.h

SHARED_FOLDER = ../shared

include($$SHARED_FOLDER/shared.pri)

RESOURCES += composition.qrc
QT += core  gui  widgets

# install
target.path = $$[QT_INSTALL_EXAMPLES]/widgets/painting/composition
INSTALLS += target

TEMPLATE = app

TARGET = composition

CONFIG += c++17

QMAKE_CXXFLAGS += -fPIC

QMAKE_CXXFLAGS += -Wno-deprecated-declarations

QMAKE_CXXFLAGS += -Wno-unused-parameter

QMAKE_CXXFLAGS += -Wno-unused-variable
