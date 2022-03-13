# Copyright (c) 2022 ywabygl@gmail.com
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import bpy
import os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, PointerProperty, EnumProperty
from bpy.types import Operator, Panel
from . import rootmotion

bl_info = {
    "name": "Mixamo Import",
    "author": "ywaby",
    "version": (0, 2, 0),
    "blender": (3, 0, 0),
    "location": "3D View > UI (Right Panel) > Mixamo Tab",
    "description": ("Import and update mixamo animations"),
    "warning": "",
    "wiki_url": "https://github.com/ywaby/mixamo2bl",
    "tracker_url": "https://github.com/ywaby/mixamo2bl/issues",
    "category": "Import-Export",
    "support": "COMMUNITY",
}

bone_rename_maps = {
    # 'root': 'root',
    'mixamorig:Hips': 'hips',
    'mixamorig:Spine': 'spine.01',
    'mixamorig:Spine1': 'spine.02',
    'mixamorig:Spine2': 'spine.03',
    'mixamorig:LeftShoulder': 'shoulder.L',
    'mixamorig:LeftArm': 'upperarm.L',
    'mixamorig:LeftForeArm': 'lowerarm.L',
    'mixamorig:LeftHand': 'hand.L',
    'mixamorig:RightShoulder': 'shoulder.R',
    'mixamorig:RightArm': 'upperarm.R',
    'mixamorig:RightForeArm': 'lowerarm.R',
    'mixamorig:RightHand': 'hand.R',
    'mixamorig:Head': 'head',
    'mixamorig:Neck': 'neck',
    'mixamorig:LeftEye': 'eye.L',
    'mixamorig:RightEye': 'eye.R',
    'mixamorig:LeftUpLeg': 'thigh.L',
    'mixamorig:LeftLeg': 'shin.L',
    'mixamorig:LeftFoot': 'foot.L',
    'mixamorig:RightUpLeg': 'thigh.R',
    'mixamorig:RightLeg': 'shin.R',
    'mixamorig:RightFoot': 'foot.R',
    'mixamorig:LeftHandIndex1': 'index.01.L',
    'mixamorig:LeftHandIndex2': 'index.02.L',
    'mixamorig:LeftHandIndex3': 'index.03.L',
    'mixamorig:LeftHandMiddle1': 'middle.01.L',
    'mixamorig:LeftHandMiddle2': 'middle.02.L',
    'mixamorig:LeftHandMiddle3': 'middle.03.L',
    'mixamorig:LeftHandPinky1': 'pinky.01.L',
    'mixamorig:LeftHandPinky2': 'pinky.02.L',
    'mixamorig:LeftHandPinky3': 'pinky.03.L',
    'mixamorig:LeftHandRing1': 'ring.01.L',
    'mixamorig:LeftHandRing2': 'ring.02.L',
    'mixamorig:LeftHandRing3': 'ring.03.L',
    'mixamorig:LeftHandThumb1': 'thumb.01.L',
    'mixamorig:LeftHandThumb2': 'thumb.02.L',
    'mixamorig:LeftHandThumb3': 'thumb.03.L',
    'mixamorig:RightHandIndex1': 'index.01.R',
    'mixamorig:RightHandIndex2': 'index.02.R',
    'mixamorig:RightHandIndex3': 'index.03.R',
    'mixamorig:RightHandMiddle1': 'middle.01.R',
    'mixamorig:RightHandMiddle2': 'middle.02.R',
    'mixamorig:RightHandMiddle3': 'middle.03.R',
    'mixamorig:RightHandPinky1': 'pinky.01.R',
    'mixamorig:RightHandPinky2': 'pinky.02.R',
    'mixamorig:RightHandPinky3': 'pinky.03.R',
    'mixamorig:RightHandRing1': 'ring.01.R',
    'mixamorig:RightHandRing2': 'ring.02.R',
    'mixamorig:RightHandRing3': 'ring.03.R',
    'mixamorig:RightHandThumb1': 'thumb.01.R',
    'mixamorig:RightHandThumb2': 'thumb.02.R',
    'mixamorig:RightHandThumb3': 'thumb.03.R',
    'mixamorig:LeftToeBase': 'toe.L',
    'mixamorig:RightToeBase': 'toe.R'
}


