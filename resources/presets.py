from flask_jwt_extended import jwt_required, get_jwt, current_user
from flask_restx import Resource, Namespace, marshal, reqparse
from flask import send_file
from werkzeug.datastructures import FileStorage
from models import message_model, preset_model, preset_list_model
from orm_models.chat import ChatORM
from orm_models.preset import PresetORM
from extensions import db
from sqlalchemy import or_, and_

presets_namespace = Namespace("presets", description="Preset operations")

preset_parser = reqparse.RequestParser()
preset_parser.add_argument("name", type=str, required=True, help="Name of the preset.")
preset_parser.add_argument(
    "description", type=str, required=True, help="Description of the preset."
)
preset_parser.add_argument(
    "type",
    type=str,
    required=True,
    help="Type of the preset.",
    choices=["chat_generation", "image_generation"],
)
preset_parser.add_argument(
    "content", type=str, required=True, help="Content of the preset."
)
preset_parser.add_argument(
    "visibility",
    type=str,
    required=True,
    help="Visibility of the preset. If the user is not an admin, the visibility will be set to unlisted if the user tries to set it to public.",
    choices=["public", "unlisted", "private"],
)

presets_namespace.add_model("Preset", preset_model)
presets_namespace.add_model("Message", message_model)
presets_namespace.add_model("PresetList", preset_list_model)


@presets_namespace.route("/<string:preset_uuid>")
class Preset(Resource):
    @jwt_required
    def get(self, preset_uuid):
        preset = PresetORM.query.filter_by(uuid=preset_uuid).first()
        if not preset:
            return {"message": "Preset not found"}, 404
        return marshal(preset, preset_model), 200

    @jwt_required
    @presets_namespace.expect(preset_parser)
    @presets_namespace.response(200, "Presets updated", message_model)
    @presets_namespace.response(403, "Permission denied", message_model)
    @presets_namespace.response(404, "Preset not found", message_model)
    def put(self, preset_uuid):
        """
        Update a preset by UUID
        """
        data = preset_parser.parse_args()
        preset = PresetORM.query.filter_by(uuid=preset_uuid).first()

        if not preset:
            return {"message": "Preset not found"}, 404

        if preset.owner_id != current_user.id and current_user.permission_level < 2:
            return {"message": "You do not have permission to update this preset"}, 403

        preset.name = data["name"]
        preset.description = data["description"]
        preset.type = data["type"]
        preset.content = data["content"]

        if data["visibility"] == "public" and current_user.permission_level < 2:
            preset.visibility = "unlisted"
        else:
            preset.visibility = data["visibility"]

        db.session.commit()
        return {"message": "Preset updated"}, 200

    @jwt_required
    @presets_namespace.response(200, "Preset deleted", message_model)
    @presets_namespace.response(403, "Permission denied", message_model)
    @presets_namespace.response(404, "Preset not found", message_model)
    def delete(self, preset_uuid):
        """
        Delete a preset by UUID
        ---
        This operation is irreversible and will permanently delete the preset.
        All chats generated with this preset will be deleted.
        If you are not an admin, you can only delete presets that you own and are not public.
        """
        preset = PresetORM.query.filter_by(uuid=preset_uuid).first()
        if not preset:
            return {"message": "Preset not found"}, 404
        
        if preset.owner_id != current_user.id and current_user.permission_level < 2:
            return {"message": "You do not have permission to delete this preset"}, 403
        
        if preset.visibility == "public" and current_user.permission_level < 2:
            return {"message": "You do not have permission to delete a public preset"}, 403
        
        db.session.delete(preset)
        db.session.commit()
        return {"message": "Preset deleted"}, 200


@presets_namespace.route("")
class PresetList(Resource):

    @jwt_required
    @presets_namespace.response(200, "Success", preset_list_model)
    def get(self):
        """
        Get a list of all presets
        ---
        This will return a list of all presets that the user has access to.
        For non-admin users, this will only return public and owned presets.
        For admin users, this will return public, unlisted, and owned presets.
        """
        presets = PresetORM.query.filter(
            or_(
                PresetORM.owner_id == current_user.id,
                PresetORM.visibility == "public",
                and_(
                    PresetORM.visibility == "unlisted",
                    current_user.permission_level > 1,
                ),
            )
        ).all()
        return {"preset_ids": [preset.uuid for preset in presets]}, 200

    @jwt_required
    @presets_namespace.expect(preset_parser)
    @presets_namespace.response(201, "Preset created", message_model)
    def post(self):
        """
        Create a new preset
        """
        data = preset_parser.parse_args()

        visibility = data["visibility"]
        if visibility == "public" and current_user.permission_level < 2:
            visibility = "unlisted"

        preset = PresetORM(
            owner_id=current_user.id,
            name=data["name"],
            description=data["description"],
            type=data["type"],
            content=data["content"],
            visibility=visibility,
        )
        current_user.owned_presets.append(preset)
        db.session.commit()
        return (
            {"message": "Preset created"},
            201,
            {"Location": f"/presets/{preset.uuid}"},
        )
