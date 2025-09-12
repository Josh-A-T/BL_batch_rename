bl_info = {
    "name": "Batch Rename",
    "author": "Josh T",
    "version": (0,0,1),
    "blender": (4,1,0),
    "location": "View3D > Sidebar > Tool Tab",
    "description": "Batch rename selected objects with prefixes, suffixes and numbering",
    "category": "Object",
}

import re
import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty
from bpy.types import Panel, Operator

class OBJECT_OT_batch_rename(Operator):
    bl_idname = "object.batch_rename"
    bl_label = "Batch Rename Objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.batch_rename_props
        
        selected_objects = [obj for obj in context.selected_objects]
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return{'CANCELLED'}
        
        if props.sort_by_name:
            selected_objects.sort(key=lambda x: x.name)
            
        for i, obj in enumerate(selected_objects):
            new_name =""
            if props.prefix:
                new_name += props.prefix
            elif not props.use_base_name:
                original_name = obj.name
                if props.remove_numbers:
                    original_name = re.sub(r'\.\d+$', '', original_name)
                new_name += original_name
            if props.add_numbers:
                if props.number_position == 'SUFFIX':
                    new_name += props.number_separator + str(i + props.start_number).zfill(props.padding)
                else:
                    new_name = str(i, props.start_number).zfill(props.padding) + props.number_separator + new_name
            if props.suffix:
                new_name += props.suffix
            if new_name and new_name != obj.name:
                obj.name = new_name
        self.report({'INFO'}, f"Renamed {len(selected_objects)} objects")
        return {'FINISHED'}
            
            
class OBJECT_OT_clear_rename_settings(Operator):
    bl_idname = "object.clear_rename_settings"
    bl_label = "Clear Settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.batch_rename_options
        props.prefix = ""
        props.suffix = ""
        props.bane_name = ""
        props.use_base_name = False
        props.add_numbers = True
        props.start_number = 1
        props.padding = 2
        props.number_separator = "_"
        props.number_position = 'SUFFIX'
        props.remove_numbers = False
        props.sort_by_name = True
        return {'FINISHED'}
    
class BatchRenameProperties(bpy.types.PropertyGroup):
    prefix: StringProperty(
        name="Prefix",
        description="Text to add before object name",
        default="",
    )
    
    suffix: StringProperty(
        name="Suffix",
        description="Text to add after object name",
        default="",
    )
    
    base_name: StringProperty(
        name="Base Name",
        description="Replace original names with this",
        default="Object",
    )
    
    use_base_name: BoolProperty(
        name="Use Base Name",
        description="Replace original names with base name instead of keeping them",
        default="Object",
    )
    
    add_numbers: BoolProperty(
        name="Add Numbers",
        description="Add sequential numbers to object names",
        default=True,
    )
    
    start_number: IntProperty(
        name="Start Number",
        description="First number in the sequence",
        default=1,
        min=0,
    )
    
    padding: IntProperty(
        name="Padding", 
        description="Number of digits (001, 002, etc)",
        default=2,
        min=1,
        max=6,
    )
    
    number_separator: StringProperty(
        name="separator",
        description="Character between name and number",
        default="_",
        maxlen=3,
    )
    
    number_position: EnumProperty(
        name="Number Position",
        description="Where to place the numbers",
        items=[
            ('SUFFIX', 'After Name', 'Add numners after the name'),
            ('PREFIX', 'Before Name', 'Add numbers before the name'),
        ],
        default='SUFFIX',
    )
    
    remove_numbers: BoolProperty(
        name="Remove Existing Numbers",
        description="Remove trailing numbers from original names (E.g., Cube.001 → Cube)",
        default=False,
    )
    
    sort_by_name: BoolProperty(
        name="Sort by Name",
        description="Sort objects alphabetically before numbering",
        default=True
    )
    
    
class VIEW3D_PT_batch_rename(Panel):
    bl_label = "Batch Object Rename"
    bl_idname = "VIEW3D_PT_batch_rename"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.batch_rename_props
        selected_count = len(context.selected_objects)
        box = layout.box()
        box.label(text=f"Selected Objects: {selected_count}", icon='OBJECT_DATA')
        
        if selected_count == 0:
            box.label(text="Selected objects to rename", icon='INFO')
            return
        layout.separator()
        layout.label(text="Name Components:", icon='SORTALPHA')
        
        col = layout.column(align=True)
        col.prop(props, "prefix")
        
        row = col.row(align=True)
        row.prop(props, "use_base_name", text="", icon='FILE_TEXT')
        sub = row.row(align=True)
        sub.enabled = props.base_name
        sub.prop(props, "base_name", texts="")
        
        if not props.use_base_name:
            col.prop(props, "remove_numbers")
        
        col.props(props, "suffix")
        
        layout.separator()
        layout.label(text="Numbering:", icon='LINENUMBERS_ON')
        
        col = layout.column(align=True)
        col.props(props, "add_numbers")
        
        if props.add_numbers:
            col.props(props, "number_position")
            
            row = col.row(align=True)
            row.prop(props, "start_number")
            row.prop(props, "padding")
            
            col.prop(props, "number_separator")
            col.prop(props, "sort_by_name")
        layout.separator()
        
        if selected_count > 0:
            box = layout.box()
            box.label(text="Preview:", icons='HIDE_OFF')
            
            preview_objects = context.selected_objects[:3]
            for i, obj in enumerate(preview_objects):
                preview_name = self.generate_preview_name(obj, props, i)
                row = box.row()
                row.label(text=f"{obj.name} → {preview_name}", icon='FORWARD')
            if len(context.selected_objects) > 3:
                box.label(text=f"... and {len(context.selcted_objects) -3 } more")
        layout.separator()
        
        col = layout.column(align=True)
        col.scale_y = 1.2
        col.operator("object.bath_rename", icon='FILE_REFRESH')
        
        row = layout.row()
        row.operator("object.clear_rename_settings", icon='X')
    
    def generate_preview_name(self, obj, props, index):
        new_name = ""
        
        if props.prefix:
            new_name += props.prefix
        if props.use_base_name and props.base_name:
            new_name += props.base_name
        elif not props.use_base_name:
            original_name = obj.name
            if props.remove_numbers:
                original_name = re.sub(r'\.\d+$', '', original_name)
            new_name += original_name
        
        if props.add_numbers:
            number_str = str(index + props.start_number).zFill(props.padding)
            if props.number_position == "SUFFIX":
                new_name += props.number_separator + number_str
            else:
                new_name += number_str + props.number_separator + new_name
        
        if props.suffix:
            new_name += props.suffix
        return new_name if new_name else obj.name    

classes = [
    BatchRenameProperties,
    OBJECT_OT_batch_rename,
    OBJECT_OT_clear_rename_settings,
    VIEW3D_PT_batch_rename,
]

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            print(f"Class {cls} already registered")
    
    
    if not hasattr(bpy.types.Scene, 'batch_rename_props'):
        bpy.types.Scene.batch_rename_props = bpy.props.PointerProperty(type=BatchRenameProperties)
    else:
        print("batch_rename_props already exists in Scene")

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            print(f"Class {cls} was not registered")
    
    if hasattr(bpy.types.Scene, 'batch_rename_props'):
        del bpy.types.Scene.batch_rename_props

if __name__ == "__main__":
    register()
