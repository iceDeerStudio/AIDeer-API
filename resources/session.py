from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, current_user
from flask_restx import Namespace, Resource, reqparse, marshal
from flask import current_app
from models import token_model, message_model
from orm_models.user import UserORM, TokenBlocklistORM
from extensions import db
import requests
from utils import generate_random_string, get_wechat_login_info, check_wechat_login_info

session_namespace = Namespace("session", description="Session operations")
login_parser = reqparse.RequestParser()
login_parser.add_argument(
    "username", type=str, required=True, help="Username of the user."
)
login_parser.add_argument(
    "password", type=str, required=True, help="Password of the user."
)
wechat_login_parser = reqparse.RequestParser()
wechat_login_parser.add_argument(
    "code", type=str, required=True, help="Code from WeChat."
)

session_namespace.add_model("Token", token_model)
session_namespace.add_model("Message", message_model)


@session_namespace.route("")
class SessionResource(Resource):

    @session_namespace.expect(login_parser)
    @session_namespace.response(200, "Success", token_model)
    @session_namespace.response(400, "Bad Request", message_model)
    @session_namespace.response(401, "Invalid credentials", message_model)
    @session_namespace.response(500, "Internal Server Error", message_model)
    def post(self):
        """
        Login as a user
        ---
        This will create a new session for a user and return the access and refresh tokens
        """
        data = login_parser.parse_args()
        user = UserORM.query.filter_by(username=data["username"], is_deleted=False).first()

        if user and user.check_password(data["password"]):
            access_token = create_access_token(identity=user, fresh=True)
            refresh_token = create_refresh_token(user)
            return (
                marshal(
                    {"access_token": access_token, "refresh_token": refresh_token},
                    token_model,
                ),
                200,
            )

        return marshal({"message": "Invalid credentials"}, message_model), 401
    
    @jwt_required(refresh=True)
    @session_namespace.doc(security="Bearer Auth")
    @session_namespace.response(200, "Success", token_model)
    @session_namespace.response(401, "Unauthorized", message_model)
    @session_namespace.response(500, "Internal Server Error", message_model)
    def get(self):
        """
        Refresh the access token
        ---
        !!! Refresh token required
        This will refresh the access token using the refresh token
        """
        new_token = create_access_token(identity=current_user, fresh=False)
        return marshal({"access_token": new_token}, token_model), 200
    
    @jwt_required(refresh=True)
    @session_namespace.doc(security="Bearer Auth")
    @session_namespace.response(200, "Success", token_model)
    @session_namespace.response(401, "Unauthorized", message_model)
    @session_namespace.response(500, "Internal Server Error", message_model)
    def delete(self):
        """
        Logout a user
        ---
        !!! Refresh token required
        This will blacklist the user's refresh token
        """
        jti = get_jwt()["jti"]
        token = TokenBlocklistORM(jti=jti)
        db.session.add(token)
        db.session.commit()
        return marshal({"message": "User logged out"}, message_model), 200
    
@session_namespace.route("/wechat")
class WechatSessionResource(Resource):
    @session_namespace.expect(wechat_login_parser)
    @session_namespace.response(200, "Success", token_model)
    @session_namespace.response(400, "Bad Request", message_model)
    @session_namespace.response(401, "Invalid credentials", message_model)
    @session_namespace.response(500, "Internal Server Error", message_model)
    def post(self):
        """
        Login as a user using WeChat
        ---
        ! If a user with the WeChat openid does not exist, a new user will be created
        ! If a user with the WeChat openid exists but is deleted, a 401 will be returned
        This will create a new session for a user and return the access and refresh tokens
        """
        data = wechat_login_parser.parse_args()
        code = data["code"]
        openid, session_key = get_wechat_login_info(code)
        user = UserORM.query.filter_by(wechat_openid=openid).first()
        if not user:
            username = f"微信用户{generate_random_string(8)}"
            while UserORM.query.filter_by(username=username).first():
                username = f"微信用户{generate_random_string(8)}"
            user = UserORM(username=username, wechat_openid=openid, wechat_session_key=session_key, permission_level=1)
            db.session.add(user)
            db.session.commit()

        if user.is_deleted:
            return marshal({"message": "Account has been deleted, please contact the administrator to restore the account"}, message_model), 401

        access_token = create_access_token(identity=user, fresh=True)
        refresh_token = create_refresh_token(user)
        return (
            marshal(
                {"access_token": access_token, "refresh_token": refresh_token},
                token_model,
            ),
            200,
        )

    @jwt_required(refresh=True)
    @session_namespace.doc(security="Bearer Auth")
    @session_namespace.response(200, "Success", token_model)
    @session_namespace.response(401, "Unauthorized", message_model)
    @session_namespace.response(500, "Internal Server Error", message_model)
    def get(self):
        """
        Refresh the access token using WeChat
        ---
        !!! Refresh token required
        This will refresh the access token using the refresh token
        """
        if current_user.wechat_openid is None:
            return marshal({"message": "User is not a WeChat user"}, message_model), 401
        
        if check_wechat_login_info(current_user.wechat_openid, current_user.wechat_session_key):
            new_token = create_access_token(identity=current_user, fresh=False)
            return marshal({"access_token": new_token}, token_model), 200
        else:
            return marshal({"message": "WeChat login info expired, please re-login"}, message_model), 401

    @jwt_required(refresh=True)
    @session_namespace.doc(security="Bearer Auth")
    @session_namespace.response(200, "Success", token_model)
    @session_namespace.response(401, "Unauthorized", message_model)
    @session_namespace.response(500, "Internal Server Error", message_model)
    def delete(self):
        """
        Logout a user using WeChat
        ---
        !!! Refresh token required
        This will blacklist the user's refresh token
        """
        jti = get_jwt()["jti"]
        token = TokenBlocklistORM(jti=jti)
        db.session.add(token)
        db.session.commit()
        return marshal({"message": "User logged out"}, message_model), 200