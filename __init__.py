# Copyright (c) 2022 ywabygl@gmail.com
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# notes


from distutils.command.sdist import sdist
import bpy
import os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, PointerProperty
from bpy.types import Operator

bl_info = {
    "name": "Mixamo Import",
    "author": "ywaby",
    "version": (0, 1, 1),
    "blender": (3, 0, 0),
    "location": "3D View > UI (Right Panel) > Mixamo Tab",
    "description": ("Import And Update mixamo animations"),
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
    'mixamorig:LeftShoulder': 'shoulder_L',
    'mixamorig:LeftArm': 'upperarm_L',
    'mixamorig:LeftForeArm': 'lowerarm_L',
    'mixamorig:LeftHand': 'hand_L',
    'mixamorig:RightShoulder': 'shoulder_R',
    'mixamorig:RightArm': 'upperarm_R',
    'mixamorig:RightForeArm': 'lowerarm_R',
    'mixamorig:RightHand': 'hand_R',
    'mixamorig:Head': 'head',
    'mixamorig:Neck': 'neck',
    'mixamorig:LeftEye': 'eye_L',
    'mixamorig:RightEye': 'eye_R',
    'mixamorig:LeftUpLeg': 'thigh_L',
    'mixamorig:LeftLeg': 'shin_L',
    'mixamorig:LeftFoot': 'foot_L',
    'mixamorig:RightUpLeg': 'thigh_R',
    'mixamorig:RightLeg': 'shin_R',
    'mixamorig:RightFoot': 'foot_R',
    'mixamorig:LeftHandIndex1': 'index_01_L',
    'mixamorig:LeftHandIndex2': 'index_02_L',
    'mixamorig:LeftHandIndex3': 'index_03_L',
    'mixamorig:LeftHandMiddle1': 'middle_01_L',
    'mixamorig:LeftHandMiddle2': 'middle_02_L',
    'mixamorig:LeftHandMiddle3': 'middle_03_L',
    'mixamorig:LeftHandPinky1': 'pinky_01_L',
    'mixamorig:LeftHandPinky2': 'pinky_02_L',
    'mixamorig:LeftHandPinky3': 'pinky_03_L',
    'mixamorig:LeftHandRing1': 'ring_01_L',
    'mixamorig:LeftHandRing2': 'ring_02_L',
    'mixamorig:LeftHandRing3': 'ring_03_L',
    'mixamorig:LeftHandThumb1': 'thumb_01_L',
    'mixamorig:LeftHandThumb2': 'thumb_02_L',
    'mixamorig:LeftHandThumb3': 'thumb_03_L',
    'mixamorig:RightHandIndex1': 'index_01_R',
    'mixamorig:RightHandIndex2': 'index_02_R',
    'mixamorig:RightHandIndex3': 'index_03_R',
    'mixamorig:RightHandMiddle1': 'middle_01_R',
    'mixamorig:RightHandMiddle2': 'middle_02_R',
    'mixamorig:RightHandMiddle3': 'middle_03_R',
    'mixamorig:RightHandPinky1': 'pinky_01_R',
    'mixamorig:RightHandPinky2': 'pinky_02_R',
    'mixamorig:RightHandPinky3': 'pinky_03_R',
    'mixamorig:RightHandRing1': 'ring_01_R',
    'mixamorig:RightHandRing2': 'ring_02_R',
    'mixamorig:RightHandRing3': 'ring_03_R',
    'mixamorig:RightHandThumb1': 'thumb_01_R',
    'mixamorig:RightHandThumb2': 'thumb_02_R',
    'mixamorig:RightHandThumb3': 'thumb_03_R',
    'mixamorig:LeftToeBase': 'toe_L',
    'mixamorig:RightToeBase': 'toe_R'
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
        if fc.data_path.endswith('.location'):
            for key in fc.keyframe_points:
                val = key.co_ui
                val.y *= scale.x


class MIXAMO_OT_ImportCharater(Operator, ImportHelper):
    '''Import mixamo character with skin (*.fbx) for animation to merge in'''
    bl_idname = "mixamo.import_character"
    bl_label = "Import Mixamo Character"
    filter_glob: StringProperty(
        default="*.fbx;*.dae",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    filter_folder : BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})

    filename: StringProperty(
        name="File Name",
    )
    def execute(self, context:  bpy.context):
        name, ext = os.path.splitext(self.filename)
        if ext == '.fbx':
            mixamo_fix_import_fbx(context, self.filepath)
        elif ext == '.dae':
            mixamo_fix_import_dae(context, self.filepath)
        else:
            return {'CANCELLED'}
        armature = context.active_object
        action_2_NAL(armature, armature.animation_data.action)
        context.scene.mixamo_character = armature
        context.scene.mixamo.input_folder = os.path.dirname(self.filepath)
        return{'FINISHED'}


