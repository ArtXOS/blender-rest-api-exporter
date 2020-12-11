import bpy
from bpy.props import PointerProperty
from bpy.types import Context, UILayout, AnyType, PointerProperty
import requests
import datetime
import json
import time
import os

"""
Export to RESTfull API add-on for Blender. You can use this add-on to make faster the process of sending 
3D models to your server, after they’ve been created or modified. You have a possibility to export the 
whole scene collection in different file formats. Currently they are .blend, .fbx, .obj, .gltf. 
Add-on creates tmp 3D model file in the format you’ve choosed, then sends it to the server. 
After receiving a response, add log with a response status and shows the response content if possible. 
Also this add-on can be used with authorized requests. By default it uses Bearer token 
(you have to fill Authorization field without Bearer prefix) to send your request with authorization header added.
This add-on has to be a part of VMCK project.
"""

# required version of Blender is 2.90.1
bl_info = {
    "name": "Export to API",
    "description": "Export of 3D models to API",
    "author": "Illia Brylov",
    "version": (0, 0, 5),
    "blender": (2, 90, 1),
    "category": "Import-Export"
}

# HTTP requests timeout
TIMEOUT = 100

# messages definitions
HTTP_ERROR_MESSAGE = "Http Error: "
CONNECTION_ERROR_MESSAGE = "Connection Error: "
TIMEOUT_ERROR_MESSAGE = "Timeout Error: "
UNKNOWN_ERROR_MESSAGE = "Oops... Unknown Error: "
INVALID_HOST_MESSAGE = "Error: host has to start with https:// or http://"
FILENAME_EMPTY_MESSAGE = "Error: file name is empty"

# panel UI
CREDENTIALS_SECTION_NAME = "Credentials:"
USERNAME_FIELD = "Username:"
USER_EMAIL_FIELD = "User email:"
IMPORT_SECTION_NAME = "Import:"
EXPORT_SECTION_NAME = "Export:"
LOG_SECTION_NAME = "Log:"

# ----------------- Start: Log section ----------------- #

"""
Classes to create and manage Log section
"""


class Log(bpy.types.PropertyGroup):
    """
        Log class of Log section, using Blender Property Group

        log : string
            One log in log section
    """

    log: bpy.props.StringProperty(name="")


class LogGroup(bpy.types.PropertyGroup):
    """
        LogGroup class helps to manage Log section, using Blender Property Group
    """

    coll: bpy.props.CollectionProperty(type=Log)
    index: bpy.props.IntProperty()


class LogList(bpy.types.UIList):
    """
        LogList class defines the look of Log section, using Blender UI List
    """

    bl_idname = "LOGLIST_UL_log_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index=0, flt_flag=0):
        layout.prop(item, "log", emboss=False)


class AddLog(bpy.types.Operator):
    """
        AddLog class adds log to Log section, using Blender Operator
    """

    bl_idname = "log.add"
    bl_label = "Add log to log section"

    log: bpy.props.StringProperty(default="OBJECT")

    def execute(self, context):
        item = context.scene.LogGroup.coll.add()
        item.log = self.log
        context.scene.LogGroup.coll.move(len(context.scene.LogGroup.coll.items()) + 1, 0)
        return {'FINISHED'}


class ClearLogList(bpy.types.Operator):
    """
        ClearLogList class clears Log sections, using Blender Operator
    """

    bl_idname = "log.clear"
    bl_label = "Clear log section"

    def execute(self, context):
        context.scene.LogGroup.coll.clear()
        return {'FINISHED'}


# ----------------- End: Log section ----------------- #


# ----------------- Start: Helpers ----------------- #

"""
Classes to store data about the User and API. 
May be used for adding additional features to the add-on
"""


class Payload(bpy.types.PropertyGroup):
    """
        Payload class to store Request or Response body, using Blender Property Group
        Can be used if you want to send some data as data= argument in POST and PUT requests, that can be transformed from
        string back to dictionary using json.loads()

        body : string
            Request body as string
    """

    body: bpy.props.StringProperty()


class Request(bpy.types.PropertyGroup):
    """
        Request class to store information about HTTP request, using Blender Property Group

        method : string
            HTTP request method as uppercase string
        endpoint : string
            Request endpoint - part after hostname as "/*"
        headers : string
            Headers of HTTP request as string which can be transformed to dictionary using json.loads()
        payload : Payload
            Object of Payload class
    """

    method: bpy.props.StringProperty()
    endpoint: bpy.props.StringProperty(
        name="Endpoint",
        description="API endpoint",
        default=""
    )
    headers: bpy.props.StringProperty()
    payload: bpy.props.PointerProperty(type=Payload)


