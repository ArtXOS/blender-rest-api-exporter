import bpy
from bpy.props import PointerProperty
from bpy.types import Context, UILayout, AnyType, PointerProperty
import requests
import datetime
import json
import time
import os

bl_info = {
    "name": "Export test",
    "description": "Export of 3D models to API",
    "author": "Illia Brylov",
    "version": (0, 1, 0),
    "blender": (2, 90, 1),
    "category": "Import-Export"
}

TIMEOUT = 100


class Log(bpy.types.PropertyGroup):
    log: bpy.props.StringProperty(name="")


class LogGroup(bpy.types.PropertyGroup):
    coll: bpy.props.CollectionProperty(type=Log)
    index: bpy.props.IntProperty()


class LogList(bpy.types.UIList):
    bl_idname = "LOGLIST_UL_log_list"

    def draw_item(self,
                  context,
                  layout,
                  data,
                  item,
                  icon,
                  active_data,
                  active_property,
                  index=0,
                  flt_flag=0):
        layout.prop(item, "log", emboss=False)


class AddLog(bpy.types.Operator):
    bl_idname = "log.add"
    bl_label = "Add log to log section"

    log: bpy.props.StringProperty(default="OBJECT")

    def execute(self, context):
        item = context.scene.LogGroup.coll.add()
        item.log = self.log
        context.scene.LogGroup.coll.move(len(context.scene.LogGroup.coll.items()) - 1, 0)
        return {'FINISHED'}


class ClearLogList(bpy.types.Operator):
    bl_idname = "log.clear"
    bl_label = "Clear log section"

    def execute(self, context):
        context.scene.LogGroup.coll.clear()
        return {'FINISHED'}


class Payload(bpy.types.PropertyGroup):
    body: bpy.props.StringProperty()


class Request(bpy.types.PropertyGroup):
    method: bpy.props.StringProperty()
    endpoint: bpy.props.StringProperty(
        name="Endpoint",
        description="API endpoint",
        default=""
    )
    headers: bpy.props.StringProperty()
    payload: bpy.props.PointerProperty(type=Payload)


class Response(bpy.types.PropertyGroup):
    successful: bpy.props.BoolProperty()
    status: bpy.props.StringProperty()
    headers: bpy.props.StringProperty()
    payload: bpy.props.PointerProperty(type=Payload)


class User(bpy.types.PropertyGroup):
    username: bpy.props.StringProperty(
        name="Username",
        description="User username",
        default=""
    )
    user_email: bpy.props.StringProperty(
        name="User email",
        description="User email",
        default=""
    )
    authorization: bpy.props.StringProperty(
        name="Authorization",
        description="User authorization",
        default=""
    )


class APIData(bpy.types.PropertyGroup):
    host: bpy.props.StringProperty(
        name="Host",
        description="Host address",
        default=""
    )
    user: bpy.props.PointerProperty(type=User)


class DoGetRequest(bpy.types.Operator):
    bl_idname = "object.do_get_request"
    bl_label = "API get request operator"

    def execute(self, context):
        print("Executing " + bpy.context.scene.Request.method + " request")
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(context.scene.Request.headers)
        scene_response = context.scene.Response

        scene_response.successful = False

        try:
            response = requests.get(endpoint, headers=headers, timeout=TIMEOUT)
            scene_response.successful = True
        except requests.exceptions.HTTPError as httperr:
            print("Http Error:", httperr)
            bpy.ops.log.add(log="Http Error:" + str(httperr))
        except requests.exceptions.ConnectionError as conerr:
            print("Connection Error:", conerr)
            bpy.ops.log.add(log="Connection Error" + str(conerr))
        except requests.exceptions.Timeout as tmterr:
            print("Timeout Error:", tmterr)
            bpy.ops.log.add(log="Timeout Error:" + str(tmterr))
        except requests.exceptions.RequestException as error:
            print("Oops... Unknown Error", error)
            bpy.ops.log.add(log="Oops... Unknown Error" + str(error))

        if not scene_response.successful:
            return {'FINISHED'}

        scene_response.status = "[" + str(response.status_code) + "]"

        return {'FINISHED'}


class DoPostRequest(bpy.types.Operator):
    bl_idname = "object.do_post_request"
    bl_label = "API post request operator"

    def execute(self, context):
        print("Executing " + bpy.context.scene.Request.method + " request")
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(context.scene.Request.headers)
        scene_response = context.scene.Response

        scene_response.successful = False

        try:
            response = requests.post(endpoint, headers=headers, timeout=TIMEOUT)
            scene_response.successful = True
        except requests.exceptions.HTTPError as httperr:
            print("Http Error:", httperr)
            bpy.ops.log.add(log="Http Error:" + str(httperr))
        except requests.exceptions.ConnectionError as conerr:
            print("Connection Error:", conerr)
            bpy.ops.log.add(log="Connection Error" + str(conerr))
        except requests.exceptions.Timeout as tmterr:
            print("Timeout Error:", tmterr)
            bpy.ops.log.add(log="Timeout Error:" + str(tmterr))
        except requests.exceptions.RequestException as error:
            print("Oops... Unknown Error", error)
            bpy.ops.log.add(log="Oops... Unknown Error" + str(error))

        if not scene_response.successful:
            return {'FINISHED'}

        scene_response.status = "[" + str(response.status_code) + "]"

        return {'FINISHED'}


