cmake_minimum_required(VERSION 3.18)

project(nexus_native
    VERSION     0.1.0
    DESCRIPTION "NEXUS Native Engine — C++ acceleration layer for trading computations"
    LANGUAGES   CXX
)

# ===========================================================
# C++ standard
# ===========================================================
set(CMAKE_CXX_STANDARD          17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS        OFF)


# ===========================================================
# Default build type
# ===========================================================
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING
        "Build type (Debug|Release|RelWithDebInfo)" FORCE)
endif()
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")


# ===========================================================
# Compiler flags
# ===========================================================
if(MSVC)
    # Windows / MSVC
    add_compile_options(
        /W4         # warning level 4
        /WX-        # warnings are not errors (pybind11 headers may warn)
        /wd4100     # suppress: unreferenced formal parameter (stubs use (void)x)
    )
    # Release: full optimisation + AVX2 (if available)
    add_compile_options("$<$<CONFIG:Release>:/O2;/arch:AVX2>")
    add_compile_options("$<$<CONFIG:Debug>:/Od;/Zi>")
else()
    # GCC / Clang (Linux, macOS)
    add_compile_options(
        -Wall
        -Wextra
        -Wno-unused-parameter   # stubs deliberately suppress params with (void)x
    )
    add_compile_options("$<$<CONFIG:Release>:-O3;-march=native;-ffast-math>")
    add_compile_options("$<$<CONFIG:Debug>:-O0;-g;-fsanitize=address>")
    if(CMAKE_BUILD_TYPE STREQUAL "Debug")
        add_link_options(-fsanitize=address)
    endif()
endif()


# ===========================================================
# Python discovery
# ===========================================================
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development)
message(STATUS "Python interpreter: ${Python_EXECUTABLE}")
message(STATUS "Python version:     ${Python_VERSION}")
message(STATUS "Python include:     ${Python_INCLUDE_DIRS}")


# ===========================================================
# pybind11 discovery / automatic fetch
# ===========================================================
find_package(pybind11 2.10 QUIET CONFIG)

if(pybind11_FOUND)
    message(STATUS "Found pybind11 ${pybind11_VERSION} (system install)")
else()
    message(STATUS "pybind11 not found — fetching v2.13.6 via FetchContent")
    include(FetchContent)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG        v2.13.6
        GIT_SHALLOW    TRUE
    )
    FetchContent_MakeAvailable(pybind11)
endif()


# ===========================================================
# Source files
# ===========================================================
set(NEXUS_CPP_SOURCES
    cpp/engine.cpp
    cpp/indicators.cpp
    cpp/risk.cpp
    cpp/bindings.cpp
)

set(NEXUS_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/include)


# ===========================================================
# pybind11 extension module target
# ===========================================================
pybind11_add_module(nexus_native_ext MODULE ${NEXUS_CPP_SOURCES})

target_include_directories(nexus_native_ext
    PRIVATE ${NEXUS_INCLUDE_DIR}
)

# Version definition accessible at compile time
target_compile_definitions(nexus_native_ext PRIVATE
    NEXUS_NATIVE_VERSION="0.1.0-alpha"
    NEXUS_NATIVE_PHASE="CPP-2"
)


# ===========================================================
# Output location
# Place the compiled .so / .pyd alongside the Python bridge so
# `python_bridge/nexus_native.py` can `import nexus_native_ext`
# without any sys.path manipulation beyond its own directory.
# ===========================================================
set(_OUTPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/python_bridge")

set_target_properties(nexus_native_ext PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY                "${_OUTPUT_DIR}"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE        "${_OUTPUT_DIR}"
    LIBRARY_OUTPUT_DIRECTORY_DEBUG          "${_OUTPUT_DIR}"
    RUNTIME_OUTPUT_DIRECTORY                "${_OUTPUT_DIR}"   # Windows .dll
    RUNTIME_OUTPUT_DIRECTORY_RELEASE        "${_OUTPUT_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG          "${_OUTPUT_DIR}"
)

message(STATUS "Extension output directory: ${_OUTPUT_DIR}")


# ===========================================================
# Install rules (optional — for packaging)
# ===========================================================
install(TARGETS nexus_native_ext
    LIBRARY DESTINATION "${CMAKE_INSTALL_PREFIX}/python_bridge"
    RUNTIME DESTINATION "${CMAKE_INSTALL_PREFIX}/python_bridge"
)

install(DIRECTORY include/
    DESTINATION "${CMAKE_INSTALL_PREFIX}/include/nexus_native"
    FILES_MATCHING PATTERN "*.hpp"
)


# ===========================================================
# Build summary
# ===========================================================
message(STATUS "")
message(STATUS "=== NEXUS Native Engine ===")
message(STATUS "  Version  : ${PROJECT_VERSION}")
message(STATUS "  Phase    : CPP-2 (infrastructure)")
message(STATUS "  Python   : ${Python_VERSION}")
message(STATUS "  Compiler : ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "  Output   : ${_OUTPUT_DIR}/nexus_native_ext<suffix>")
message(STATUS "")
message(STATUS "Quick build:")
message(STATUS "  cmake -B build -DCMAKE_BUILD_TYPE=Release")
message(STATUS "  cmake --build build --config Release -j4")
message(STATUS "")
