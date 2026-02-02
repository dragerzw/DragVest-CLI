from __future__ import annotations

from flask import Blueprint, jsonify
from decimal import Decimal

from app.service.security_service import SecurityService
from app.service.exceptions import NotFoundError


security_bp = Blueprint("security_bp", __name__)


def _security_to_dict(s) -> dict:
    return {
        "ticker": s.ticker,
        "name": s.name,
        "price": float(Decimal(str(s.price))),
    }


@security_bp.get("/")
def list_securities():
    svc = SecurityService()
    secs = svc.list_securities()
    return jsonify([_security_to_dict(s) for s in secs])


@security_bp.get("/<string:ticker>")
def get_security(ticker: str):
    svc = SecurityService()
    try:
        s = svc.get_security(ticker)
        return jsonify(_security_to_dict(s))
    except NotFoundError as ne:
        return {"error": str(ne)}, 404