class DoPutRequest(bpy.types.Operator):
    bl_idname = "object.do_put_request"
    bl_label = "API put request operator"

    def execute(self, context):
        print("Executing " + bpy.context.scene.Request.method + " request")
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(context.scene.Request.headers)
        scene_response = context.scene.Response

        scene_response.successful = False

        try:
            response = requests.put(endpoint, headers=headers, timeout=TIMEOUT)
            scene_response.successful = True
        except requests.exceptions.HTTPError as httperr:
            print("Http Error:", httperr)
            bpy.ops.log.add(log="Http Error:" + str(httperr))
        except requests.exceptions.ConnectionError as conerr:
            print("Connection Error:", conerr)
            bpy.ops.log.add(log="Connection Error" + str(conerr))
        except requests.exceptions.Timeout as tmterr:
            print("Timeout Error:", tmterr)
            bpy.ops.log.add(log="Timeout Error:" + str(tmterr))
        except requests.exceptions.RequestException as error:
            print("Oops... Unknown Error", error)
            bpy.ops.log.add(log="Oops... Unknown Error" + str(error))

        if not scene_response.successful:
            return {'FINISHED'}

        scene_response.status = "[" + str(response.status_code) + "]"

        return {'FINISHED'}


class DoDeleteRequest(bpy.types.Operator):
    bl_idname = "object.do_delete_request"
    bl_label = "API delete request operator"

    def execute(self, context):
        print("Executing " + bpy.context.scene.Request.method + " request")
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(context.scene.Request.headers)
        scene_response = context.scene.Response

        scene_response.successful = False

        try:
            response = requests.delete(endpoint, headers=headers, timeout=TIMEOUT)
            scene_response.successful = True
        except requests.exceptions.HTTPError as httperr:
            print("Http Error:", httperr)
            bpy.ops.log.add(log="Http Error:" + str(httperr))
        except requests.exceptions.ConnectionError as conerr:
            print("Connection Error:", conerr)
            bpy.ops.log.add(log="Connection Error" + str(conerr))
        except requests.exceptions.Timeout as tmterr:
            print("Timeout Error:", tmterr)
            bpy.ops.log.add(log="Timeout Error:" + str(tmterr))
        except requests.exceptions.RequestException as error:
            print("Oops... Unknown Error", error)
            bpy.ops.log.add(log="Oops... Unknown Error" + str(error))

        if not scene_response.successful:
            return {'FINISHED'}

        scene_response.status = "[" + str(response.status_code) + "]"

        return {'FINISHED'}


class CheckConnection(bpy.types.Operator):
    bl_idname = "system.check_connection"
    bl_label = "Check connection"

    def execute(self, context):
        request = context.scene.Request
        request.method = "GET"
        request.headers = "{}"

        bpy.ops.object.do_request()

        return {'FINISHED'}


class DoRequest(bpy.types.Operator):
    bl_idname = "object.do_request"
    bl_label = "API request operator"

    @classmethod
    def poll(cls, context):
        method = bpy.context.scene.Request.method
        return context.scene.APIData is not None and context.scene.APIData.host is not "" and method in {
            'GET', 'POST', 'PUT', 'DELETE'}

    def execute(self, context):
        method = bpy.context.scene.Request.method
        method_call = "bpy.ops.object.do_" + method.lower() + "_request()"
        eval(method_call)
        response = bpy.context.scene.Response

        if not response.successful:
            return {'FINISHED'}

        bpy.ops.log.add(log=response.status)
        return {'FINISHED'}


