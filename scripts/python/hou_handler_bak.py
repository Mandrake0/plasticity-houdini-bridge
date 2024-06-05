# TODO:
# - [ ] All on_... methods should call operators (to better handle undo, to have reporting be visible in the ui, etc)
from collections import defaultdict
from enum import Enum

import hou
# import mathutils
import numpy as np

class PlasticityIdUniquenessScope(Enum):
    ITEM = 0
    GROUP = 1
    EMPTY = 2


class ObjectType(Enum):
    SOLID = 0
    SHEET = 1
    WIRE = 2
    GROUP = 5
    EMPTY = 6


class SceneHandler:
    def __init__(self):
        # NOTE: filename -> [item/group] -> id -> object
        # NOTE: items/groups have overlapping ids
        # NOTE: it turns out that caching this is unsafe with undo/redo; call __prepare() before every update
        self.files = {}

    def __create_mesh(self, name, verts, indices, normals, groups, face_ids):
        print("__create_mesh")
        geo = hou.Geometry()
        
        # ----------------------------- 
        # Add Attributes
        # ----------------------------- 
        n_attrib = geo.addAttrib(hou.attribType.Point, "N", hou.Vector3(0,0,0))
        faceids_attrib = geo.addAttrib(hou.attribType.Prim, "id", 0)
        name_attrib = geo.addAttrib(hou.attribType.Prim, "name", "")
        
        verts    = np.array_split(verts.astype(np.float64), len(verts)/3)
        normals     = np.array_split(normals.astype(np.float64), len(normals)/3)

        # Creates Points
        for i in range(0, int(len(verts))):
            pt = geo.createPoint()
            pt.setPosition(verts[i])
            pt.setAttribValue(n_attrib, normals[i]*-1) # Value is Inverted: *-1

        # Create Facet
        for i in range(0, len(verts)):
            if not (i % 3):
                poly = geo.createPolygon()
            poly.addVertex(geo.point(int(verts[i])))

        # Add Face ids
        for i in range(0, len(face_ids)):   
            for prim_pos in range(int(groups[i*2]/3),int(groups[i*2]/3 + groups[i*2+1]/3)):
                prim = geo.prim(prim_pos)
                prim.setAttribValue(faceids_attrib, int(face_ids[i]))
                prim.setAttribValue(name_attrib, name)

        return geo

    def __update_object_and_mesh(self, obj, object_type, version, name, verts, indices, normals, groups, face_ids):
        print("__update_object_and_mesh")

    def __update_mesh_ngons(self, obj, version, faces, verts, indices, normals, groups, face_ids):
        # there is a Implementation in the HDA Asset that converts Triangulated Mesh to Ngons
        print("__update_mesh_ngons | Not Implemented")

    def update_pivot(self, obj):
        print("update_pivot | Not Implemented")
        # NOTE: this doesn't work unfortunately. It seems like changing matrix_world or matrix_local
        # is only possible in special contexts that I cannot yet figure out.
        return


    def __add_object(self, filename, object_type, plasticity_id, name, mesh):
        print("__add_object")
        # Custom Mesh Object
        mesh_obj = {}
        mesh_obj["name"] = name
        mesh_obj["mesh"] = mesh
        mesh_obj["plasticity_id"] = plasticity_id
        mesh_obj["plasticity_filename"] = filename
        self.files[filename][PlasticityIdUniquenessScope.ITEM][plasticity_id] = mesh_obj
        return mesh_obj

    def __delete_object(self, filename, version, plasticity_id):
        print("__delete_object")
        obj = self.files[filename][PlasticityIdUniquenessScope.ITEM].pop(
            plasticity_id, None)
        # if obj:
        #     del self.hou_geo.pop(obj) # Delete Geometry Object 

    def __delete_group(self, filename, version, plasticity_id):
        print("__delete_group")
        group = self.files[filename][PlasticityIdUniquenessScope.GROUP].pop(
            plasticity_id, None)
        # if group:
        #     del self.hou_groups.pop(obj) # Delete Groups Object 

    def __replace_objects(self, filename, inbox_collection, version, objects):
        print("__replace_objects")

        for item in objects:
            object_type = item['type']
            name = item['name']
            plasticity_id = item['id']
            material_id = item['material_id']
            parent_id = item['parent_id']
            flags = item['flags']
            verts = item['vertices']
            faces = item['faces']
            normals = item['normals']
            groups = item['groups']
            face_ids = item['face_ids']

            if object_type == ObjectType.SOLID.value or object_type == ObjectType.SHEET.value:
                obj = None
                if plasticity_id not in self.files[filename][PlasticityIdUniquenessScope.ITEM]:
                    mesh = self.__create_mesh(
                        name, verts, faces, normals, groups, face_ids)
                    obj = self.__add_object(filename, object_type,
                                            plasticity_id, name, mesh)
                else:
                    obj = self.files[filename][PlasticityIdUniquenessScope.ITEM].get(
                        plasticity_id)
                    if obj:
                        self.__update_object_and_mesh(
                            obj, object_type, version, name, verts, faces, normals, groups, face_ids)
                        # for parent in obj.users_collection:
                        #     parent.objects.unlink(obj)

            elif object_type == ObjectType.GROUP.value:
                if plasticity_id > 0:
                    group_collection = None
                    if plasticity_id not in self.files[filename][PlasticityIdUniquenessScope.GROUP]:
                        group_collection = {}
                        group_collection["plasticity_id"] = plasticity_id
                        group_collection["plasticity_filename"] = filename
                        self.files[filename][PlasticityIdUniquenessScope.GROUP][plasticity_id] = group_collection
                    else:
                        group_collection = self.files[filename][PlasticityIdUniquenessScope.GROUP].get(
                            plasticity_id)
                        group_collection.name = name
                        #collections_to_unlink.add(group_collection)


        for item in objects:
            object_type = item['type']
            uniqueness_scope = PlasticityIdUniquenessScope.ITEM if object_type != ObjectType.GROUP.value else PlasticityIdUniquenessScope.GROUP
            plasticity_id = item['id']
            parent_id = item['parent_id']
            flags = item['flags']
            is_hidden = flags & 1
            is_visible = flags & 2
            is_selectable = flags & 4

            if plasticity_id == 0:  # root group
                continue

            obj = self.files[filename][uniqueness_scope].get(
                plasticity_id)
            if not obj:
                self.report(
                    {'ERROR'}, "Object of type {} with id {} and parent_id {} not found".format(
                        object_type, plasticity_id, parent_id))
                continue

            parent = inbox_collection if parent_id == 0 else self.files[filename][PlasticityIdUniquenessScope.GROUP].get(
                parent_id)
            if not parent:
                self.report(
                    {'ERROR'}, "Parent of object of type {} with id {} and parent_id {} not found".format(
                        object_type, plasticity_id, parent_id))
                continue

            if object_type == ObjectType.GROUP.value:
                parent.children.link(obj)
                group_collection.hide_viewport = is_hidden or not is_visible
                group_collection.hide_select = not is_selectable
            else:
                parent.objects.link(obj)
                obj.hide_set(is_hidden or not is_visible)
                obj.hide_select = not is_selectable

    def __inbox_for_filename(self, filename):
        print("__inbox_for_filename")
        # plasticity_collection = bpy.data.collections.get("Plasticity")
        # if not plasticity_collection:
        #     plasticity_collection = bpy.data.collections.new("Plasticity")
        #     bpy.context.scene.collection.children.link(plasticity_collection)

        # filename_collection = plasticity_collection.children.get(filename)
        # if not filename_collection:
        #     filename_collection = bpy.data.collections.new(filename)
        #     plasticity_collection.children.link(filename_collection)

        # inbox_collections = [
        #     child for child in filename_collection.children if "inbox" in child]
        # inbox_collection = None
        # if len(inbox_collections) > 0:
        #     inbox_collection = inbox_collections[0]
        # if not inbox_collection:
        #     inbox_collection = bpy.data.collections.new("Inbox")
        #     filename_collection.children.link(inbox_collection)
        #     inbox_collection["inbox"] = True
        # return inbox_collection

    def __prepare(self, filename):
        print("__prepare")
        inbox_collection = self.__inbox_for_filename(filename)

        def gather_items(collection):
            objects = list(collection.objects)
            collections = list(collection.children)
            for sub_collection in collection.children:
                subobjects, subcollections = gather_items(sub_collection)
                objects.extend(subobjects)
                collections.extend(subcollections)
            return objects, collections
        objects, collections = gather_items(inbox_collection)

        existing_objects = {
            PlasticityIdUniquenessScope.ITEM: {},
            PlasticityIdUniquenessScope.GROUP: {}
        }
        for obj in objects:
            if "plasticity_id" not in obj:
                continue
            plasticity_filename = obj.get("plasticity_filename")
            plasticity_id = obj.get("plasticity_id")
            if plasticity_id:
                existing_objects[PlasticityIdUniquenessScope.ITEM][plasticity_id] = obj
        for collection in collections:
            if "plasticity_id" not in collection:
                continue
            plasticity_id = collection.get("plasticity_id")
            if plasticity_id:
                existing_objects[PlasticityIdUniquenessScope.GROUP][plasticity_id] = collection

        self.files[filename] = existing_objects


    def on_transaction(self, transaction):
        print("on_transaction")
        filename = transaction["filename"]
        version = transaction["version"]

        self.report({'INFO'}, "Updating " + filename +
                    " to version " + str(version))

        inbox_collection = self.__prepare(filename)

        if "delete" in transaction:
            for plasticity_id in transaction["delete"]:
                self.__delete_object(filename, version, plasticity_id)

        if "add" in transaction:
            self.__replace_objects(filename, inbox_collection,
                                   version, transaction["add"])

        if "update" in transaction:
            self.__replace_objects(filename, inbox_collection,
                                   version, transaction["update"])


    def on_list(self, message):
        print("on_list")
        filename = message["filename"]
        version = message["version"]

        self.report({'INFO'}, "Updating " + filename +
                    " to version " + str(version))

        inbox_collection = self.__prepare(filename)

        all_items = set()
        all_groups = set()
        if "add" in message:
            for item in message["add"]:
                if item["type"] == ObjectType.GROUP.value:
                    all_groups.add(item["id"])
                else:
                    all_items.add(item["id"])
            self.__replace_objects(filename, inbox_collection,
                                   version, message["add"])

        to_delete = []
        for plasticity_id, obj in self.files[filename][PlasticityIdUniquenessScope.ITEM].items():
            if plasticity_id not in all_items:
                to_delete.append(plasticity_id)
        for plasticity_id in to_delete:
            self.__delete_object(filename, version, plasticity_id)

        to_delete = []
        for plasticity_id, obj in self.files[filename][PlasticityIdUniquenessScope.GROUP].items():
            if plasticity_id not in all_groups:
                to_delete.append(plasticity_id)
        for plasticity_id in to_delete:
            self.__delete_group(filename, version, plasticity_id)

        print("Safe Files to Session")
        hou.session.files = self.files # Send the Values to the Houdini Session where the HDA can read the values 

    def on_refacet(self, filename, version, plasticity_ids, versions, faces, positions, indices, normals, groups, face_ids):
        print("on_refacet | Not Implemented")


    def on_new_version(self, filename, version):
        self.report({'INFO'}, "New version of " +
                    filename + " available: " + str(version))

    def on_new_file(self, filename):
        self.report({'INFO'}, "New file available: " + filename)

    def on_connect(self):
        self.files = {}

    def on_disconnect(self):
        self.files = {}

    def report(self, level, message):
        print(message)