class Response(bpy.types.PropertyGroup):
    """
        Response class to store information of HTTP response, using Blender Property Group

        successful : bool
            True - if Request was successful, False - otherwise
        status : string
            HTTP response code as "[code]"
        headers : string
            Headers of HTTP as string which can be transformed back to dictionary using json.loads()
        payload : Payload
            Object of Payload class
    """

    successful: bpy.props.BoolProperty()
    status: bpy.props.StringProperty()
    headers: bpy.props.StringProperty()
    payload: bpy.props.PointerProperty(type=Payload)


class User(bpy.types.PropertyGroup):
    """
        User class to store credentials of API user

        username : string
            User username
        user_email : string
            User email
        authorization : string
            User authorization header as string, which can be transformed to dictionary using json.loads()
    """

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
    """
        APIData class stores information about API and it's user, using Blender Property Group

        host : string
            hostname of the server
        user : User
            User object
    """

    host: bpy.props.StringProperty(
        name="Host",
        description="Host address",
        default=""
    )
    user: bpy.props.PointerProperty(type=User)


# ----------------- End: Helpers ----------------- #


# ----------------- Start: API communication helpers ----------------- #

"""
Classes to store communicate with the server. 
May be used for adding additional features to the add-on
"""


class DoGetRequest(bpy.types.Operator):
    """
        DoGetRequest class wraps HTTP GET request, using Blender Operator
    """

    bl_idname = "system.do_get_request"
    bl_label = "API get request operator"

    def execute(self, context):
        """
            Function to call HTTP GET request. Handles possible errors and informs user about execution process
            and results by printing info messages to Log and Blender console.
        """

        print(f"Executing: {bpy.context.scene.Request.method}request")

        # setting up
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(bpy.context.scene.Request.headers)
        scene_response = context.scene.Response
        scene_response.successful = False

        # executing GET request and handling possible errors
        try:
            response = requests.get(endpoint, headers=headers, timeout=TIMEOUT)
            scene_response.successful = True
        except requests.exceptions.HTTPError as httperr:
            print(HTTP_ERROR_MESSAGE, httperr)
            bpy.ops.log.add(log=HTTP_ERROR_MESSAGE + str(httperr))
        except requests.exceptions.ConnectionError as conerr:
            print(CONNECTION_ERROR_MESSAGE, conerr)
            bpy.ops.log.add(log=CONNECTION_ERROR_MESSAGE + str(conerr))
        except requests.exceptions.Timeout as tmterr:
            print(TIMEOUT_ERROR_MESSAGE, tmterr)
            bpy.ops.log.add(log=TIMEOUT_ERROR_MESSAGE + str(tmterr))
        except requests.exceptions.RequestException as error:
            print(UNKNOWN_ERROR_MESSAGE, error)
            bpy.ops.log.add(log=UNKNOWN_ERROR_MESSAGE + str(error))

        # if not successful - exit
        if not scene_response.successful:
            return {'FINISHED'}

        # filling scene response property with info
        scene_response.status = f"[{str(response.status_code)}]"
        scene_response.headers = json.dumps(dict(response.headers))
        scene_response.payload.body = str(response.content)

        # printing headers and body content to Blender console
        print(scene_response.headers)
        print(scene_response.payload.body)

        return {'FINISHED'}


