import bpy
from bpy.props import PointerProperty
from bpy.types import Context, UILayout, AnyType, PointerProperty
import requests
import datetime
import json
import time

bl_info = {
    "name": "Export test",
    "description": "Export of 3D models to API",
    "author": "Illia Brylov",
    "version": (0, 1, 0),
    "blender": (2, 90, 1),
    "category": "Import-Export"
}


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


class Payload(bpy.types.PropertyGroup):
    file_name: bpy.props.StringProperty()
    body: bpy.props.StringProperty()
    pass


class Request(bpy.types.PropertyGroup):
    method: bpy.props.StringProperty()
    endpoint: bpy.props.StringProperty()
    headers: bpy.props.StringProperty()
    payload: bpy.props.PointerProperty(type=Payload)


class Response(bpy.types.PropertyGroup):
    successful: bpy.props.BoolProperty()
    status: bpy.props.StringProperty()
    headers: bpy.props.StringProperty()
    payload: bpy.props.PointerProperty(type=Payload)


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
        print("Executing request: " + bpy.context.scene.Request.method + " request")
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(context.scene.Request.headers)
        scene_response = context.scene.Response
        try:
            response = requests.get(endpoint, headers=headers, timeout=30)
        except requests.exceptions.ConnectionError:
            print("Errorrrrrr")
            scene_response.successful = False
            return {'FINISHED'}
        except requests.exceptions.ReadTimeout:
            print("timeout")
            scene_response.successful = False
            return {'FINISHED'}

        scene_response.successful = True
        scene_response.status = "[" + str(response.status_code) + "]"
        scene_response.headers = str(response.headers)
        scene_response.payload.body = str(response.content)
        return {'FINISHED'}


class DoPostRequest(bpy.types.Operator):
    bl_idname = "object.do_post_request"
    bl_label = "API post request operator"

    def execute(self, context):
        print("Executing request: " + bpy.context.scene.Request.method + " request")
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(context.scene.Request.headers)
        scene_response = context.scene.Response
        try:
            response = requests.post(endpoint, headers=headers, data={}, timeout=30)
        except requests.exceptions.ConnectionError:
            print("Errorrrrrr")
            scene_response.successful = False
            return {'FINISHED'}
        except requests.exceptions.ReadTimeout:
            print("timeout")
            scene_response.successful = False
            return {'FINISHED'}

        scene_response.successful = True
        scene_response.status = "[" + str(response.status_code) + "]"
        scene_response.headers = str(response.headers)
        scene_response.payload.body = str(response.content)
        return {'FINISHED'}


class DoPutRequest(bpy.types.Operator):
    bl_idname = "object.do_put_request"
    bl_label = "API put request operator"

    def execute(self, context):
        print("Executing request: " + bpy.context.scene.Request.method + " request")
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(context.scene.Request.headers)
        scene_response = context.scene.Response
        try:
            response = requests.put(endpoint, headers=headers, data={}, timeout=30)
        except requests.exceptions.ConnectionError:
            print("Errorrrrrr")
            scene_response.successful = False
            return {'FINISHED'}
        except requests.exceptions.ReadTimeout:
            print("timeout")
            scene_response.successful = False
            return {'FINISHED'}

        scene_response.successful = True
        scene_response.status = "[" + str(response.status_code) + "]"
        scene_response.headers = str(response.headers)
        scene_response.payload.body = str(response.content)
        return {'FINISHED'}


class DoDeleteRequest(bpy.types.Operator):
    bl_idname = "object.do_delete_request"
    bl_label = "API delete request operator"

    def execute(self, context):
        print("Executing request: " + bpy.context.scene.Request.method + " request")
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(context.scene.Request.headers)
        scene_response = context.scene.Response
        try:
            response = requests.delete(endpoint, headers=headers, timeout=30)
        except requests.exceptions.ConnectionError:
            print("Errorrrrrr")
            scene_response.successful = False
            return {'FINISHED'}
        except requests.exceptions.ReadTimeout:
            print("timeout")
            scene_response.successful = False
            return {'FINISHED'}

        scene_response.successful = True
        scene_response.status = "[" + str(response.status_code) + "]"
        scene_response.headers = str(response.headers)
        scene_response.payload.body = str(response.content)
        return {'FINISHED'}


class DoRequest(bpy.types.Operator):
    bl_idname = "object.do_request"
    bl_label = "API request operator"

    @classmethod
    def poll(cls, context):
        method = bpy.context.scene.Request.method
        return context.scene.APIData is not None and context.scene.APIData.host is not "" and method in (
            "GET", "POST", "PUT", "DELETE")

    def execute(self, context):
        method = bpy.context.scene.Request.method
        print("Executing... " + method + " request")
        method_call = "bpy.ops.object.do_" + method.lower() + "_request()"
        eval(method_call)
        response = bpy.context.scene.Response
        print("Done")
        print(response.status, response.headers, response.payload.body)
        return {'FINISHED'}


classes = (
    User,
    APIData,
    Payload,
    Request,
    Response,
    DoRequest,
    DoGetRequest,
    DoPostRequest,
    DoPutRequest,
    DoDeleteRequest
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.APIData = bpy.props.PointerProperty(type=APIData)
    bpy.types.Scene.Request = bpy.props.PointerProperty(type=Request)
    bpy.types.Scene.Response = bpy.props.PointerProperty(type=Response)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

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


    try:
        bpy.ops.object.do_request()
    except RuntimeError:
        print("Error")
