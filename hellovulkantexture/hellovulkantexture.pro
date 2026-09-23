HEADERS += hellovulkantexture.h
SOURCES += hellovulkantexture.cpp main.cpp
RESOURCES += hellovulkantexture.qrc

# install
target.path = $$[QT_INSTALL_EXAMPLES]/vulkan/hellovulkantexture
INSTALLS += target

TEMPLATE = app

TARGET = hellovulkantexture

QT += widgets gui core

CONFIG += c++17

QMAKE_CXXFLAGS += -fPIC

QMAKE_CXXFLAGS += -Wno-deprecated-declarations

QMAKE_CXXFLAGS += -Wno-unused-parameter

QMAKE_CXXFLAGS += -Wno-unused-variable
