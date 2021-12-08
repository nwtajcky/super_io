import bpy
import os
import sys

from bpy.props import StringProperty, BoolProperty, EnumProperty

from .ops_super_import import import_icon
from ..clipboard.windows import PowerShellClipboard
from ..exporter.default_exporter import default_exporter, exporter_ops_props


class ModeCopyDefault:
    @classmethod
    def poll(_cls, context):
        if sys.platform == "win32":
            return (
                    context.area.type == "VIEW_3D"
                    and context.active_object is not None
                    and context.active_object.mode == 'OBJECT'
                    and len(context.selected_objects) != 0
            )


class SPIO_OT_export_model(ModeCopyDefault, bpy.types.Operator):
    """Export Selected objects to file and copy to clipboard\nAlt to export every object to a single file"""
    bl_idname = 'spio.export_model'
    bl_label = 'Copy Model'

    extension: StringProperty()
    batch_mode: BoolProperty(default=False)

    def get_temp_dir(self):
        ori_dir = bpy.context.preferences.filepaths.temporary_directory
        temp_dir = ori_dir
        if ori_dir == '':
            # win temp file
            temp_dir = os.path.join(os.getenv('APPDATA'), os.path.pardir, 'Local', 'Temp')

        return temp_dir

    def export_batch(self, context, op_callable, op_args):
        paths = []
        temp_dir = self.get_temp_dir()

        src_active = context.active_object
        selected_objects = context.selected_objects.copy()

        for obj in selected_objects:
            filepath = os.path.join(temp_dir, obj.name + f'.{self.extension}')
            paths.append(filepath)

            context.view_layer.objects.active = obj
            obj.select_set(True)

            op_args.update({'filepath': filepath})
            op_callable(**op_args)
            obj.select_set(False)

        context.view_layer.objects.active = src_active

        return paths

    def export_single(self, context, op_callable, op_args):
        paths = []
        temp_dir = self.get_temp_dir()
        filepath = os.path.join(temp_dir, context.active_object.name + f'.{self.extension}')
        paths.append(filepath)

        op_args.update({'filepath': filepath})
        op_callable(**op_args)

        return paths

    def invoke(self, context, event):
        self.batch_mode = True if event.alt else False
        return self.execute(context)

    def execute(self, context):
        if self.extension not in default_exporter: return {"CANCELLED"}

        bl_idname = default_exporter.get(self.extension)
        op_callable = getattr(getattr(bpy.ops, bl_idname.split('.')[0]), bl_idname.split('.')[1])

        op_args = exporter_ops_props.get(self.extension)

        if self.batch_mode:
            paths = self.export_batch(context, op_callable, op_args)
            self.report({'INFO'},
                        f'{len(paths)} {self.extension} files has been copied to Clipboard')

        else:
            paths = self.export_single(context, op_callable, op_args)
            self.report({'INFO'}, f'{context.active_object.name}.{self.extension} has been copied to Clipboard')

        clipboard = PowerShellClipboard()
        clipboard.push_to_clipboard(paths=paths)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(SPIO_OT_export_model)


def unregister():
    bpy.utils.unregister_class(SPIO_OT_export_model)