def action_2_NAL(arm_obj, action: bpy.types.Action):
    # add  action to NAL
    arm_obj.animation_data.action = action
    track = arm_obj.animation_data.nla_tracks.new()
    track.name = action.name
    track.mute = True
    track.strips.new(action.name, action.frame_range[0], action)


def scale_animation(action: bpy.types.Action, scale):
    fcurves = action.fcurves
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
        default="*.fbx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    filter_folder: BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})

    filename: StringProperty(
        name="File Name",
    )

    def execute(self, context:  bpy.context):
        scene = context.scene
        name, ext = os.path.splitext(self.filename)
        mixamo_fix_import_fbx(context, self.filepath)
        armature = context.active_object
        if scene.mixamo.add_root_motion:
            bpy.ops.mixamo.add_root_motion()
        if scene.mixamo.stash_action:
            action_2_NAL(armature, armature.animation_data.action)
        scene.mixamo_character = armature
        if scene.mixamo.input_folder == '':
            scene.mixamo.input_folder = os.path.dirname(self.filepath)
        return{'FINISHED'}



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
    # rename Action
    action.name = name
    # rename bones
    for k, v in bone_rename_maps.items():
        if k in armature.bones:
            armature.bones[k].name = v

    # fix scale
    scale = arm_obj.scale
    scale_animation(action, scale)

    # fix rotation
    bpy.ops.object.transform_apply(
        location=True, rotation=True, scale=True)
    # TODO fix bone roll


class MIXAMO_OT_Update(Operator):
    '''Update all mixamo file in dir'''
    bl_idname = "mixamo.update"
    bl_label = "Update Mixamo"
    bl_description = "Update all mixamo from the input dir if action not exist."

    @classmethod
    def poll(cls, context: bpy.context):
        return  context.scene.mixamo.input_folder 
        
    def execute(self, context: bpy.context):
        scene = context.scene
        mixamo_character = scene.mixamo_character
        if scene.mixamo_character == None:
            self.report({'WARNING'},
                        'Not Found mixamo character in current scene.')
            return {'CANCELLED'}

        input_folder = scene.mixamo.input_folder
        input_folder = bpy.path.abspath(input_folder)
        files = os.listdir(input_folder)
        files=[f for f in files if os.path.splitext(f)[1]=='.fbx' ]
        for file in files:
            name, ext = os.path.splitext(file)
            dir = os.path.join(input_folder, file)
            if name in bpy.data.actions:  # if exist, pass
                continue
            
            mixamo_fix_import_fbx(context, dir)
            if scene.mixamo.add_root_motion:
                bpy.ops.mixamo.add_root_motion()
            # add animation  to NAL
            if scene.mixamo.stash_action:
                action_2_NAL(mixamo_character, bpy.data.actions[name])
            # remove
            bpy.ops.object.delete()
        return{'FINISHED'}


class MIXAMO_PT_Main(Panel):
    """Mixamo Import UI"""
    bl_label = "Mixamo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Mixamo"

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        scene = context.scene
        box = layout.box()
        row = box.row()
        row.prop(scene, "mixamo_character")
        # import
        box = layout.box()
        row = box.row()
        row.label(text="Import Option")
        row = box.row()
        row.prop(scene.mixamo, 'ignore_leaf_bones')
        row = box.row()
        row.prop(scene.mixamo, 'stash_action')
        # root motion
        row = box.row()
        row.prop(scene.mixamo, 'add_root_motion')

        # update
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
    stash_action: BoolProperty(
        name='Stash Action',
        description='Stash action to NAL.',
        default=True)
    ignore_leaf_bones: BoolProperty(
        name='Ignore Leaf Bones',
        description='Ignore leaf bones when import mixamo.',
        default=False)
    add_root_motion: BoolProperty(
        name='Add Root Motion',
        description='Add root bone and copy motion from hips.',
        default=False)



classes = (
    MixamoPropertyGroup,
    MIXAMO_OT_ImportCharater,
    MIXAMO_OT_Update,
    MIXAMO_PT_Main,
)


def register():
    print("register mixamo")
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mixamo = PointerProperty(
        type=MixamoPropertyGroup)
    bpy.types.Scene.mixamo_character = PointerProperty(
        type=bpy.types.Object,
        name='Mixamo Armature',
        description='Merge animation to this object')
    rootmotion.register()


def unregister():
    rootmotion.unregister()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.mixamo
    del bpy.types.Scene.mixamo_character


if __name__ == "__main__":
    register()
