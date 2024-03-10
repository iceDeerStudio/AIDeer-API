from orm_models.chat import ChatORM
from orm_models.preset import PresetORM
from celery import Celery, Task, current_task
from celery.result import AsyncResult
from flask import current_app
from http import HTTPStatus
from dashscope import Generation
from extensions import db
from datetime import datetime
from orm_models.usage import UsageORM
from config import Config
import pika
import json

celery_app = Celery("tasks", backend=Config.CELERY_RESULT_BACKEND, broker=Config.CELERY_BROKER_URL)

class ChatGenerationTask(Task):
    name = "chat_generation_task"

    def run(self, chat_id: int, messages: list):
        self.chat_id = chat_id

        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(current_app.config["RABBITMQ_HOST"], current_app.config["RABBITMQ_PORT"]))
        channel = connection.channel()
        channel.queue_declare(queue=current_task.request.id)

        # Generate chat
        responses = Generation.call(
            Generation.Models.qwen_max,
            messages=messages,
            result_format='message',
            stream=True,
            incremental_output=True
        )

        full_content = ''
        for response in responses:
            if response.status_code == HTTPStatus.OK:
                new_content = response.output.choices[0]['message']['content']
                message = json.dumps({"status": "in_progress", "content": new_content})
                channel.basic_publish(exchange='', routing_key=current_task.request.id, body=message)
                full_content += new_content
            else:
                message = json.dumps({"status": "error", "content": response.message})
                channel.basic_publish(exchange='', routing_key=current_task.request.id, body=message)
                raise Exception(f"Error occurred while generating chat: {response.message}")

        message = json.dumps({"status": "success", "content": full_content})

        return full_content
    
    def on_success(self, retval, task_id, args, kwargs):
        """
        This method will be called when the chat generation task is successful.
        It will record the usage and add the generated content to the chat.
        """
        chat = ChatORM.query.filter_by(id=self.chat_id).first()
        if not chat:
            raise Exception("Chat not found")
        
        # Record usage
        usage = UsageORM(user_id=chat.owner_id, token_used=len(retval))
        db.session.add(usage)

        # Add message to chat
        new_content = {"type": "chat", "role": "assistant", "content": retval, "visible": True, "created_at": datetime.now()}
        chat.add_message(new_content)

        # Remove task ID from chat
        chat.task_id = None
        db.session.commit()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        chat = ChatORM.query.filter_by(id=self.chat_id).first()
        if not chat:
            raise Exception("Chat not found")

        chat.task_id = None
        db.session.commit()


celery_app.tasks.register(ChatGenerationTask)