def mixamo_fix_import_dae(context: bpy.context, dir: str):
    """import mixamo animation (*.dae), 
    rename ,
    add root motion, 
    etc. 
    """
    file = os.path.basename(dir)
    print(f"input file:{dir}")
    name, ext = os.path.splitext(file)
    bpy.ops.wm.collada_import(
        filepath=dir,
        # auto_connect=True
        # ignore_leaf_bones=context.scene.mixamo.ignore_leaf_bones, #TODO set when suport
    )
    arm_obj = [
        obj for obj in context.selected_objects if obj.type == 'ARMATURE'][0]
    context.view_layer.objects.active = arm_obj
    anim_data: bpy.types.AnimData = arm_obj.animation_data
    armature: bpy.types.Armature = arm_obj.data
    action = anim_data.action
    fcurves = action.fcurves
    # rename Action
    action.name = name
    # rename bones
    for k, v in bone_rename_maps.items():
        k = k.replace('mixamorig:', 'mixamorig_')
        if k in armature.bones:
            armature.bones[k.replace('mixamorig:', 'mixamorig_')].name = v
    # fix scale
    scale = arm_obj.scale
    scale_animation(fcurves, scale)
    # fix rotation
    bpy.ops.object.transform_apply(
        location=True, rotation=True, scale=True)
    # add root motion from hips
    if context.scene.mixamo.add_root_motion:
        mixamo_add_root_motion(context.scene.mixamo, armature, fcurves)


def mixamo_add_root_motion(mixamo, armature, fcurves):
    """add root motion"""
    # add root bone
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    root = armature.edit_bones.new('root')
    root.head = (0, 0, 0)
    root.tail = (0, 0, 0.25)
    armature.edit_bones['hips'].parent = root
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    # hips location to rootbone
    if mixamo.root_motion_copy_lx:
        fcurves.find(data_path='pose.bones["hips"].location',
                     index=0).data_path = 'pose.bones["root"].location'
    if mixamo.root_motion_copy_ly:
        fcurves.find(data_path='pose.bones["hips"].location',
                     index=1).data_path = 'pose.bones["root"].location'
    if mixamo.root_motion_copy_lz:
        fcurves.find(data_path='pose.bones["hips"].location',
                     index=2).data_path = 'pose.bones["root"].location'

    if mixamo.root_motion_copy_r:
        fcurves.find(data_path='pose.bones["hips"].rotation_quaternion',
                     index=0).data_path = 'pose.bones["root"].rotation_quaternion'
        fcurves.find(data_path='pose.bones["hips"].rotation_quaternion',
                     index=1).data_path = 'pose.bones["root"].rotation_quaternion'
        fcurves.find(data_path='pose.bones["hips"].rotation_quaternion',
                     index=2).data_path = 'pose.bones["root"].rotation_quaternion'
        fcurves.find(data_path='pose.bones["hips"].rotation_quaternion',
                     index=3).data_path = 'pose.bones["root"].rotation_quaternion'


def mixamo_fix_import_fbx(context, dir: str):
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
        # automatic_bone_orientation=True # (cause bone roll,and mirror ops err)
    )
    arm_obj = [
        obj for obj in context.selected_objects if obj.type == 'ARMATURE'][0]
    context.view_layer.objects.active = arm_obj
    anim_data: bpy.types.AnimData = arm_obj.animation_data
    armature: bpy.types.Armature = arm_obj.data
    action = anim_data.action
    fcurves = action.fcurves
    # rename Action
    action.name = name
    # rename bones
    for k, v in bone_rename_maps.items():
        if k in armature.bones:
            armature.bones[k].name = v

    # fix scale
    scale = arm_obj.scale
    scale_animation(fcurves, scale)

    # fix rotation
    bpy.ops.object.transform_apply(
        location=True, rotation=True, scale=True)

    # add root motion from hips
    if context.scene.mixamo.add_root_motion:
        mixamo_add_root_motion(context.scene.mixamo, armature, fcurves)


