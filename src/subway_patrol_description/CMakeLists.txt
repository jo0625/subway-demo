cmake_minimum_required(VERSION 3.8)
project(subway_patrol_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY urdf/
  DESTINATION share/${PROJECT_NAME}/urdf
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_program(CHECK_URDF_EXECUTABLE check_urdf REQUIRED)
  add_test(
    NAME check_gazebo_train_tf_urdf
    COMMAND ${CHECK_URDF_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/urdf/gazebo_train_tf.urdf
  )
endif()

ament_package()
