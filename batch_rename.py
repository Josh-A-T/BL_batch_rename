bl_info = {
    "name": "Batch Rename",
    "author": "Josh T",
    "version": (0, 0, 2),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Tool Tab",
    "description": "Batch rename selected objects with prefixes, suffixes, and numbering",
    "category": "Object"
}

import bpy
import re
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty
from bpy.types import Panel, Operator, PropertyGroup

NUMBER_PATTERN = re.compile(r'\.\d+$')

class OBJECT_OT_batch_rename(Operator):
    bl_idname = "object.batch_rename"
    bl_label = "Batch Rename Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.batch_renamer_props
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        if props.sort_by_name:
            selected_objects = sorted(selected_objects, key=lambda x: x.name)
        
        add_numbers = props.add_numbers
        use_base_name = props.use_base_name
        remove_numbers = props.remove_numbers
        number_position = props.number_position
        number_separator = props.number_separator
        padding = props.padding
        start_number = props.start_number
        prefix = props.prefix
        suffix = props.suffix
        base_name = props.base_name
        
        for i, obj in enumerate(selected_objects):
            new_name = ""
            
            if prefix:
                new_name += prefix
            
            if use_base_name and base_name:
                new_name += base_name
            elif not use_base_name:
                original_name = obj.name
                if remove_numbers:
                    original_name = NUMBER_PATTERN.sub('', original_name)
                new_name += original_name
            
            if add_numbers:
                number_str = str(i + start_number).zfill(padding)
                if number_position == 'SUFFIX':
                    new_name += number_separator + number_str
                else: 
                    new_name = number_str + number_separator + new_name
            
            if suffix:
                new_name += suffix
            if new_name and new_name != obj.name:
                obj.name = new_name
        
        self.report({'INFO'}, f"Renamed {len(selected_objects)} objects")
        return {'FINISHED'}


class OBJECT_OT_clear_rename_settings(Operator):
    bl_idname = "object.clear_rename_settings"
    bl_label = "Clear Settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.batch_renamer_props
        props.prefix = ""
        props.suffix = ""
        props.base_name = ""
        props.use_base_name = False
        props.add_numbers = True
        props.start_number = 1
        props.padding = 2
        props.number_separator = "_"
        props.number_position = 'SUFFIX'
        props.remove_numbers = False
        props.sort_by_name = True
        return {'FINISHED'}


class BatchRenameProperties(PropertyGroup):
    prefix: StringProperty(
        name="Prefix",
        description="Text to add before object names",
        default="",
    )
    
    suffix: StringProperty(
        name="Suffix",
        description="Text to add after object names",
        default="",
    )
    
    base_name: StringProperty(
        name="Base Name",
        description="Replace original names with this base name",
        default="Object",
    )
    
    use_base_name: BoolProperty(
        name="Use Base Name",
        description="Replace original names with base name instead of keeping them",
        default=False,
    )
    
    add_numbers: BoolProperty(
        name="Add Numbers",
        description="Add sequential numbers to objects",
        default=True,
    )
    
    start_number: IntProperty(
        name="Start Number",
        description="First number in sequence",
        default=1,
        min=0,
    )
    
    padding: IntProperty(
        name="Padding",
        description="Number of digits (001, 002, etc.)",
        default=2,
        min=1,
        max=6,
    )
    
    number_separator: StringProperty(
        name="Separator",
        description="Character between name and number",
        default="_",
        maxlen=3,
    )
    
    number_position: EnumProperty(
        name="Number Position",
        description="Where to place the numbers",
        items=[
            ('SUFFIX', 'After Name', 'Add numbers after the name'),
            ('PREFIX', 'Before Name', 'Add numbers before the name'),
        ],
        default='SUFFIX',
    )
    
    remove_numbers: BoolProperty(
        name="Remove Existing Numbers",
        description="Remove trailing numbers from original names (e.g., Cube.001 → Cube)",
        default=False,
    )
    
    sort_by_name: BoolProperty(
        name="Sort by Name",
        description="Sort objects alphabetically before numbering",
        default=True,
    )


class VIEW3D_PT_batch_renamer(Panel):
    bl_label = "Batch Object Renamer"
    bl_idname = "VIEW3D_PT_batch_renamer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        props = context.scene.batch_renamer_props
        selected_objects = context.selected_objects
        selected_count = len(selected_objects)

        box = layout.box()
        box.label(text=f"Selected Objects: {selected_count}", icon='OBJECT_DATA')
        
        if selected_count == 0:
            box.label(text="Select objects to rename", icon='INFO')
            return

        layout.separator()
        layout.label(text="Name Components:", icon='SORTALPHA')
        
        col = layout.column(align=True)
        col.prop(props, "prefix")
        
        row = col.row(align=True)
        row.prop(props, "use_base_name", text="Use Base Name")
        if props.use_base_name:
            col.prop(props, "base_name")
        else:
            col.prop(props, "remove_numbers")
        
        col.prop(props, "suffix")

        layout.separator()
        layout.label(text="Numbering:", icon='LINENUMBERS_ON')
        
        col = layout.column(align=True)
        col.prop(props, "add_numbers")
        
        if props.add_numbers:
            col.prop(props, "number_position")
            
            row = col.row(align=True)
            row.prop(props, "start_number")
            row.prop(props, "padding")
            
            col.prop(props, "number_separator")
            col.prop(props, "sort_by_name")

    
        if selected_count > 0:
            layout.separator()
            box = layout.box()
            box.label(text="Preview:", icon='HIDE_OFF')
            
            preview_objects = selected_objects[:3]
            for i, obj in enumerate(preview_objects):
                preview_name = self.generate_preview_name(obj, props, i)
                row = box.row()
                row.label(text=f"{obj.name} → {preview_name}", icon='FORWARD')
            
            if selected_count > 3:
                box.label(text=f"... and {selected_count - 3} more")

        layout.separator()
        col = layout.column(align=True)
        col.scale_y = 1.2
        col.operator("object.batch_rename", icon='FILE_REFRESH')
        col.operator("object.clear_rename_settings", icon='X')

    def generate_preview_name(self, obj, props, index):
        new_name = ""
        
        if props.prefix:
            new_name += props.prefix
        
        if props.use_base_name and props.base_name:
            new_name += props.base_name
        elif not props.use_base_name:
            original_name = obj.name
            if props.remove_numbers:
                original_name = NUMBER_PATTERN.sub('', original_name)
            new_name += original_name
        
        if props.add_numbers:
            number_str = str(index + props.start_number).zfill(props.padding)
            if props.number_position == 'SUFFIX':
                new_name += props.number_separator + number_str
            else:
                new_name = number_str + props.number_separator + new_name
        
        if props.suffix:
            new_name += props.suffix
        
        return new_name if new_name else obj.name


# Registration
classes = (
    BatchRenameProperties,
    OBJECT_OT_batch_rename,
    OBJECT_OT_clear_rename_settings,
    VIEW3D_PT_batch_renamer,
)

def register():
    try:
        unregister()
    except:
        pass
    
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except:
            print(f"Failed to register {cls}")
    
    if not hasattr(bpy.types.Scene, 'batch_renamer_props'):
        bpy.types.Scene.batch_renamer_props = bpy.props.PointerProperty(type=BatchRenameProperties)

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            print(f"Failed to unregister {cls}")
    
    if hasattr(bpy.types.Scene, 'batch_renamer_props'):
        try:
            del bpy.types.Scene.batch_renamer_props
        except:
            pass

if __name__ == "__main__":
    register()