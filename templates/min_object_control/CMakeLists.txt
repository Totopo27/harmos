cmake_minimum_required(VERSION 3.25)
project(min_control_template LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Incluir macros y configuración del min-devkit
# Se asume que c74support o min-devkit está en el path del paquete de Max
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../c74support/min-devkit")
    include("${CMAKE_CURRENT_SOURCE_DIR}/../../c74support/min-devkit/script/min-package.cmake")
    min_add_external(min_control_template min_control_template.cpp)
endif()
