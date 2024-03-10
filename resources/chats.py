from flask_jwt_extended import jwt_required, get_jwt, current_user
from flask_restx import Resource, Namespace, marshal, reqparse
from flask import send_file
from werkzeug.datastructures import FileStorage
from models import message_model, chat_model, chat_list_model, chat_message_model
from orm_models.user import UserORM
from orm_models.chat import ChatORM
from extensions import db

chats_namespace = Namespace("chats", description="Chat operations")

chat_parser = reqparse.RequestParser()
chat_parser.add_argument("preset_id", type=int, required=True, help="Preset ID of the chat.")
chat_parser.add_argument("title", type=str, required=True, help="Title of the chat.")
chat_parser.add_argument("content", type=str, required=True, help="Content of the chat.")

chats_namespace.add_model("Chat", chat_model)
chats_namespace.add_model("Message", message_model)
chats_namespace.add_model("ChatList", chat_list_model)
chats_namespace.add_model("ChatMessage", chat_message_model)

@chats_namespace.route("/<string:chat_uuid>")
class ChatResource(Resource):

    @jwt_required()
    @chats_namespace.doc(security="Bearer Auth")
    @chats_namespace.response(200, "Success", chat_model)
    @chats_namespace.response(201, "Copy created", chat_model)
    @chats_namespace.response(404, "Chat not found", message_model)
    def get(self, chat_uuid):
        """
        Get chat by UUID
        ---
        ! Rteturn a copy of the chat if the user is not the owner
        """
        chat = ChatORM.query.filter_by(uuid=chat_uuid).first()

        if not chat:
            return marshal({"message": "Chat not found"}, message_model), 404
        
        if chat.owner_id != current_user.id:
            # If the user is not the dialog owner, make a copy of the chat
            new_chat = ChatORM(
                owner_id=current_user.id,
                preset_id=chat.preset_id,
                content=chat.content,
            )
            current_user.chats.append(new_chat)
            db.session.commit()
            return marshal(new_chat.to_dict(), chat_model), 201, {"Location": f"/chats/{new_chat.uuid}"}
        
        return marshal(chat.to_dict(), chat_model), 200

    @jwt_required()
    @chats_namespace.doc(security="Bearer Auth")
    @chats_namespace.expect(chat_parser)
    @chats_namespace.response(200, "Chat updated", message_model)
    @chats_namespace.response(403, "Permission denied", message_model)
    @chats_namespace.response(404, "Chat not found", message_model)
    def put(self, chat_uuid):
        """
        Update chat by UUID
        """
        data = chat_parser.parse_args()
        chat = ChatORM.query.filter_by(uuid=chat_uuid).first()

        if not chat:
            return marshal({"message": "Chat not found"}, message_model), 404
        
        if chat.owner_id != current_user.id and current_user.permission_level < 2:
            return marshal({"message": "You do not have permission to update this chat"}, message_model), 403
        
        chat.preset_id = data["preset_id"]
        chat.content = data["content"]
        db.session.commit()
        return marshal({"message": "Chat updated successfully"}, message_model), 200

    @jwt_required()
    @chats_namespace.doc(security="Bearer Auth")
    @chats_namespace.response(200, "Success", message_model)
    @chats_namespace.response(403, "Permission denied", message_model)
    @chats_namespace.response(404, "Chat not found", message_model)
    def delete(self, chat_uuid):
        """
        Delete chat by UUID
        """
        chat = ChatORM.query.filter_by(uuid=chat_uuid).first()

        if not chat:
            return marshal({"message": "Chat not found"}, message_model), 404
        if chat.owner_id != current_user.id and current_user.permission_level < 2:
            return marshal({"message": "You do not have permission to delete this chat"}, message_model), 403
        
        db.session.delete(chat)
        db.session.commit()
        return marshal({"message": "Chat deleted"}, message_model), 200


@chats_namespace.route("")
class ChatsResource(Resource):
    @jwt_required()
    @chats_namespace.doc(security="Bearer Auth")
    @chats_namespace.response(200, "Success", chat_model)
    @chats_namespace.response(403, "Permission denied", message_model)
    def post(self):
        """
        Create a new chat
        """
        data = chat_parser.parse_args()
        
        chat = ChatORM(
            owner_id=current_user.id,
            preset_id=data["preset_id"],
            title=data["title"],
            content=data["content"],
        
        )

        current_user.chats.append(chat)
        db.session.commit()
        return marshal(chat.to_dict(), chat_model), 201, {"Location": f"/chats/{chat.uuid}"}
    
    
    @jwt_required()
    @chats_namespace.doc(security="Bearer Auth")
    @chats_namespace.response(200, "Success", chat_list_model)
    def get(self):
        """
        Get all chats of the user
        """
        chats = current_user.chats.all()
        return marshal({"chat_ids": [chat.uuid for chat in chats]}, chat_list_model), 200