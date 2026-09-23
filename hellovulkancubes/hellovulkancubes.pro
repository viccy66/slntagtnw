QT += core  gui  widgets concurrent

HEADERS += \
    mainwindow.h \
    vulkanwindow.h \
    renderer.h \
    mesh.h \
    shader.h \
    camera.h

SOURCES += \
    main.cpp \
    mainwindow.cpp \
    vulkanwindow.cpp \
    renderer.cpp \
    mesh.cpp \
    shader.cpp \
    camera.cpp

RESOURCES += hellovulkancubes.qrc

# install
target.path = $$[QT_INSTALL_EXAMPLES]/vulkan/hellovulkancubes
INSTALLS += target

TEMPLATE = app

TARGET = hellovulkancubes

CONFIG += c++17

QMAKE_CXXFLAGS += -fPIC

QMAKE_CXXFLAGS += -Wno-deprecated-declarations

QMAKE_CXXFLAGS += -Wno-unused-parameter

QMAKE_CXXFLAGS += -Wno-unused-variable
