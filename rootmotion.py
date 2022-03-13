# Copyright (c) 2022 ywabygl@gmail.com
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
from mathutils import Quaternion, Vector
import bpy
from bpy.props import StringProperty, BoolProperty, PointerProperty, EnumProperty
from bpy.types import Operator, Panel


def quat_separate_y(quat: Quaternion):
    qm = quat.to_matrix()
    x_axis = qm[0][0:3]
    angle = Vector([x_axis[0], x_axis[2]])
    angle = angle.angle_signed(Vector((1, 0)))
    y_quat = Quaternion(Vector((0, 1, 0)), angle)
    return y_quat, y_quat.rotation_difference(quat)


class MIXAMO_OT_AddRootMotion(Operator):
    """add root bone and root motion to current action"""
    bl_idname = "mixamo.add_root_motion"
    bl_label = "Add Root Motion "
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.context):
        obj = context.object
        return obj and \
            obj.type == 'ARMATURE'

    def execute(self, context:  bpy.context):
        obj = context.object
        action: bpy.types.Action = obj.animation_data.action
        fcurves = action.fcurves
        # add root bone if not exist
        if "root" not in obj.data.bones:
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            root = obj.data.edit_bones.new('root')
            root.head = (0, 0, 0)
            root.tail = (0, 0, 0.25)
            obj.data.edit_bones['hips'].parent = root
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        # root location xz=root xz,
        fcurves.find(data_path='pose.bones["hips"].location',
                     index=0).data_path = 'pose.bones["root"].location'
        fcurves.find(data_path='pose.bones["hips"].location',
                     index=2).data_path = 'pose.bones["root"].location'

        fc_root_locy = fcurves.new('pose.bones["root"].location', index=1)
        fc_hips_locy = fcurves.find(data_path='pose.bones["hips"].location',
                                    index=1)

        fc_hips_quat0 = fcurves.find(
            'pose.bones["hips"].rotation_quaternion', index=0)
        fc_hips_quat1 = fcurves.find(
            'pose.bones["hips"].rotation_quaternion', index=1)
        fc_hips_quat2 = fcurves.find(
            'pose.bones["hips"].rotation_quaternion', index=2)
        fc_hips_quat3 = fcurves.find(
            'pose.bones["hips"].rotation_quaternion', index=3)
        fc_root_quat0 = fcurves.new(
            'pose.bones["root"].rotation_quaternion', index=0)
        fc_root_quat1 = fcurves.new(
            'pose.bones["root"].rotation_quaternion', index=1)
        fc_root_quat2 = fcurves.new(
            'pose.bones["root"].rotation_quaternion', index=2)
        fc_root_quat3 = fcurves.new(
            'pose.bones["root"].rotation_quaternion', index=3)

        # root location y=0
        fc_root_locy.keyframe_points.insert(action.frame_range[0], 0)

        # root rotation y == hips rotation y
        for i in   fc_hips_quat0.keyframe_points.items(): 
            k=i[0]
            frame = i[1].co.x
            hips_quat = Quaternion((
                fc_hips_quat0.keyframe_points[k].co.y,
                fc_hips_quat1.keyframe_points[k].co.y,
                fc_hips_quat2.keyframe_points[k].co.y,
                fc_hips_quat3.keyframe_points[k].co.y,
            ))
            root_quat, hips_quat = quat_separate_y(hips_quat)
            fc_hips_quat0.keyframe_points[k].co.y = hips_quat.w
            fc_hips_quat1.keyframe_points[k].co.y = hips_quat.x
            fc_hips_quat2.keyframe_points[k].co.y = hips_quat.y
            fc_hips_quat3.keyframe_points[k].co.y = hips_quat.z
            fc_root_quat0.keyframe_points.insert(frame, root_quat[0])
            fc_root_quat1.keyframe_points.insert(frame, root_quat[1])
            fc_root_quat2.keyframe_points.insert(frame, root_quat[2])
            fc_root_quat3.keyframe_points.insert(frame, root_quat[3])
        return{'FINISHED'}

class MIXAMO_PT_RootMotion(Panel):
    """Root Motion UI"""
    bl_label = "Root Motion"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Mixamo"

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        scene = context.scene
        box = layout.box()
        row = box.row()
        row.operator("mixamo.add_root_motion")


classes = (
    MIXAMO_PT_RootMotion,
    MIXAMO_OT_AddRootMotion,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
