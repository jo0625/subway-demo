cmake_minimum_required(VERSION 3.8)
project(subway_patrol_simulation)

find_package(ament_cmake REQUIRED)
find_package(subway_patrol_description REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
