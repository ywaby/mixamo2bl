# Copyright (c) 2022 ywabygl@gmail.com
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import bpy
import os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, PointerProperty
from bpy.types import Operator

bl_info = {
    "name": "Mixamo Import",
    "author": "ywaby",
    "version": (0, 1, 0),
    "blender": (3, 0, 0),
    "location": "3D View > UI (Right Panel) > Mixamo Tab",
    "description": ("Import mixamo animations"),
    "warning": "",
    "wiki_url": "https://github.com/ywaby/mixamo2bl",
    "tracker_url": "https://github.com/ywaby/mixamo2bl/issues",
    "category": "Import-Export",
    "support": "COMMUNITY",
}


bone_rename_maps = {
    # 'root': 'root',
    'mixamorig:Hips': 'hips',
    'mixamorig:Spine': 'spine_01',
    'mixamorig:Spine1': 'spine_02',
    'mixamorig:Spine2': 'spine_03',
    'mixamorig:LeftShoulder': 'shoulder_l',
    'mixamorig:LeftArm': 'upperarm_l',
    'mixamorig:LeftForeArm': 'lowerarm_l',
    'mixamorig:LeftHand': 'hand_l',
    'mixamorig:RightShoulder': 'shoulder_r',
    'mixamorig:RightArm': 'upperarm_r',
    'mixamorig:RightForeArm': 'lowerarm_r',
    'mixamorig:RightHand': 'hand_r',
    'mixamorig:Head': 'head',
    'mixamorig:Neck': 'neck',
    'mixamorig:LeftEye': 'eye_l',
    'mixamorig:RightEye': 'eye_r',
    'mixamorig:LeftUpLeg': 'thigh_l',
    'mixamorig:LeftLeg': 'shin_l',
    'mixamorig:LeftFoot': 'foot_l',
    'mixamorig:RightUpLeg': 'thigh_r',
    'mixamorig:RightLeg': 'shin_r',
    'mixamorig:RightFoot': 'foot_r',
    'mixamorig:LeftHandIndex1': 'index_01_l',
    'mixamorig:LeftHandIndex2': 'index_02_l',
    'mixamorig:LeftHandIndex3': 'index_03_l',
    'mixamorig:LeftHandMiddle1': 'middle_01_l',
    'mixamorig:LeftHandMiddle2': 'middle_02_l',
    'mixamorig:LeftHandMiddle3': 'middle_03_l',
    'mixamorig:LeftHandPinky1': 'pinky_01_l',
    'mixamorig:LeftHandPinky2': 'pinky_02_l',
    'mixamorig:LeftHandPinky3': 'pinky_03_l',
    'mixamorig:LeftHandRing1': 'ring_01_l',
    'mixamorig:LeftHandRing2': 'ring_02_l',
    'mixamorig:LeftHandRing3': 'ring_03_l',
    'mixamorig:LeftHandThumb1': 'thumb_01_l',
    'mixamorig:LeftHandThumb2': 'thumb_02_l',
    'mixamorig:LeftHandThumb3': 'thumb_03_l',
    'mixamorig:RightHandIndex1': 'index_01_r',
    'mixamorig:RightHandIndex2': 'index_02_r',
    'mixamorig:RightHandIndex3': 'index_03_r',
    'mixamorig:RightHandMiddle1': 'middle_01_r',
    'mixamorig:RightHandMiddle2': 'middle_02_r',
    'mixamorig:RightHandMiddle3': 'middle_03_r',
    'mixamorig:RightHandPinky1': 'pinky_01_r',
    'mixamorig:RightHandPinky2': 'pinky_02_r',
    'mixamorig:RightHandPinky3': 'pinky_03_r',
    'mixamorig:RightHandRing1': 'ring_01_r',
    'mixamorig:RightHandRing2': 'ring_02_r',
    'mixamorig:RightHandRing3': 'ring_03_r',
    'mixamorig:RightHandThumb1': 'thumb_01_r',
    'mixamorig:RightHandThumb2': 'thumb_02_r',
    'mixamorig:RightHandThumb3': 'thumb_03_r',
    'mixamorig:LeftToeBase': 'toe_l',
    'mixamorig:RightToeBase': 'toe_r'
}


def action_2_NAL(arm_obj, action: bpy.types.Action):
    # add  action to NAL
    arm_obj.animation_data.action = action
    track = arm_obj.animation_data.nla_tracks.new()
    track.name = action.name
    track.mute = True
    strip = track.strips.new(action.name, action.frame_range[0], action)


def scale_animation(fcurves: list[bpy.types.FCurve], scale):
    for fc in fcurves:
        # TODO how to know fcurve location xyz
        if fc.data_path.endswith('.location'):
            for key in fc.keyframe_points:
                val = key.co_ui
                val.y *= scale.x


