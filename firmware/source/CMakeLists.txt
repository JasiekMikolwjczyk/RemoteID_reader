# CMakeLists.txt for ESP32-S3 Remote ID Sniffer
cmake_minimum_required(VERSION 3.16)

# Set the ESP32-S3 as the target
set(CMAKE_TOOLCHAIN_FILE "$ENV{IDF_PATH}/tools/cmake/toolchain-esp32s3.cmake")

include($ENV{IDF_PATH}/tools/cmake/project.cmake)

project(esp32s3_remote_id_sniffer)

# Add custom partitions table if needed
# set(PARTITION_TABLE_CUSTOM_FILENAME "partitions.csv")