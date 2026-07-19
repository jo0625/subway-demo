# subway_patrol_description

ROS 2 description package for robot URDF/Xacro files, meshes, collision geometry,
inertial properties, joints, and sensor mounting frames.

The active simulation TF description is installed as:

```text
share/subway_patrol_description/urdf/gazebo_train_tf.urdf
```

The legacy repository-level `urdf/gazebo_train_tf.urdf` path is a compatibility
symlink so existing scripts continue to work while launch files are migrated to
package discovery. Experimental custom-robot descriptions remain outside this
package until the model branch provides a stable version.
