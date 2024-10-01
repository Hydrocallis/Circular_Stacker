bl_info = {
    "name": "Circular Stacker",
    "blender": (4, 2, 0),  # 対応するBlenderのバージョンを指定
    "category": "Object",
    "description": "Distribute selected objects in a circular (donut) pattern",
    "author": "KSYN",  # あなたの名前
    "version": (1, 0 ,0),
    "support": "COMMUNITY",
}


import bpy
import math

class OBJECT_OT_circular_stacker(bpy.types.Operator):
    bl_idname = "object.circular_stacker"  # bl_idnameを変更
    bl_label = "Distribute Objects in Circular Stack"  # bl_labelを変更
    bl_description = "Distribute selected objects in a circular (donut) pattern"
    bl_options = {'REGISTER', 'UNDO','PRESET'}

    # ソートするかどうかを判断するためのプロパティ
    sort_objects: bpy.props.BoolProperty(
        name="Sort Objects(By Name)",
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

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "radius")
        layout.prop(self, "height_increment")
        layout.prop(self, "rotation_angle_deg")
        layout.prop(self, "skip_list")
        layout.prop(self, "face_center")
        layout.prop(self, "z_rotation_deg")
        layout.prop(self, "sort_objects")
        try:
            skip_list = [int(x) for x in self.skip_list if x in "01"]
            count_ones = skip_list.count(1)
            layout.label(text=f"Valid Skip Count (1's): {count_ones}")
        except ValueError:
            layout.label(text="Invalid skip list.")

    def execute(self, context):
        try:
            skip_list = [int(x) for x in self.skip_list if x in "01"]
        except ValueError:
            self.report({'ERROR'}, "Skip list must contain only 1s and 0s.")
            return {'CANCELLED'}
        
        selected_objects = bpy.context.selected_objects


        # プロパティがTrueのときにソート
        if self.sort_objects:
            selected_objects = sorted(selected_objects, key=lambda obj: obj.name)
        else:
            selected_objects = selected_objects

        num_objects = len(selected_objects)
        if num_objects == 0:
            self.report({'ERROR'}, "No objects selected.")
            return {'CANCELLED'}
        skip_length = len(skip_list)
        if skip_length == 0:
            self.report({'ERROR'}, "Skip list is empty or invalid.")
            return {'CANCELLED'}
        obj_index = 0
        cursor_location = bpy.context.scene.cursor.location
        
        rotation_angle_rad = math.radians(self.rotation_angle_deg)
        z_rotation_rad = math.radians(self.z_rotation_deg)
        
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
                obj.location = (x, y, z)
                
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