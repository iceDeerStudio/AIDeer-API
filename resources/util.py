from flask_restx import Resource, Namespace, marshal, reqparse
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from orm_models.user import UserORM
from models import message_model
from extensions import db

util_namespace = Namespace("util", description="Utility operations")

util_namespace.add_model("Message", message_model)
    
@util_namespace.route("/init")
class Init(Resource):
    @util_namespace.response(200, "Success", message_model)
    def get(self):
        """
        Initialize database.
        """
        db.create_all()
        if not UserORM.query.filter_by(username=current_app.config["ADMIN_USERNAME"]).first():
            admin = UserORM(
                username=current_app.config["ADMIN_USERNAME"],
                nickname=current_app.config["ADMIN_USERNAME"],
                permission_level=2,
            )
            admin.set_password(current_app.config["ADMIN_PASSWORD"])
            db.session.add(admin)
            db.session.commit()
        return marshal({"message": "Database initialized"}, message_model), 200
    
@util_namespace.route("/drop")
class Drop(Resource):
    @util_namespace.response(200, "Success", message_model)
    def get(self):
        """
        Drop database.
        """
        db.drop_all()
        return marshal({"message": "Database dropped"}, message_model), 200