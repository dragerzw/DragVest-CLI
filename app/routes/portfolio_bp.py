from __future__ import annotations

from flask import Blueprint, jsonify, request
from decimal import Decimal
from sqlalchemy.orm import selectinload

from app.database import sqldb as db
from app.models import Portfolio as ORMPortfolio, Investment as ORMInvestment
from app.service.portfolio_service import PortfolioService
from app.service.security_service import SecurityService
from app.service.exceptions import NotFoundError, ValidationError


portfolio_bp = Blueprint("portfolio_bp", __name__)


def _investment_to_dict(inv: ORMInvestment) -> dict:
    return {
        "id": inv.id,
        "ticker": inv.ticker,
        "quantity": inv.quantity,
        "purchase_price": float(Decimal(str(inv.purchase_price))),
        "portfolio_id": inv.portfolio_id,
    }


def _portfolio_to_dict(p: ORMPortfolio) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "owner_username": p.owner_username,
        "investments": [_investment_to_dict(i) for i in (p.investments or [])],
    }


@portfolio_bp.get("/")
def list_portfolios():
    owner = request.args.get("owner")
    if owner:
        svc = PortfolioService()
        try:
            ports = svc.get_portfolios_by_username(owner)
        except NotFoundError:
            return jsonify([])
        return jsonify([_portfolio_to_dict(p) for p in ports])
    # list all portfolios (admin-style) if owner not specified
    s = db.session
    ports = (
        s.query(ORMPortfolio)
        .options(selectinload(ORMPortfolio.investments))
        .all()
    )
    return jsonify([_portfolio_to_dict(p) for p in ports])


@portfolio_bp.get("/<int:portfolio_id>")
def get_portfolio(portfolio_id: int):
    s = db.session
    p = (
        s.query(ORMPortfolio)
        .options(selectinload(ORMPortfolio.investments))
        .filter_by(id=portfolio_id)
        .one_or_none()
    )
    if not p:
        return {"error": "Portfolio not found"}, 404
    return jsonify(_portfolio_to_dict(p))


@portfolio_bp.post("/")
def create_portfolio():
    data = request.get_json(silent=True) or {}
    owner = data.get("owner") or data.get("owner_username")
    name = data.get("name")
    description = data.get("description", "")
    try:
        svc = PortfolioService()
        p = svc.create_portfolio(owner, name, description)
        return jsonify(_portfolio_to_dict(p)), 201
    except (ValidationError, NotFoundError) as e:
        return {"error": str(e)}, 400


@portfolio_bp.delete("/<int:portfolio_id>")
def delete_portfolio(portfolio_id: int):
    owner = request.args.get("owner")
    if not owner:
        return {"error": "owner is required as query parameter"}, 400
    try:
        svc = PortfolioService()
        svc.delete_portfolio(owner, portfolio_id)
        return {"message": f"Portfolio {portfolio_id} deleted"}, 200
    except NotFoundError as ne:
        return {"error": str(ne)}, 404
    except ValidationError as ve:
        return {"error": str(ve)}, 400


@portfolio_bp.post("/<int:portfolio_id>/buy")
def buy_security(portfolio_id: int):
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    ticker = data.get("ticker")
    amount = float(data.get("amount", 0.0))
    try:
        from app.service.security_service import SecurityService

        svc = SecurityService()
        svc.buy_security(username, ticker, amount, portfolio_id)
        return {"message": f"Bought ${amount:.2f} of {ticker} in portfolio {portfolio_id}"}, 201
    except (ValidationError, NotFoundError, PermissionError, ValueError) as e:
        return {"error": str(e)}, 400


@portfolio_bp.post("/<int:portfolio_id>/harvest")
def harvest_investment(portfolio_id: int):
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    ticker = data.get("ticker")
    quantity = int(data.get("quantity", 0))
    if not username or not ticker or quantity <= 0:
        return {"error": "username, ticker, and positive quantity are required"}, 400
    try:
        sec_svc = SecurityService()
        sec = sec_svc.get_security(ticker)
        sale_price = Decimal(str(sec.price))
        svc = PortfolioService()
        proceeds = svc.harvest_investment(username, portfolio_id, ticker, quantity, float(sale_price))
        return {
            "message": f"Harvested {quantity} of {ticker}",
            "proceeds": float(Decimal(str(proceeds))),
        }, 200
    except (ValidationError, NotFoundError) as e:
        return {"error": str(e)}, 400
