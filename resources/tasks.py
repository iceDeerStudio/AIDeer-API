from flask_jwt_extended import jwt_required, get_jwt, current_user
from flask_restx import Resource, Namespace, marshal, reqparse
from orm_models.chat import ChatORM
from orm_models.preset import PresetORM
from models import message_model, task_model
from extensions import db
from celery.result import AsyncResult
from tasks import ChatGenerationTask

tasks_namespace = Namespace("tasks", description="Task operations")

task_parser = reqparse.RequestParser()
task_parser.add_argument("chat_id", type=str, required=True, help="Chat ID of the task.")

tasks_namespace.add_model("Task", task_model)
tasks_namespace.add_model("Message", message_model)


@tasks_namespace.route("/<string:task_uuid>")
class Task(Resource):
    
    @jwt_required
    @tasks_namespace.response(200, "Success", task_model)
    @tasks_namespace.response(404, "Task not found", message_model)
    def get(self, task_uuid):
        """
        Retrieve a task by UUID
        ---
        ! If the task is in SUCCESS or FAILURE status, the result will be included in the response
        """
        task = AsyncResult(task_uuid)

        if not task:
            return {"message": "Task not found"}, 404
        
        status = {
            "id": task.id,
            "status": task.status,
        }

        if task.status in ["SUCCESS", "FAILURE"]:
            status["result"] = task.result

        return marshal(status, task_model), 200
    
    @jwt_required
    def delete(self, task_uuid):
        """
        Delete a task by UUID
        ---
        ! This will revoke and forget the task
        """
        task = AsyncResult(task_uuid)

        if not task:
            return {"message": "Task not found"}, 404
        
        task.revoke(terminate=True)
        task.forget()

        return {"message": "Task deleted"}, 200
    

@tasks_namespace.route("")
class TaskList(Resource):

    @jwt_required
    @tasks_namespace.expect(task_parser)
    @tasks_namespace.response(201, "Task created", message_model)
    @tasks_namespace.response(402, "Insufficient credits", message_model)
    @tasks_namespace.response(403, "Permission denied", message_model)
    @tasks_namespace.response(404, "Chat not found", message_model)
    @tasks_namespace.response(409, "Task already exists", message_model)
    def post(self):
        """
        Create a new task
        ---
        ! Update the chat with user's input before creating a task
        ! If the chat already has a task, return 409
        ! If the user does not have enough credits, return 402
        This will start a new task to generate a chat based on the preset and chat content.
        The task will be added to the chat and the chat will be updated with the result.
        """
        data = task_parser.parse_args()

        chat = ChatORM.query.filter_by(uuid=data["chat_id"]).first()
        if not chat:
            return marshal({"message": "Chat not found"}, message_model), 404
        
        preset = PresetORM.query.filter_by(id=chat.preset_id).first()
        if not preset:
            return marshal({"message": "Preset not found"}, message_model), 404
        
        if chat.owner_id != current_user.id:
            return marshal({"message": "You are not the owner of the chat"}, message_model), 403
        if current_user.credits <= 0:
            return marshal({"message": "You do not have enough credits, please purchase more credits"}, message_model), 402
        
        if chat.task_id:
            return marshal({"message": "The chat already has a task"}, message_model), 409
        
        preset_messages = [{"role": message.role, "content": message.content} for message in preset.get_content()]
        chat_messages = [{"role": message.role, "content": message.content} for message in chat.get_content()]
        messages = preset_messages + chat_messages

        task = ChatGenerationTask.apply_async(args=(chat.id, messages))
        chat.task_id = task.id
        db.session.commit()

        return marshal({"message": "Task created"}, message_model), 201, {"Location": f"/tasks/{task.id}"}