class DoPostRequest(bpy.types.Operator):
    """
        DoPostRequest class wraps HTTP POST request, using Blender Operator
    """

    bl_idname = "system.do_post_request"
    bl_label = "API post request operator"

    def execute(self, context):
        """
            Function to call HTTP POST request. Handles possible errors and informs user about execution process
            and results by printing info messages to Log and Blender console. Sends Request scene property payload
            as data
        """

        print(f"Executing: {bpy.context.scene.Request.method}request")

        # setting up
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(bpy.context.scene.Request.headers)
        payload = json.loads(bpy.context.scene.Request.payload.body)
        scene_response = context.scene.Response
        scene_response.successful = False

        # executing POST request and handling possible errors
        try:
            response = requests.post(endpoint, headers=headers, data=payload, timeout=TIMEOUT)
            scene_response.successful = True
        except requests.exceptions.HTTPError as httperr:
            print(HTTP_ERROR_MESSAGE, httperr)
            bpy.ops.log.add(log=HTTP_ERROR_MESSAGE + str(httperr))
        except requests.exceptions.ConnectionError as conerr:
            print(CONNECTION_ERROR_MESSAGE, conerr)
            bpy.ops.log.add(log=CONNECTION_ERROR_MESSAGE + str(conerr))
        except requests.exceptions.Timeout as tmterr:
            print(TIMEOUT_ERROR_MESSAGE, tmterr)
            bpy.ops.log.add(log=TIMEOUT_ERROR_MESSAGE + str(tmterr))
        except requests.exceptions.RequestException as error:
            print(UNKNOWN_ERROR_MESSAGE, error)
            bpy.ops.log.add(log=UNKNOWN_ERROR_MESSAGE + str(error))

        # if not successful - exit
        if not scene_response.successful:
            return {'FINISHED'}

        # filling scene response property with info
        scene_response.status = f"[{str(response.status_code)}]"
        scene_response.headers = json.dumps(dict(response.headers))
        scene_response.payload.body = str(response.content)

        # printing headers and body content to Blender console
        print(scene_response.headers)
        print(scene_response.payload.body)

        return {'FINISHED'}


class DoPutRequest(bpy.types.Operator):
    """
            DoPostRequest class wraps HTTP PUT request, using Blender Operator
    """

    bl_idname = "system.do_put_request"
    bl_label = "API put request operator"

    def execute(self, context):
        """
            Function to call HTTP PUT request. Handles possible errors and informs user about execution process
            and results by printing info messages to Log and Blender console. Sends Request scene property payload
            as data
        """

        print(f"Executing: {bpy.context.scene.Request.method}request")

        # setting up
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(bpy.context.scene.Request.headers)
        payload = json.loads(bpy.context.scene.Request.payload.body)
        scene_response = context.scene.Response
        scene_response.successful = False

        # executing PUT request and handling possible errors
        try:
            response = requests.put(endpoint, headers=headers, data=payload, timeout=TIMEOUT)
            scene_response.successful = True
        except requests.exceptions.HTTPError as httperr:
            print(HTTP_ERROR_MESSAGE, httperr)
            bpy.ops.log.add(log=HTTP_ERROR_MESSAGE + str(httperr))
        except requests.exceptions.ConnectionError as conerr:
            print(CONNECTION_ERROR_MESSAGE, conerr)
            bpy.ops.log.add(log=CONNECTION_ERROR_MESSAGE + str(conerr))
        except requests.exceptions.Timeout as tmterr:
            print(TIMEOUT_ERROR_MESSAGE, tmterr)
            bpy.ops.log.add(log=TIMEOUT_ERROR_MESSAGE + str(tmterr))
        except requests.exceptions.RequestException as error:
            print(UNKNOWN_ERROR_MESSAGE, error)
            bpy.ops.log.add(log=UNKNOWN_ERROR_MESSAGE + str(error))

        # if not successful - exit
        if not scene_response.successful:
            return {'FINISHED'}

        # filling scene response property with info
        scene_response.status = f"[{str(response.status_code)}]"
        scene_response.headers = json.dumps(dict(response.headers))
        scene_response.payload.body = str(response.content)

        # printing headers and body content to Blender console
        print(scene_response.headers)
        print(scene_response.payload.body)

        return {'FINISHED'}


class DoDeleteRequest(bpy.types.Operator):
    """
        DoPostRequest class wraps HTTP POST request, using Blender Operator
    """

    bl_idname = "system.do_delete_request"
    bl_label = "API delete request operator"

    def execute(self, context):
        """
            Function to call HTTP DELETE request. Handles possible errors and informs user about execution process
            and results by printing info messages to Log and Blender console
        """

        print(f"Executing: {bpy.context.scene.Request.method}request")

        # setting up
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = json.loads(bpy.context.scene.Request.headers)
        scene_response = context.scene.Response
        scene_response.successful = False

        # executing DELETE request and handling possible errors
        try:
            response = requests.delete(endpoint, headers=headers, timeout=TIMEOUT)
            scene_response.successful = True
        except requests.exceptions.HTTPError as httperr:
            print(HTTP_ERROR_MESSAGE, httperr)
            bpy.ops.log.add(log=HTTP_ERROR_MESSAGE + str(httperr))
        except requests.exceptions.ConnectionError as conerr:
            print(CONNECTION_ERROR_MESSAGE, conerr)
            bpy.ops.log.add(log=CONNECTION_ERROR_MESSAGE + str(conerr))
        except requests.exceptions.Timeout as tmterr:
            print(TIMEOUT_ERROR_MESSAGE, tmterr)
            bpy.ops.log.add(log=TIMEOUT_ERROR_MESSAGE + str(tmterr))
        except requests.exceptions.RequestException as error:
            print(UNKNOWN_ERROR_MESSAGE, error)
            bpy.ops.log.add(log=UNKNOWN_ERROR_MESSAGE + str(error))

        # if not successful - exit
        if not scene_response.successful:
            return {'FINISHED'}

        # filling scene response property with info
        scene_response.status = f"[{str(response.status_code)}]"
        scene_response.payload.body = json.dumps(dict(response.headers))
        scene_response.payload.body = str(response.content)

        # printing headers and body content to Blender console
        print(scene_response.headers)
        print(scene_response.payload.body)

        return {'FINISHED'}