class MIXAMO_OT_ImportCharater(Operator, ImportHelper):
    '''Import mixamo character with skin (*.fbx) for animation to merge in'''
    bl_idname = "mixamo.import_character"
    bl_label = "Import Mixamo Character"
    directory = StringProperty(
        name="Character Dir",
    )
    filter_glob: StringProperty(
        default="*.fbx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context:  bpy.context):
        mixamo_fix_import_fbx(context, self.filepath)
        armature = context.active_object
        armature.is_mixamo_character = True
        action_2_NAL(armature, armature.animation_data.action)
        return{'FINISHED'}

def mixamo_fix_import_fbx(context, dir:str):
    """import mixamo (*.fbx), 
    rename ,
    fix scale,
    add root motion, 
    etc. 
    """
    file = os.path.basename(dir)
    print(f"input file:{dir}")
    name, ext = os.path.splitext(file)
    bpy.ops.import_scene.fbx(
        filepath=dir,
        ignore_leaf_bones=context.scene.mixamo.ignore_leaf_bones,
        automatic_bone_orientation=True)
    anim_data:bpy.types.AnimData = context.active_object.animation_data
    armature: bpy.types.Armature = context.active_object.data
    action = anim_data.action
    fcurves=action.fcurves
    # rename Action
    action.name = name
    # rename bones
    for k, v in bone_rename_maps.items():
        if k in armature.bones:
            armature.bones[k].name = v

    # fix scale
    scale = context.active_object.scale
    scale_animation(fcurves, scale)

    # fix rotation
    bpy.ops.object.transform_apply(
        location=True, rotation=True, scale=True)

    # add root motion from hips
    if context.scene.mixamo.add_root_motion:
        #TODO direct copy fcurve data from hips to root
        # add root bone
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        root = armature.edit_bones.new('root')
        root.head = (0, 0, 0)
        root.tail = (0, 0, 0.5)
        armature.edit_bones['hips'].parent = root
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        # hips location to rootbone
        fcurves.find(data_path='pose.bones["hips"].location',index=0).data_path='pose.bones["root"].location'
        fcurves.find(data_path='pose.bones["hips"].location',index=1).data_path='pose.bones["root"].location'
        fcurves.find(data_path='pose.bones["hips"].location',index=2).data_path='pose.bones["root"].location'


class MIXAMO_OT_Update(Operator):
    '''Update all mixamo file in dir'''
    bl_idname = "mixamo.update"
    bl_label = "Update Mixamo"
    bl_description = "Update all mixamo from the input dir if action not exist."

    @classmethod
    def poll(cls, context: bpy.context):
        bpy.context.scene.frame_set(1)
        return True

    def execute(self, context: bpy.context):
        # find mixamo character
        target_arms = [object for object in context.scene.objects
                       if object.is_mixamo_character]
        if len(target_arms) == 0:
            self.report({'WARNING'},
                        'Not Found mixamo character in current scene.')
            return {'CANCELLED'}
        if len(target_arms) == 1:
            self.target_arm = target_arms[0]
        else:
            self.report({'WARNING'},
                        'Too many mixamo character in current scene.')
            return {'CANCELLED'}

        input_path = context.scene.mixamo.input_dir
        files = os.listdir(input_path)
        for file in files:
            name, ext = os.path.splitext(file)
            dir = os.path.join(input_path, file)
            if name in bpy.data.actions:  # if exist, pass
                continue
            if ext == '.fbx':
                mixamo_fix_import_fbx(context, dir)
                # add animation  to NAL
                action_2_NAL(self.target_arm, bpy.data.actions[name])
                # remove
                bpy.ops.object.delete()
            elif ext == '.gltf':
                continue  # TODO
            else:
                continue
        return{'FINISHED'}



class MIXAMO_PT_Main(bpy.types.Panel):
    """Mixamo Import UI"""
    bl_label = "Mixamo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Mixamo"

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        obj = context.active_object
        if obj is not None and obj.type == 'ARMATURE':
            box = layout.box()
            row = box.row()
            row.prop(context.active_object, "is_mixamo_character")
        box = layout.box()
        row = box.row()
        row.label(text="Import Option")
        row = box.row()
        row.prop(scene.mixamo, 'ignore_leaf_bones')
        row = box.row()
        row.prop(scene.mixamo, 'add_root_motion')
        box = layout.box()
        row = box.row()
        row.operator("mixamo.import_character")
        box = layout.box()
        row = box.row()
        row.prop(scene.mixamo, "input_dir")
        row = box.row()
        row.operator("mixamo.update")


class MixamoPropertyGroup(bpy.types.PropertyGroup):
    input_dir: StringProperty(
        name="mixamo Path",
        description="Path to mixamo",
        maxlen=256,
        default="",
        subtype='DIR_PATH')
    add_root_motion: BoolProperty(
        name='Add Root Motion',
        description='Add root bone and copy motion from hips',
        default=False)
    ignore_leaf_bones: BoolProperty(
        name='Ignore_Leaf Bones',
        description='Remove Leaf Bones ',
        default=False)

classes = (
    MixamoPropertyGroup,
    MIXAMO_OT_ImportCharater,
    MIXAMO_OT_Update,
    MIXAMO_PT_Main
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mixamo = PointerProperty(
        type=MixamoPropertyGroup)
    bpy.types.Object.is_mixamo_character = BoolProperty(
        name='is mixamo character',
        description='Merge animation to this object',
        default=False)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.mixamo
    del bpy.types.Object.is_mixamo_character


if __name__ == "__main__":
    register()
