cmake_minimum_required(VERSION 3.25)
project(wilson_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Si c74support o min-devkit está presente, compilar el external
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../c74support/min-devkit")
    include("${CMAKE_CURRENT_SOURCE_DIR}/../../c74support/min-devkit/script/min-package.cmake")
    min_add_external(wilson.core wilson_core.cpp)
    min_add_external(wilson.hexslider wilson_hexslider.cpp)
else()
    # Target de verificación sintáctica estándar en Windows MSVC
    add_library(wilson_core_test OBJECT wilson_core.cpp wilson_hexslider.cpp)
    target_include_directories(wilson_core_test PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/../../templates/min_object_control")
endif()
