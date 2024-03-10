from flask_restx import Model, fields

message_model = Model(
    "Message",
    {"message": fields.String(required=True, description="The message to be returned")},
)

user_model = Model(
    "User",
    {
        "id": fields.Integer(required=True, description="The user unique identifier"),
        "username": fields.String(
            required=True, description="The username of the user"
        ),
        "nickname": fields.String(
            required=True, description="The nickname of the user"
        ),
        "permission_level": fields.Integer(
            required=True,
            description="The permission level of the user (0: visitor, 1: user, 2: admin).",
        ),
        "avatar": fields.String(
            required=True, description="The avatar URL of the user"
        ),
    },
)

users_list_model = Model(
    "UsersList",
    {
        "users": fields.List(
            fields.Nested(user_model), required=True, description="A list of users"
        )
    },
)

token_model = Model(
    "Token",
    {
        "access_token": fields.String(
            required=True, description="The access token for the user"
        ),
        "refresh_token": fields.String(
            required=False, description="The refresh token for the user"
        ),
    },
)

chat_message_model = Model(
    "ChatMessage",
    {
        "type": fields.String(
            required=True,
            description="The type of the message (text, image)",
            enum=["text", "image"],
        ),
        "role": fields.String(
            required=True,
            description="The role of the message (user, assistant, system)",
            enum=["user", "assistant", "system"],
        ),
        "content": fields.String(
            required=True,
            description="The content of the message, can be text or URL(only for image)",
        ),
        "visible": fields.Boolean(
            required=True, description="The visibility of the message"
        ),
        "created_at": fields.DateTime(
            required=True, description="The creation time of the message"
        ),
    },
)

chat_model = Model(
    "Chat",
    {
        "id": fields.Integer(required=True, description="The chat unique identifier"),
        "uuid": fields.String(required=True, description="The UUID of the chat"),
        "owner_id": fields.Integer(
            required=True, description="The user unique identifier of the owner"
        ),
        "preset_id": fields.Integer(
            required=True, description="The preset unique identifier of the chat"
        ),
        "title": fields.String(required=True, description="The title of the chat"),
        "content": fields.List(
            fields.Nested(chat_message_model),
            required=True,
            description="The content of the chat",
        ),
        "created_at": fields.DateTime(
            required=True, description="The creation time of the chat"
        ),
        "updated_at": fields.DateTime(
            required=True, description="The update time of the chat"
        ),
    },
)

chat_list_model = Model(
    "ChatList",
    {
        "chat_ids": fields.List(
            fields.String, required=True, description="A list of chat UUIDs"
        )
    },
)

preset_model = Model(
    "Preset",
    {
        "id": fields.Integer(required=True, description="The preset unique identifier"),
        "uuid": fields.String(required=True, description="The UUID of the preset"),
        "name": fields.String(required=True, description="The name of the preset"),
        "description": fields.String(
            required=True, description="The description of the preset"
        ),
        "type": fields.String(
            required=True,
            description="The type of the preset (chat_generation, image_generation)",
            enum=["chat_generation", "image_generation"],
        ),
        "avatar": fields.String(
            required=True, description="The avatar URL of the preset"
        ),
        "content": fields.List(
            fields.Nested(chat_message_model),
            required=True,
            description="The content of the preset",
        ),
        "visibility": fields.String(
            required=True,
            description="The visibility of the preset (private, unlisted, public)",
            enum=["public", "unlisted", "private"],
        ),
        "created_at": fields.DateTime(
            required=True, description="The creation time of the preset"
        ),
        "updated_at": fields.DateTime(
            required=True, description="The update time of the preset"
        ),
    },
)

preset_list_model = Model(
    "PresetList",
    {
        "preset_ids": fields.List(
            fields.String, required=True, description="A list of preset UUIDs"
        )
    },
)

task_model = Model(
    "Task",
    {
        "id": fields.String(required=True, description="The task unique identifier"),
        "status": fields.String(
            required=True,
            description="The status of the task (PENDING, STARTED, SUCCESS, FAILURE)",
            enum=["PENDING", "STARTED", "SUCCESS", "FAILURE"],
        ),
        "result": fields.String(
            required=False, description="The result of the task"
        ),
    },
)