class Export(bpy.types.Operator):
    bl_idname = "object.export"
    bl_label = "Export"

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "file_format")

    def execute(self, context):
        temp_dir = bpy.context.preferences.filepaths.temporary_directory
        file_format = context.scene.file_format
        file_name = "test_file"
        filepath = temp_dir + file_name + "." + file_format.lower()

        if file_format == 'OBJ':
            bpy.ops.export_scene.obj(filepath=filepath)
            # TODO .mtl file export
        elif file_format == 'FBX':
            bpy.ops.export_scene.fbx(filepath=filepath)
        elif file_format == 'BLEND':
            bpy.ops.wm.save_mainfile(filepath=filepath)
        elif file_format == 'GLTF':
            bpy.ops.export_scene.gltf(filepath=filepath)

        bpy.ops.log.add(log="Tmp file saved to: " + filepath)

        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(context.scene.Request.headers)
        scene_response = context.scene.Response

        bpy.ops.log.add(log="Exporting...")
        file_obj = open(filepath, 'rb')
        file = {'model': (file_name, file_obj, 'multipart/form-data')}

        context.scene.Response.successful = False
        try:
            response = requests.post(endpoint, headers=headers, files=file, timeout=TIMEOUT)
            context.scene.Response.successful = True
        except requests.exceptions.HTTPError as httperr:
            print("Http Error:", httperr)
            bpy.ops.log.add(log="Http Error:" + str(httperr))
        except requests.exceptions.ConnectionError as conerr:
            print("Connection Error:", conerr)
            bpy.ops.log.add(log="Connection Error" + str(conerr))
        except requests.exceptions.Timeout as tmterr:
            print("Timeout Error:", tmterr)
            bpy.ops.log.add(log="Timeout Error:" + str(tmterr))
        except requests.exceptions.RequestException as error:
            print("Oops... Unknown Error", error)
            bpy.ops.log.add(log="Oops... Unknown Error" + str(error))

        if not context.scene.Response.successful:
            return {'FINISHED'}

        bpy.ops.log.add(log="[" + str(response.status_code) + "]")
        bpy.ops.log.add(log=str(response.content))
        bpy.ops.log.add(log="Removed tmp files")
        file_obj.close()
        os.remove(filepath)

        return {'FINISHED'}


class ExportAs(bpy.types.Operator):
    bl_idname = "object.export_as"
    bl_label = "Export As"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}


class ExporterPanel(bpy.types.Panel):
    bl_idname = "PANEL1_PT_exporter_panel"
    bl_label = "Export to API"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        APIData = context.scene.APIData
        Request = context.scene.Request
        LogGroup = context.scene.LogGroup

        main_layout = self.layout
        main_layout.label(text="Credentials:")

        credentials_box = main_layout.box()
        credentials_box_split = credentials_box.split()

        credentials_box_left_column = credentials_box_split.column(align=True)
        credentials_box_right_column = credentials_box_split.column(align=True)

        credentials_box_left_column.label(text="Username:")
        credentials_box_left_column.prop(APIData.user, "username", icon_only=True)

        credentials_box_right_column.label(text="User email:")
        credentials_box_right_column.prop(APIData.user, "user_email", icon_only=True)

        credentials_box.row().prop(APIData.user, "authorization")

        host_box = main_layout.box()
        host_box.row().prop(APIData, "host")
        host_box.row().prop(Request, "endpoint")
        host_box.split(factor=0.5).operator("system.check_connection")

        main_layout.label(text="Import section:")
        import_box = main_layout.box()

        main_layout.label(text="Export section:")
        export_box = main_layout.box()
        export_buttons_row = export_box.row()
        export_buttons_row.operator("object.export")

        log_box = main_layout.box()
        log_box.label(text="Log section:")

        log_box.template_list("LOGLIST_UL_log_list", "", LogGroup, "coll", LogGroup, "index",
                              rows=3, maxrows=5, columns=3, type='DEFAULT')
        log_box.operator("log.clear")


classes = (
    User,
    APIData,
    Payload,
    Log,
    LogGroup,
    LogList,
    AddLog,
    ClearLogList,
    Request,
    Response,
    CheckConnection,
    DoRequest,
    DoGetRequest,
    DoPostRequest,
    DoPutRequest,
    DoDeleteRequest,
    ExportAs,
    Export,
    ExporterPanel
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.APIData = bpy.props.PointerProperty(type=APIData)
    bpy.types.Scene.Request = bpy.props.PointerProperty(type=Request)
    bpy.types.Scene.Response = bpy.props.PointerProperty(type=Response)
    bpy.types.Scene.file_format = bpy.props.EnumProperty(
        name="File format",
        description="Select file format",
        items=[
            ('OBJ', "OBJ", "OBJ file."),
            ('FBX', "FBX", "FBX file"),
            ('BLEND', "BLENDER", 'Blender file'),
            ('GLTF', "GLTF", 'glTF file')
        ]
    )
    bpy.types.Scene.LogGroup = bpy.props.PointerProperty(type=LogGroup)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.LogGroup
    del bpy.types.Scene.Response
    del bpy.types.Scene.Request
    del bpy.types.Scene.APIData


if __name__ == "__main__":
    register()
    unregister()
    register()

    bpy.context.scene.APIData.host = "https://fb.com"
    bpy.context.scene.Request.method = "GET"
    bpy.context.scene.Request.headers = "{}"

