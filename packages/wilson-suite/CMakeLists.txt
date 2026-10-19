cmake_minimum_required(VERSION 3.25)
project(wilson-suite LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PACKAGE_VERSION "1.0.0")
set(ADD_VERINFO NO)

include(${CMAKE_CURRENT_LIST_DIR}/../../c74support/min-devkit/source/min-api/script/min-package.cmake)

add_subdirectory(source/projects/wilson.core)
add_subdirectory(source/projects/wilson.hexslider)
