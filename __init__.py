bl_info = {
    "name": "Circular Stacker",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),  
    "category": "Object",
    "description": "Distribute selected objects in a circular (donut) pattern",
    "author": "KSYN",  
    "support": "COMMUNITY",
}

import bpy
import math

class OBJECT_OT_circular_stacker(bpy.types.Operator):
    bl_idname = "object.circular_stacker"
    bl_label = "Distribute Objects in Circular Stack"
    bl_description = "Distribute selected objects in a circular (donut) pattern"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    # 列挙型プロパティ: スキップモードの選択
    skip_mode: bpy.props.EnumProperty(
        name="Skip Mode",
        description="Choose how to handle the skip list",
        items=[
            ('BY_LIST', "Use Skip pattern List", "Use the skip list pattern (1's and 0's)"),
            ('BY_COUNT', "By Count", "Distribute evenly based on count")
        ],
        default='BY_COUNT'
    ) # type: ignore

    # インテジャープロパティ: スキップの間隔を指定
    skip_count: bpy.props.IntProperty(
        name="Skip Count",
        description="Number of objects to skip after each placed object",
        default=4,
        min=1
    ) # type: ignore

    # ソートするかどうかを判断するためのプロパティ
    sort_objects: bpy.props.BoolProperty(
        name="Sort Objects (By Name)",
        description="Whether to sort the selected objects",
        default=True
    ) # type: ignore

    # オペレーターのプロパティ
    radius: bpy.props.FloatProperty(
        name="Radius",
        description="The radius of the circle",
        default=5.0,
        min=0.0
    ) # type: ignore

    height_increment: bpy.props.FloatProperty(
        name="Height Increment",
        description="Height increment between stacked circles",
        default=2
    ) # type: ignore

    rotation_angle_deg: bpy.props.FloatProperty(
        name="Rotation Angle",
        description="Angle to rotate the circular arrangement (degrees)",
        default=0.0
    ) # type: ignore

    skip_list: bpy.props.StringProperty(
        name="Skip List",
        description="List of 1s and 0s (e.g., '101011') to skip placements",
        default="1111"
    ) # type: ignore

    face_center: bpy.props.BoolProperty(
        name="Face Center",
        description="Rotate objects to face the center of the circle",
        default=False
    ) # type: ignore

    z_rotation_deg: bpy.props.FloatProperty(
        name="Z-Axis Rotation",
        description="Additional rotation around the Z-axis for each object (degrees)",
        default=0.0
    ) # type: ignore
    
    z_offset_per_object: bpy.props.FloatProperty(
    name="Z Offset Per Object",
    description="Z-axis offset for each object in the arrangement (in meters)",
    default=0.0,
    unit='LENGTH'
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "radius")
        layout.prop(self, "height_increment")
        layout.prop(self, "rotation_angle_deg")
        layout.prop(self, "face_center")
        layout.prop(self, "z_rotation_deg")
        layout.prop(self, "z_offset_per_object")

        layout.prop(self, "sort_objects")
        layout.prop(self, "skip_mode")

        if self.skip_mode == 'BY_LIST':
            layout.prop(self, "skip_list")
            try:
                skip_list = [int(x) for x in self.skip_list if x in "01"]
                count_ones = skip_list.count(1)
                count_zeros = skip_list.count(0)
                total_count = count_ones + count_zeros
                layout.label(text=f"Valid Skip Count (1's): {count_ones}, (0's): {count_zeros}, Total: {total_count}")
            except ValueError:
                layout.label(text="Invalid skip list.")
        else:
            layout.prop(self, "skip_count")

        layout.label(text=f"Selected Objects: {len(bpy.context.selected_objects)}")

    def execute(self, context):
        selected_objects = bpy.context.selected_objects

        if self.sort_objects:
            selected_objects = sorted(selected_objects, key=lambda obj: obj.name)

        num_objects = len(selected_objects)
        if num_objects == 0:
            self.report({'ERROR'}, "No objects selected.")
            return {'CANCELLED'}

        cursor_location = bpy.context.scene.cursor.location
        rotation_angle_rad = math.radians(self.rotation_angle_deg)
        z_rotation_rad = math.radians(self.z_rotation_deg)

        obj_index = 0

        if self.skip_mode == 'BY_LIST':
            try:
                skip_list = [int(x) for x in self.skip_list if x in "01"]
            except ValueError:
                self.report({'ERROR'}, "Skip list must contain only 1s and 0s.")
                return {'CANCELLED'}

            skip_length = len(skip_list)
            if skip_length == 0 or skip_list.count(1)==0:
                self.report({'ERROR'}, "Skip list is empty or invalid.")
                return {'CANCELLED'}

            for circle in range(math.ceil(num_objects / skip_list.count(1))):
                z = cursor_location.z + circle * self.height_increment
                for i in range(skip_length):
                    if skip_list[i] == 0:
                        continue
                    if obj_index >= num_objects:
                        return {'FINISHED'}
                    angle = 2 * math.pi * i / skip_length + rotation_angle_rad
                    x = cursor_location.x + self.radius * math.cos(angle)
                    y = cursor_location.y + self.radius * math.sin(angle)
                    obj = selected_objects[obj_index]
                    obj.location = (x, y, z + obj_index * self.z_offset_per_object)


                    # Z軸回転の適用
                    if self.face_center:
                        direction = -1 if self.face_center else 1
                        rot_z = math.atan2(y - cursor_location.y, x - cursor_location.x) + (math.pi * direction)
                        obj.rotation_euler.z = rot_z + z_rotation_rad
                    else:
                        obj.rotation_euler.z += z_rotation_rad

                    obj_index += 1

        elif self.skip_mode == 'BY_COUNT':
            skip_count = self.skip_count-1
            for circle in range(math.ceil(num_objects / (skip_count + 1))):
                z = cursor_location.z + circle * self.height_increment
                for i in range(skip_count + 1):
                    if obj_index >= num_objects:
                        return {'FINISHED'}
                    angle = 2 * math.pi * i / (skip_count + 1) + rotation_angle_rad
                    x = cursor_location.x + self.radius * math.cos(angle)
                    y = cursor_location.y + self.radius * math.sin(angle)
                    obj = selected_objects[obj_index]
                    obj.location = (x, y, z + obj_index * self.z_offset_per_object)

                    # Z軸回転の適用
                    if self.face_center:
                        direction = -1 if self.face_center else 1
                        rot_z = math.atan2(y - cursor_location.y, x - cursor_location.x) + (math.pi * direction)
                        obj.rotation_euler.z = rot_z + z_rotation_rad
                    else:
                        obj.rotation_euler.z += z_rotation_rad

                    obj_index += 1

        return {'FINISHED'}


# クラスを登録/登録解除
classes = [OBJECT_OT_circular_stacker]

def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(OBJECT_OT_circular_stacker.bl_idname)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # トランスフォームパネルのメニューにオペレーターを追加
    bpy.types.VIEW3D_MT_transform_object.append(menu_func)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_transform_object.remove(menu_func)


if __name__ == "__main__":
    register()