class DoRequest(bpy.types.Operator):
    """
        Class DoRequest manages to call other HTTP requests operators, using Blender Operator
    """

    bl_idname = "system.do_request"
    bl_label = "API request operator"

    def execute(self, context):
        """
            Function to prepare the calling of HTTP request operator by filling it with data from scene Request property
        """

        # HTTP request method to call
        method = bpy.context.scene.Request.method

        # setting up request headers
        headers = {}
        if bpy.context.scene.Request.headers is not "":
            headers = json.loads(bpy.context.scene.Request.headers)

        # adding User authorization to request headers
        headers.update({'Authorization': "Bearer " + context.scene.APIData.user.authorization})
        bpy.context.scene.Request.headers = json.dumps(headers)

        # setting up request payload
        payload = {}
        if bpy.context.scene.Request.payload.body is not "":
            payload = json.loads(bpy.context.scene.Request.payload.body)

        bpy.context.scene.Request.payload.body = json.dumps(payload)

        # checking if the Request method is valid
        if method not in {'GET', 'POST', 'PUT', 'DELETE'}:
            bpy.ops.log.add(log=f"Error: Request method is invalid: {method}")
            return {'FINISHED'}

        # checking if the hostname is correct
        if not context.scene.APIData.host.startswith("https://") \
                and not context.scene.APIData.host.startswith("http://"):
            bpy.ops.log.add(log=INVALID_HOST_MESSAGE)
            return {'FINISHED'}

        # creating the operator call string as f.e. "bpy.ops.system.do_get_request"
        method_call = "bpy.ops.system.do_" + method.lower() + "_request()"

        # calling operator
        eval(method_call)
        response = bpy.context.scene.Response

        # emptying Request scene property before next possible usage
        bpy.context.scene.Request.method = ""
        bpy.context.scene.Request.headers = ""
        bpy.context.scene.Request.payload.body = ""
        bpy.context.scene.Request.endpoint = ""

        # if not successful - exit
        if not response.successful:
            return {'FINISHED'}

        # logging info about the response to Log
        bpy.ops.log.add(log="Status: " + response.status)
        bpy.ops.log.add(log="Headers: " + response.headers)
        bpy.ops.log.add(log="Body: " + response.payload.body)

        return {'FINISHED'}


class CheckConnection(bpy.types.Operator):
    """
        CheckConnection class checks if there is any response from the server, using Blender Operator
    """

    bl_idname = "system.check_connection"
    bl_label = "Check connection"

    def execute(self, context):
        """
            Function just calls a GET request with an empty body and headers
        """

        request = context.scene.Request
        request.method = "GET"
        request.headers = ""
        request.payload.body = ""

        # calling the request
        bpy.ops.system.do_request()

        return {'FINISHED'}


# ----------------- End: API communication helpers ----------------- #


# ----------------- Start: Export (VMCK requirements) ----------------- #

"""
    Implementing the Export of the 3D model in different file formats with textures to VMCK server.
    To do Export you should have save the project and and store your textures in "textures" folder in the project 
    root. Supported textures are in png and jpg format. All textures has to be in that folder in the same dir level. No
    deeper levels are allowed.
    
    Currently it's not possible to communicate with the server, so the response is hardcoded to show the response 
    logging process
"""


