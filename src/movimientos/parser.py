from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pdfplumber
from dateutil import parser as date_parser

from .models import Transaction

# Detectores por proveedor
PROVIDER_KEYWORDS = {
    "macro": ["banco macro", "macro"],
    "brubank": ["brubank"],
    "mercadopago": ["mercado pago", "mercadopago"],
}


class UnsupportedProviderError(Exception):
    """No se reconoció el origen del PDF."""


class EmptyStatementError(Exception):
    """No se encontraron movimientos en el PDF."""


def read_pdf_text(pdf_path: Path) -> str:
    pages_text: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages_text.append(page.extract_text() or "")
    return "\n".join(pages_text)


def detect_provider(text: str) -> str:
    lower_text = text.lower()
    for provider, keywords in PROVIDER_KEYWORDS.items():
        if any(keyword in lower_text for keyword in keywords):
            return provider
    raise UnsupportedProviderError("No se pudo detectar el banco/billetera a partir del PDF")


def parse_amount(value: str) -> float:
    cleaned = value.replace(".", "").replace(" ", "").replace("$", "").replace("ARS", "").strip()
    cleaned = cleaned.replace(",", ".")
    return float(cleaned)


def parse_date(value: str) -> datetime.date:
    return date_parser.parse(value, dayfirst=True).date()


def parse_line_with_amount(line: str, provider: str, currency: str = "ARS", source_file: str = "") -> Transaction | None:
    pattern = re.compile(
        r"(?P<date>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(?P<description>.+?)\s+(?P<amount>[+-]?\d+[\d.,]*)\s*(?P<balance>[+-]?\d+[\d.,]*)?",
        re.IGNORECASE,
    )
    match = pattern.search(line)
    if not match:
        return None

    date_value = parse_date(match.group("date"))
    description = " ".join(match.group("description").split())
    amount = parse_amount(match.group("amount"))
    balance_raw = match.group("balance")
    balance = parse_amount(balance_raw) if balance_raw else None

    return Transaction(
        provider=provider,
        date=date_value,
        description=description,
        amount=amount,
        balance=balance,
        currency=currency,
        raw_reference=line.strip(),
        source_file=source_file,
    )


def parse_macro(text: str, pdf_path: Path) -> list[Transaction]:
    lines = [line for line in text.splitlines() if line.strip()]
    transactions: list[Transaction] = []
    for line in lines:
        tx = parse_line_with_amount(line, provider="macro", source_file=pdf_path.name)
        if tx:
            transactions.append(tx)
    return transactions


def parse_brubank(text: str, pdf_path: Path) -> list[Transaction]:
    lines = [line for line in text.splitlines() if line.strip()]
    transactions: list[Transaction] = []
    for line in lines:
        tx = parse_line_with_amount(line, provider="brubank", source_file=pdf_path.name)
        if tx:
            transactions.append(tx)
    return transactions


def parse_mercadopago(text: str, pdf_path: Path) -> list[Transaction]:
    lines = [line for line in text.splitlines() if line.strip()]
    transactions: list[Transaction] = []
    pattern = re.compile(
        r"(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\s+-?\s*(?P<description>.+?)\s+(?P<amount>[+-]?\$?\d+[\d.,]*)",
        re.IGNORECASE,
    )
    for line in lines:
        match = pattern.search(line)
        if not match:
            continue
        date_value = parse_date(match.group("date"))
        description = " ".join(match.group("description").split())
        amount = parse_amount(match.group("amount"))
        transactions.append(
            Transaction(
                provider="mercadopago",
                date=date_value,
                description=description,
                amount=amount,
                balance=None,
                currency="ARS",
                raw_reference=line.strip(),
                source_file=pdf_path.name,
            )
        )
    return transactions


PARSERS = {
    "macro": parse_macro,
    "brubank": parse_brubank,
    "mercadopago": parse_mercadopago,
}


def parse_pdf(pdf_path: Path) -> list[Transaction]:
    text = read_pdf_text(pdf_path)
    provider = detect_provider(text)
    parser_fn = PARSERS.get(provider)
    if not parser_fn:
        raise UnsupportedProviderError(f"No hay un parser configurado para {provider}")
    transactions = parser_fn(text, pdf_path)
    if not transactions:
        raise EmptyStatementError("No se extrajeron movimientos; revisa el formato del PDF")
    return transactions


def parse_many(pdf_paths: Iterable[Path]) -> list[Transaction]:
    results: list[Transaction] = []
    for pdf_path in pdf_paths:
        results.extend(parse_pdf(pdf_path))
    return results
