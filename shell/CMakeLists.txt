cmake_minimum_required(VERSION 3.20)

# ---- Version metadata
if(NOT DEFINED VERSION)
  execute_process(
    COMMAND git describe --tags --abbrev=0
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    OUTPUT_VARIABLE VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
  )
  if("${VERSION}" STREQUAL "")
    set(VERSION "0.0.0")
  endif()
endif()

if(NOT DEFINED GIT_REVISION)
  execute_process(
    COMMAND git rev-parse HEAD
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    OUTPUT_VARIABLE GIT_REVISION
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
  )
  if("${GIT_REVISION}" STREQUAL "")
    set(GIT_REVISION "unknown")
  endif()
endif()

string(REGEX REPLACE "^v" "" VERSION "${VERSION}")
project(caelestia-shell VERSION ${VERSION} LANGUAGES CXX)

set(QT_QML_GENERATE_QMLLS_INI ON)

option(QT_QML_GENERATE_QMLLS_INI ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# ---- C++ defaults
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")
# Where qt_add_qml_module will stage the built QML module
set(QT_QML_OUTPUT_DIRECTORY        "${CMAKE_BINARY_DIR}/qml")

# ---- Qt deps
find_package(Qt6 6.5 REQUIRED COMPONENTS Core Gui Qml Quick)
qt_standard_project_setup()
qt_policy(SET QTP0001 NEW)
qt_policy(SET QTP0004 OLD)

# ---- Install destinations (per-user by default; override with -D)
set(DISTRIBUTOR "Local" CACHE STRING "Distributor")
set(ENABLE_MODULES "plugin;shell;extras" CACHE STRING "Modules to build/install")

# Per-user defaults; you can still pass system paths explicitly if you want
set(INSTALL_LIBDIR    "$ENV{HOME}/.local/lib/caelestia"        CACHE STRING "Library install dir")
set(INSTALL_QMLDIR    "$ENV{HOME}/.local/lib/qt6/qml"          CACHE STRING "QML install dir")
set(INSTALL_QSCONFDIR "$ENV{HOME}/.config/quickshell/caelestia" CACHE STRING "Quickshell config install dir")

add_compile_options(
  -Wall -Wextra -Wpedantic -Wshadow -Wconversion
  -Wold-style-cast -Wnull-dereference -Wdouble-promotion
  -Wformat=2 -Wfloat-equal -Woverloaded-virtual
  -Wsign-conversion -Wredundant-decls -Wswitch
  -Wunreachable-code
)

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wunused-lambda-capture)
endif()

# ---- Subdirs
if("extras" IN_LIST ENABLE_MODULES)
  add_subdirectory(extras)
endif()

if("plugin" IN_LIST ENABLE_MODULES)
  add_subdirectory(plugin)
endif()

# ---- Helpers
function(qs_mark_qml_singletons)
  foreach(_f IN LISTS ARGN)
    set(_abs "${CMAKE_CURRENT_SOURCE_DIR}/${_f}")
    if(EXISTS "${_abs}")
      file(READ "${_abs}" _src)
      string(FIND "${_src}" "pragma Singleton" _hit)
      if(NOT _hit EQUAL -1)
        set_source_files_properties("${_f}" PROPERTIES QT_QML_SINGLETON_TYPE TRUE)
      endif()
    endif()
  endforeach()
endfunction()


# Components (top-level components + subfolders)
file(GLOB_RECURSE QS_COMPONENTS_QMLS
     CONFIGURE_DEPENDS
     RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
     "${CMAKE_CURRENT_SOURCE_DIR}/components/*.qml")
qs_mark_qml_singletons(${QS_COMPONENTS_QMLS})
qt_add_qml_module(qs_components
    URI qs.components
    VERSION 1.0
    QML_FILES ${QS_COMPONENTS_QMLS}
)

set_target_properties(qs_components PROPERTIES
    QT_QML_OUTPUT_DIRECTORY "${QT_QML_OUTPUT_DIRECTORY}/qs/components"
)

