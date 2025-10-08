# CMakeLists.txt for MOD utils library

cmake_minimum_required(VERSION 3.16)
project(mod-utils VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required dependencies
find_package(PkgConfig REQUIRED)

# Find JACK
pkg_check_modules(JACK REQUIRED jack)

# Find LiLV
pkg_check_modules(LILV REQUIRED lilv-0)

# Find ALSA (optional)
pkg_check_modules(ALSA alsa)

# Include directories
include_directories(${JACK_INCLUDE_DIRS})
include_directories(${LILV_INCLUDE_DIRS})
if(ALSA_FOUND)
    include_directories(${ALSA_INCLUDE_DIRS})
    add_definitions(-DHAVE_ALSA)
endif()

# Source files
set(SOURCES
    utils_jack.cpp
    utils_lilv.cpp
    sha1/sha1.c
)

# Create static library
add_library(mod_utils STATIC ${SOURCES})

# Link libraries
target_link_libraries(mod_utils
    ${JACK_LIBRARIES}
    ${LILV_LIBRARIES}
)

if(ALSA_FOUND)
    target_link_libraries(mod_utils ${ALSA_LIBRARIES})
endif()

# Add link flags for proper library linking
target_link_options(mod_utils PRIVATE ${JACK_LDFLAGS} ${LILV_LDFLAGS})

# Compiler flags
target_compile_options(mod_utils PRIVATE
    -Wall
    -Wextra
    -O2
)

# Installation
install(TARGETS mod_utils
    ARCHIVE DESTINATION lib
)

install(FILES utils.h
    DESTINATION include
)