class Export(bpy.types.Operator):
    """
        Export class exports 3D models in different formats with their textures to the VMCK server
    """

    bl_idname = "system.export"
    bl_label = "Export"

    # invokes the dialog with the user to choose the file format
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    # file format dialog
    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "file_format")

    def execute(self, context):

        # checking the file name
        if bpy.context.scene.filename is "":
            bpy.ops.log.add(log=FILENAME_EMPTY_MESSAGE)
            return {'FINISHED'}

        # ------------------------------------------ #
        """
            Uncomment when the server will be up
        """

        # # checking the connection with the server
        # bpy.ops.system.check_connection()
        #
        # # if it's not possible to connect stops export
        # if not bpy.context.scene.Response.successful:
        #     return {'FINISHED'}
        # else:
        #     bpy.ops.log.clear()

        # ------------------------------------------ #

        # getting the project dir path
        dir = bpy.path.abspath("//")

        # preparing the 3D model file info
        file_format = context.scene.file_format + ".glb" \
            if context.scene.file_format == "GLTF" else context.scene.file_format

        # filename from the filename field
        filename = context.scene.filename

        # creating the filepath to save file to export
        filepath = bpy.path.abspath("//" + filename + "." + file_format.lower())

        # filling textures array with textures files names from textures folder in the project root
        textures = \
            [f for f in os.listdir(bpy.path.abspath("//" + "textures")) if f.endswith(".png") or f.endswith(".jpg")] \
                if os.path.exists(bpy.path.abspath("//" + "textures")) else []

        # saving the file to export using Blender Operators
        if file_format == 'OBJ':
            bpy.ops.export_scene.obj(filepath=filepath)
        elif file_format == 'FBX':
            bpy.ops.export_scene.fbx(filepath=filepath)
        elif file_format == 'BLEND':
            bpy.ops.wm.save_mainfile(filepath=filepath)
        elif file_format == 'GLTF':
            bpy.ops.export_scene.gltf(filepath=filepath)

        bpy.ops.log.add(log="Tmp file saved to: " + dir)
        bpy.ops.log.add(log="Exporting..." + filename)

        # setting up request variables
        endpoint = context.scene.APIData.host + context.scene.Request.endpoint
        headers = {'Authorization': "Bearer " + context.scene.APIData.user.authorization}

        # model to export
        files = {
            'name': filename,
            'model': (filename, open(filepath, 'rb'), 'multipart/form-data')
        }

        if file_format == 'OBJ':
            mtl_file_obj_filepath = dir + filename + ".mtl"
            files.update({'assets': (filename + ".mtl", open(mtl_file_obj_filepath), 'multipart/form-data')})

        # filling files dictionary with model textures if there is any
        if textures is not []:
            for key, texture in enumerate(textures):
                files.update({f'textures[{key}]': (texture,
                                                   open(bpy.path.abspath("//" + "textures/" + texture), 'rb'),
                                                   'multipart/form-data'
                                                   )
                              })

        context.scene.Response.successful = False
        response = None

        # sending POST request
        try:
            response = requests.post(endpoint, headers=headers, files=files, timeout=TIMEOUT)
            context.scene.Response.successful = True
        except requests.exceptions.HTTPError as httperr:
            print(HTTP_ERROR_MESSAGE, httperr)
            bpy.ops.log.add(log=HTTP_ERROR_MESSAGE + str(httperr))
        except requests.exceptions.ConnectionError as conerr:
            print(CONNECTION_ERROR_MESSAGE, conerr)
            bpy.ops.log.add(log=CONNECTION_ERROR_MESSAGE + str(conerr))
        except requests.exceptions.Timeout as tmterr:
            print(TIMEOUT_ERROR_MESSAGE, tmterr)
            bpy.ops.log.add(log=TIMEOUT_ERROR_MESSAGE + str(tmterr))
        except requests.exceptions.RequestException as error:
            print(UNKNOWN_ERROR_MESSAGE, error)
            bpy.ops.log.add(log=UNKNOWN_ERROR_MESSAGE + str(error))

        response_content = {}
        if response:
            bpy.ops.log.add(log="Status: " + f"[{str(response.status_code)}]")
            response_content = dict(response.content)

        # -------- Hard coded response ------------------------- #

        response_content = {
            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "structureId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "name": "Věž Kropáčka",
            "transformation": [
                [1, 2, 3],
                [4, 5, 6],
                [7, 8, 9]
            ],
            "createdDate": "2020-12-11T17:39:25.826Z",
            "model": {
                "id": "507f1f77bcf86cd799439011",
                "filename": filename + "." + file_format.lower(),
                "uploadDate": "2019-10-13T15:31:48.507Z",
                "href": "/models/507f1f77bcf86cd799439011"
            },
            "textures": [
                {
                    "id": "507f191e810c19729de860ea",
                    "filename": "vez_kropacka_stena.jpg",
                    "uploadDate": "2019-10-13T15:49:46.583Z",
                    "href": "/textures/507f191e810c19729de860ea"
                }
            ],
            "properties": [
                {
                    "weather": "rain20"
                }
            ],
            "status": "preparing",
            "assets": [
                {
                    "id": "54759eb3c090d83494e2d804",
                    "filename": "vez_kropacka.sfa",
                    "uploadDate": "2019-10-13T15:52:16.704Z",
                    "href": "/assets/54759eb3c090d83494e2d804"
                }
            ],
            "version": "1.15.3",
            "href": "/3DObjects/3fa85f64/0.15.3"
        }

        # --------------------------------------------------- #

        # logging the response to Log
        bpy.ops.log.add(log="Status: " + "[201]")

        # info about saved model
        bpy.ops.log.add(log="< ---- Model ---- >")
        bpy.ops.log.add(log="ID: " + response_content['model']['id'])
        bpy.ops.log.add(log="Filename: " + response_content['model']['filename'])
        bpy.ops.log.add(log="Upload date: " + response_content['model']['uploadDate'])
        bpy.ops.log.add(log="Href: " + response_content['model']['href'])

        # info about model textures
        bpy.ops.log.add(log="< ---- Textures ---- >")
        for texture in response_content['textures']:
            bpy.ops.log.add(log="ID: " + texture['id'])
            bpy.ops.log.add(log="Filename: " + texture['filename'])
            bpy.ops.log.add(log="Upload date: " + texture['uploadDate'])
            bpy.ops.log.add(log="Href: " + texture['href'])
            bpy.ops.log.add(log="------------------------")

        bpy.ops.log.add(log="Done!")

        return {'FINISHED'}