class MIXAMO_OT_Update(Operator):
    '''Update all mixamo file in dir'''
    bl_idname = "mixamo.update"
    bl_label = "Update Mixamo"
    bl_description = "Update all mixamo from the input dir if action not exist."

    @classmethod
    def poll(cls, context: bpy.context):
        return True

    def execute(self, context: bpy.context):
        mixamo_character = context.scene.mixamo_character
        if context.scene.mixamo_character == None:
            self.report({'WARNING'},
                        'Not Found mixamo character in current scene.')
            return {'CANCELLED'}

        input_folder = context.scene.mixamo.input_folder
        input_folder = bpy.path.abspath(input_folder)
        files = os.listdir(input_folder)
        for file in files:
            name, ext = os.path.splitext(file)
            dir = os.path.join(input_folder, file)
            if name in bpy.data.actions:  # if exist, pass
                continue
            if ext == '.fbx':
                mixamo_fix_import_fbx(context, dir)
                # add animation  to NAL
                action_2_NAL(mixamo_character, bpy.data.actions[name])
                # remove
                bpy.ops.object.delete()
            elif ext == '.dae':
                mixamo_fix_import_dae(context, dir)
                action_2_NAL(mixamo_character, bpy.data.actions[name])
                bpy.ops.object.delete()
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
        box = layout.box()
        row = box.row()
        row.prop(scene, "mixamo_character")

        box = layout.box()
        row = box.row()
        row.label(text="Import Option")
        row = box.row()
        row.prop(scene.mixamo, 'ignore_leaf_bones')

        row = box.row()
        row.prop(scene.mixamo, 'add_root_motion')
        if scene.mixamo.add_root_motion:
            box = box.box()
            row = box.row(align=True)
            row.label(text='convert root motion from hips')
            row = box.row(align=True)
            row.label(text='location')
            row.prop(scene.mixamo, 'root_motion_copy_lx',
                     text='x', toggle=True)
            row.prop(scene.mixamo, 'root_motion_copy_lz',
                     text='y', toggle=True)
            row.prop(scene.mixamo, 'root_motion_copy_ly',
                     text='z', toggle=True)
            row = box.row(align=True)
            row.prop(scene.mixamo, 'root_motion_copy_r',
                     text='Rotation Quaternion', toggle=True)
        box = layout.box()
        row = box.row()
        row.operator("mixamo.import_character")
        box = layout.box()
        row = box.row()
        row.prop(scene.mixamo, "input_folder")
        row = box.row()
        row.operator("mixamo.update")

class MixamoPropertyGroup(bpy.types.PropertyGroup):
    # TODO use it when bug fixed
    # armture = PointerProperty(
    #     type=bpy.types.Object,
    #     name='Mixamo Armature',
    #     description='Merge animation to this object')
    input_folder: StringProperty(
        name="Mixamo Animations Folder",
        description="Path to mixamo animations folder.",
        maxlen=256,
        default="",
        subtype='DIR_PATH')
    ignore_leaf_bones: BoolProperty(
        name='Ignore Leaf Bones',
        description='Ignore leaf bones when import mixamo.',
        default=False)
    add_root_motion: BoolProperty(
        name='Add Root Motion',
        description='Add root bone and copy motion from hips.',
        default=False)
    root_motion_copy_lx: BoolProperty(
        name='Root Motion Copy Location x',
        description='Root bone copy location x from hips.',
        default=True)
    root_motion_copy_ly: BoolProperty(
        name='Root Motion Copy Location y',
        description='Root bone copy location y from hips.',
        default=True)
    root_motion_copy_lz: BoolProperty(
        name='Root Motion Copy Location z',
        description='Root bone copy location z from hips.',
        default=True)
    root_motion_copy_r: BoolProperty(
        name='Root Motion Copy Rotaion Quaternion',
        description='Root bone copy rotaion from hips.',
        default=True)


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
    bpy.types.Scene.mixamo_character = PointerProperty(
        type=bpy.types.Object,
        name='Mixamo Armature',
        description='Merge animation to this object')


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.mixamo
    del bpy.types.Scene.mixamo_character


if __name__ == "__main__":
    register()
