bl_info = {
    "name": "Batch Rename",
    "author": "Josh T",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Tool Tab",
    "description": "Batch rename selected objects with prefixes, suffixes, numbering, and collection assignment",
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
        
        target_collection = None
        if props.add_to_collection:
            if props.collection_option == 'NEW':
                collection_name = props.new_collection_name if props.new_collection_name else "Renamed_Objects"
                target_collection = bpy.data.collections.new(collection_name)
                context.scene.collection.children.link(target_collection)
            else:  
                if props.existing_collection:
                    target_collection = bpy.data.collections.get(props.existing_collection)
                    if not target_collection:
                        self.report({'WARNING'}, f"Collection '{props.existing_collection}' not found")
                        return {'CANCELLED'}
        
        renamed_objects = []
        
        for i, obj in enumerate(selected_objects):
            new_name = ""
            original_name = obj.name
            
            if prefix:
                new_name += prefix
            
            if use_base_name and base_name:
                new_name += base_name
            elif not use_base_name:
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
                
            if props.search_pattern:
                try:
                    new_name = re.sub(props.search_pattern, props.replace_pattern, new_name)
                except re.error:
                    self.report({'WARNING'}, "Invalid search pattern")
                    return {'CANCELLED'}
            
            if new_name and new_name != obj.name:
                obj.name = new_name
                renamed_objects.append(obj)
        
        if target_collection and renamed_objects:
            for obj in renamed_objects:
                if obj.name not in target_collection.objects:
                    for coll in obj.users_collection:
                        if coll != context.scene.collection:
                            coll.objects.unlink(obj)
                    target_collection.objects.link(obj)
        
        self.report({'INFO'}, f"Renamed {len(selected_objects)} objects")
        if target_collection:
            self.report({'INFO'}, f"Added to collection: {target_collection.name}")
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
        props.search_pattern = ""
        props.replace_pattern = ""
        props.add_to_collection = False
        props.collection_option = 'NEW'
        props.new_collection_name = "Renamed_Objects"
        props.existing_collection = ""
        return {'FINISHED'}

#####-----Properties-----#####
# Prefix
# Suffix
# searh_pattern
# replace_pattern
# base_name
# use_base_name
# add_numbers
# start_number
# padding
# number_separator
# number_position
# remove_numbers
# sort_by_name
# add_to_collection
# collection_options
# new_collection name
# existing collection

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
    
    search_pattern: StringProperty(
        name="Search",
        description="Text pattern to search for in object names",
        default="",
    )
    
    replace_pattern: StringProperty(
        name="Replace",
        description="Text to replace found patterns with",
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
    
    add_to_collection: BoolProperty(
        name="Add to Collection",
        description="Add renamed objects to a collection",
        default=False,
    )
    
    collection_option: EnumProperty(
        name="Collection Option",
        description="Choose whether to create a new collection or use an existing one",
        items=[
            ('NEW', 'New Collection', 'Create a new collection for the renamed objects'),
            ('EXISTING', 'Existing Collection', 'Add to an existing collection'),
        ],
        default='NEW',
    )
    
    new_collection_name: StringProperty(
        name="New Collection Name",
        description="Name for the new collection",
        default="Renamed_Objects",
    )
    
    existing_collection: StringProperty(
        name="Existing Collection",
        description="Name of existing collection to add objects to",
        default="",
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

        # Search and replace
        layout.separator()
        layout.label(text="Search & Replace:", icon='VIEWZOOM')
        col = layout.column(align=True)
        col.prop(props, "search_pattern")
        col.prop(props, "replace_pattern")

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

        # Collection options
        layout.separator()
        layout.label(text="Collection Options:", icon='OUTLINER_COLLECTION')
        col = layout.column(align=True)
        col.prop(props, "add_to_collection")
        
        if props.add_to_collection:
            col.prop(props, "collection_option", expand=True)
            
            if props.collection_option == 'NEW':
                col.prop(props, "new_collection_name")
            else: 
                row = col.row(align=True)
                row.prop_search(props, "existing_collection", bpy.data, "collections", text="Collection")
                row.operator("object.refresh_collections", text="", icon='FILE_REFRESH')
    
        # Preview
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
        
        if props.search_pattern:
            try:
                new_name = re.sub(props.search_pattern, props.replace_pattern, new_name)
            except re.error:
                pass  
        
        return new_name if new_name else obj.name


class OBJECT_OT_refresh_collections(Operator):
    bl_idname = "object.refresh_collections"
    bl_label = "Refresh Collections"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        self.report({'INFO'}, "Collection list refreshed")
        return {'FINISHED'}


classes = (
    BatchRenameProperties,
    OBJECT_OT_batch_rename,
    OBJECT_OT_clear_rename_settings,
    OBJECT_OT_refresh_collections,
    VIEW3D_PT_batch_renamer,
)

def register():
    try:
        unregister()
    except:
        pass
    
    if hasattr(bpy.types.Scene, 'batch_renamer_props'):
        try:
            del bpy.types.Scene.batch_renamer_props
        except:
            pass
    
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Failed to register {cls}: {e}")
    bpy.types.Scene.batch_renamer_props = bpy.props.PointerProperty(type=BatchRenameProperties)

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
    
    if hasattr(bpy.types.Scene, 'batch_renamer_props'):
        try:
            del bpy.types.Scene.batch_renamer_props
        except:
            pass

if __name__ == "__main__":
    register()