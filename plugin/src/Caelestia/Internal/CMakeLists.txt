qml_module(caelestia-internal
    URI Caelestia.Internal
    SOURCES
        cachingimagemanager.hpp cachingimagemanager.cpp
        circularindicatormanager.hpp circularindicatormanager.cpp
        hyprdevices.hpp hyprdevices.cpp
        hyprextras.hpp hyprextras.cpp
        idleinhibitor.hpp idleinhibitor.cpp
        idlemonitor.hpp idlemonitor.cpp
        logindmanager.hpp logindmanager.cpp
    LIBRARIES
        Qt::Gui
        Qt::Quick
        Qt::Concurrent
        Qt::Network
        Qt::DBus
)
