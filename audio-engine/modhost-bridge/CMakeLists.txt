cmake_minimum_required(VERSION 3.16)
project(modhost-bridge-cpp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# (Autobuild of mod-host removed) The bridge no longer includes a build-time option to build mod-host.

# Find ZeroMQ manually
find_path(ZMQ_INCLUDE_DIR zmq.hpp PATHS /usr/include /usr/local/include)
find_library(ZMQ_LIBRARY zmq PATHS /usr/lib /usr/local/lib /usr/lib/x86_64-linux-gnu)

if(NOT ZMQ_INCLUDE_DIR OR NOT ZMQ_LIBRARY)
    message(FATAL_ERROR "ZeroMQ not found. Please install libzmq3-dev")
endif()

# Find jsoncpp
find_path(JSONCPP_INCLUDE_DIR jsoncpp/json/json.h PATHS /usr/include)
find_library(JSONCPP_LIBRARY jsoncpp PATHS /usr/lib /usr/local/lib /usr/lib/x86_64-linux-gnu /usr/lib64)

if(NOT JSONCPP_INCLUDE_DIR OR NOT JSONCPP_LIBRARY)
    message(FATAL_ERROR "jsoncpp not found. Please install libjsoncpp-dev")
endif()

# Find spdlog
find_path(SPDLOG_INCLUDE_DIR spdlog/spdlog.h PATHS /usr/include /usr/local/include)
find_library(SPDLOG_LIBRARY spdlog PATHS /usr/lib /usr/local/lib /usr/lib/x86_64-linux-gnu)
if(NOT SPDLOG_INCLUDE_DIR OR NOT SPDLOG_LIBRARY)
    message(FATAL_ERROR "spdlog not found. Please install libspdlog-dev")
endif()

# Find fmt (required by spdlog)
find_path(FMT_INCLUDE_DIR fmt/core.h PATHS /usr/include /usr/local/include)
find_library(FMT_LIBRARY fmt PATHS /usr/lib /usr/local/lib /usr/lib/x86_64-linux-gnu)
if(NOT FMT_INCLUDE_DIR OR NOT FMT_LIBRARY)
    message(FATAL_ERROR "fmt not found. Please install libfmt-dev")
endif()

# Find MOD utils library
find_path(MOD_UTILS_INCLUDE_DIR utils.h PATHS ${CMAKE_SOURCE_DIR}/../utils)
find_library(MOD_UTILS_LIBRARY mod_utils PATHS ${CMAKE_SOURCE_DIR}/../utils)

if(NOT MOD_UTILS_INCLUDE_DIR OR NOT MOD_UTILS_LIBRARY)
    message(FATAL_ERROR "MOD utils library not found. Please build the utils library first. MOD_UTILS_INCLUDE_DIR: ${MOD_UTILS_INCLUDE_DIR}, MOD_UTILS_LIBRARY: ${MOD_UTILS_LIBRARY}")
endif()

# Find MOD host headers
find_path(MOD_HOST_INCLUDE_DIR mod-host.h PATHS ${CMAKE_SOURCE_DIR}/../mod-host/src)

if(NOT MOD_HOST_INCLUDE_DIR)
    message(FATAL_ERROR "MOD host headers not found. MOD_HOST_INCLUDE_DIR: ${MOD_HOST_INCLUDE_DIR}")
endif()

# Include directories
include_directories(${ZMQ_INCLUDE_DIR})
include_directories(/usr/include/jsoncpp)
include_directories(${SPDLOG_INCLUDE_DIR})
include_directories(${FMT_INCLUDE_DIR})
include_directories(${MOD_UTILS_INCLUDE_DIR})
include_directories(${MOD_HOST_INCLUDE_DIR})

# Autobuild support removed; no custom build targets are created for mod-host.

# Add executable
add_executable(modhost-bridge
    src/main.cpp
    src/utils/types.cpp
    src/utils/parser.cpp
    src/core/feedback_reader.cpp
    src/core/command_service.cpp
    src/core/health_monitor.cpp
    src/plugins/plugin_manager.cpp
    src/plugins/plugin_scanner.cpp
    src/plugins/plugin_bundle_monitor.cpp
    src/plugins/plugin_validator.cpp
    src/plugins/plugin_search_engine.cpp
)

# Link libraries
target_link_libraries(modhost-bridge
    ${ZMQ_LIBRARY}
    ${JSONCPP_LIBRARY}
    ${SPDLOG_LIBRARY}
    ${FMT_LIBRARY}
    ${MOD_UTILS_LIBRARY}
    pthread
)

# Compiler flags
target_compile_options(modhost-bridge PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -O2
)

# Install target
install(TARGETS modhost-bridge
    RUNTIME DESTINATION bin
)