# ----------------- Start: Export (VMCK requirements) ----------------- #


# ----------------- Start: Add-on UI --------------- #

"""
    Add-on UI definition
"""


class ExporterPanel(bpy.types.Panel):
    """
        ExporterPanel class defines the look of the add-on UI
    """
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
        """
            Function to create add-on UI layout
        """

        # scene properties
        APIData = context.scene.APIData
        Request = context.scene.Request
        LogGroup = context.scene.LogGroup

        main_layout = self.layout
        main_layout.label(text=CREDENTIALS_SECTION_NAME)

        # Credentials section
        credentials_box = main_layout.box()
        credentials_box_split = credentials_box.split()

        credentials_box_left_column = credentials_box_split.column(align=True)
        credentials_box_right_column = credentials_box_split.column(align=True)

        credentials_box_left_column.label(text=USERNAME_FIELD)
        credentials_box_left_column.prop(APIData.user, "username", icon_only=True)

        credentials_box_right_column.label(text=USER_EMAIL_FIELD)
        credentials_box_right_column.prop(APIData.user, "user_email", icon_only=True)

        credentials_box.row().prop(APIData.user, "authorization")

        # server info
        host_box = main_layout.box()
        host_box.row().prop(APIData, "host")
        host_box.row().prop(Request, "endpoint")
        host_box.split(factor=0.5).operator("system.check_connection")

        # TODO ------ Import section#
        main_layout.label(text=IMPORT_SECTION_NAME)
        import_box = main_layout.box()
        # ----------- #

        # Export section
        main_layout.label(text=EXPORT_SECTION_NAME)
        export_box = main_layout.box()
        export_filename_row = export_box.row()
        export_filename_row.prop(context.scene, "filename")
        export_buttons_row = export_box.row()
        export_buttons_row.operator("system.export")

        # Log section
        log_box = main_layout.box()
        log_box.label(text=LOG_SECTION_NAME)
        log_box.template_list("LOGLIST_UL_log_list", "", LogGroup, "coll", LogGroup, "index",
                              rows=3, maxrows=5, columns=3, type='DEFAULT')
        log_box.operator("log.clear")


# ----------------- End: Add-on UI --------------- #


# ----------------- Start: Add-on registration --------------- #

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
    bpy.types.Scene.filename = bpy.props.StringProperty(
        name="Filename",
        description="Filename of file to export",
        default=""
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.LogGroup
    del bpy.types.Scene.Response
    del bpy.types.Scene.Request
    del bpy.types.Scene.APIData


# ----------------- End: Add-on registration --------------- #

if __name__ == "__main__":
    # when running add-on as script
    register()
