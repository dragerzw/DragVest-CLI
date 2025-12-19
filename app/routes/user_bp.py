from __future__ import annotations

from flask import Blueprint, jsonify, request
from decimal import Decimal

from app.database import sqldb as db
from app.models import User as ORMUser
from app.service.user_service import UserService
from app.service.exceptions import NotFoundError, ValidationError


user_bp = Blueprint("user_bp", __name__)


def _user_to_dict(u: ORMUser) -> dict:
    return {
        "id": u.id,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "username": u.username,
        "role": u.role,
        "balance": float(Decimal(str(u.balance))) if u.balance is not None else 0.0,
    }


@user_bp.get("/")
def list_users():
    svc = UserService()
    users = svc.list_users()
    return jsonify([_user_to_dict(u) for u in users])


@user_bp.get("/<int:user_id>")
def get_user_by_id(user_id: int):
    s = db.session
    u = s.query(ORMUser).filter_by(id=user_id).one_or_none()
    if not u:
        return {"error": "User not found"}, 404
    return jsonify(_user_to_dict(u))


@user_bp.post("/")
def create_user():
    data = request.get_json(silent=True) or {}
    try:
        svc = UserService()
        u = svc.create_user(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            balance=float(data.get("balance", 0.0)),
            role=data.get("role", "customer"),
        )
        return jsonify(_user_to_dict(u)), 201
    except ValidationError as ve:
        return {"error": str(ve)}, 400


@user_bp.delete("/<string:username>")
def delete_user(username: str):
    try:
        svc = UserService()
        svc.delete_user(username)
        return {"message": f"User '{username}' deleted"}, 200
    except NotFoundError as ne:
        return {"error": str(ne)}, 404
    except ValidationError as ve:
        return {"error": str(ve)}, 400