target_link_libraries(qs_components PRIVATE
  Qt6::Qml Qt6::Quick
)

# Config
file(GLOB_RECURSE QS_CONFIG_QMLS
     CONFIGURE_DEPENDS
     RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
     "${CMAKE_CURRENT_SOURCE_DIR}/config/*.qml")
qs_mark_qml_singletons(${QS_CONFIG_QMLS})
qt_add_qml_module(qs_config
    URI qs.config
    VERSION 1.0
    QML_FILES ${QS_CONFIG_QMLS}
)

set_target_properties(qs_config PROPERTIES
    QT_QML_OUTPUT_DIRECTORY "${QT_QML_OUTPUT_DIRECTORY}/qs/config"
)

target_link_libraries(qs_config PRIVATE
  Qt6::Qml Qt6::Quick
)


# Modules
file(GLOB_RECURSE QS_MODULES_QMLS
     CONFIGURE_DEPENDS
     RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
     "${CMAKE_CURRENT_SOURCE_DIR}/modules/*.qml")
qs_mark_qml_singletons(${QS_MODULES_QMLS})
qt_add_qml_module(qs_modules
    URI qs.modules
    VERSION 1.0
    QML_FILES ${QS_MODULES_QMLS}
)

set_target_properties(qs_modules PROPERTIES
    QT_QML_OUTPUT_DIRECTORY "${QT_QML_OUTPUT_DIRECTORY}/qs/modules"
)

target_link_libraries(qs_modules PRIVATE
  Qt6::Qml Qt6::Quick
)

# Services
file(GLOB_RECURSE QS_SERVICES_QMLS
     CONFIGURE_DEPENDS
     RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
     "${CMAKE_CURRENT_SOURCE_DIR}/services/*.qml")
qs_mark_qml_singletons(${QS_SERVICES_QMLS})
qt_add_qml_module(qs_services
    URI qs.services
    VERSION 1.0
    QML_FILES ${QS_SERVICES_QMLS}
)

set_target_properties(qs_services PROPERTIES
    QT_QML_OUTPUT_DIRECTORY "${QT_QML_OUTPUT_DIRECTORY}/qs/services"
)

target_link_libraries(qs_services PRIVATE
  Qt6::Qml Qt6::Quick
)

# Utils
file(GLOB_RECURSE QS_UTILS_QMLS
     CONFIGURE_DEPENDS
     RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
     "${CMAKE_CURRENT_SOURCE_DIR}/utils/*.qml")
qs_mark_qml_singletons(${QS_UTILS_QMLS})
qt_add_qml_module(qs_utils
    URI qs.utils
    VERSION 1.0
    QML_FILES ${QS_UTILS_QMLS}
)

set_target_properties(qs_utils PROPERTIES
    QT_QML_OUTPUT_DIRECTORY "${QT_QML_OUTPUT_DIRECTORY}/qs/utils"
)

target_link_libraries(qs_utils PRIVATE
  Qt6::Qml Qt6::Quick
)

# ---- Install shell assets & entry points
if("shell" IN_LIST ENABLE_MODULES)
  foreach(dir assets components config modules services utils)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/${dir}")
      install(DIRECTORY ${dir} DESTINATION "${INSTALL_QSCONFDIR}")
    endif()
  endforeach()
  if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/shell.qml")
    install(FILES shell.qml DESTINATION "${INSTALL_QSCONFDIR}")
  endif()
  if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
    install(FILES LICENSE   DESTINATION "${INSTALL_QSCONFDIR}")
  endif()
endif()

# ---- “uninstall” target for cleaning user installs
configure_file(
  "${CMAKE_CURRENT_SOURCE_DIR}/cmake/cmake_uninstall.cmake.in"
  "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
  IMMEDIATE @ONLY
)
add_custom_target(uninstall
  COMMAND ${CMAKE_COMMAND} -P "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
)
