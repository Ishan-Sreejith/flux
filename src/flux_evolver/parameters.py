from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, List

from .models import Gene


@dataclass(frozen=True)
class Parameter:
    id: int
    name: str
    apply: Callable[[Any, Gene], Any]
    domain: str


NUM_CONSTS = [-10, -5, -2, -1, 1, 2, 5, 10]
TOKENS = ["a", "b", "c", "x", "y", "z", "_", "-", "0", "1"]


def _coerce_number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, str):
        return float(value.strip())
    raise ValueError("not numeric")


def _apply_elementwise(value: Any, fn: Callable[[Any], Any]) -> Any:
    if isinstance(value, list):
        return [fn(item) for item in value]
    return fn(value)


def _apply_add(value: Any, gene: Gene, const: float) -> Any:
    def op(item: Any) -> Any:
        num = _coerce_number(item)
        return num + const * (1.0 + gene.strength)

    return _apply_elementwise(value, op)


def _apply_sub(value: Any, gene: Gene, const: float) -> Any:
    return _apply_add(value, gene, -const)


def _apply_mul(value: Any, gene: Gene, const: float) -> Any:
    def op(item: Any) -> Any:
        num = _coerce_number(item)
        return num * (const * (1.0 + gene.strength))

    return _apply_elementwise(value, op)


def _apply_div(value: Any, gene: Gene, const: float) -> Any:
    def op(item: Any) -> Any:
        num = _coerce_number(item)
        denom = const * (1.0 + gene.strength)
        if abs(denom) < 1e-8:
            return num
        return num / denom

    return _apply_elementwise(value, op)


def _apply_mod(value: Any, gene: Gene, const: float) -> Any:
    def op(item: Any) -> Any:
        num = _coerce_number(item)
        mod = int(const) if int(const) != 0 else 1
        return int(num) % mod

    return _apply_elementwise(value, op)


def _apply_pow(value: Any, gene: Gene, const: float) -> Any:
    def op(item: Any) -> Any:
        num = _coerce_number(item)
        exponent = max(-3, min(3, const * (1.0 + gene.strength)))
        return math.pow(num, exponent)

    return _apply_elementwise(value, op)


def _apply_sin(value: Any, gene: Gene) -> Any:
    return _apply_elementwise(value, lambda x: math.sin(_coerce_number(x)))


def _apply_cos(value: Any, gene: Gene) -> Any:
    return _apply_elementwise(value, lambda x: math.cos(_coerce_number(x)))


def _apply_tan(value: Any, gene: Gene) -> Any:
    return _apply_elementwise(value, lambda x: math.tan(_coerce_number(x)))


def _apply_abs(value: Any, gene: Gene) -> Any:
    return _apply_elementwise(value, lambda x: abs(_coerce_number(x)))


def _apply_round(value: Any, gene: Gene, digits: int) -> Any:
    return _apply_elementwise(value, lambda x: round(_coerce_number(x), digits))


def _apply_clamp(value: Any, gene: Gene) -> Any:
    return _apply_elementwise(value, lambda x: max(0.0, min(1.0, _coerce_number(x))))


def _apply_to_str(value: Any, gene: Gene) -> Any:
    return str(value)


def _apply_lower(value: Any, gene: Gene) -> Any:
    return str(value).lower()


def _apply_upper(value: Any, gene: Gene) -> Any:
    return str(value).upper()


def _apply_strip(value: Any, gene: Gene) -> Any:
    return str(value).strip()


def _apply_reverse(value: Any, gene: Gene) -> Any:
    return str(value)[::-1]


def _apply_first_letter(value: Any, gene: Gene) -> Any:
    text = str(value)
    return text[0] if text else ""


def _apply_last_letter(value: Any, gene: Gene) -> Any:
    text = str(value)
    return text[-1] if text else ""


def _apply_append(value: Any, gene: Gene, token: str) -> Any:
    return str(value) + token


def _apply_prepend(value: Any, gene: Gene, token: str) -> Any:
    return token + str(value)


def _apply_replace(value: Any, gene: Gene, token: str) -> Any:
    return str(value).replace(token, "")


def _apply_capitalize(value: Any, gene: Gene) -> Any:
    return str(value).capitalize()


def _apply_swapcase(value: Any, gene: Gene) -> Any:
    return str(value).swapcase()


def _apply_concat(value: Any, gene: Gene, token: str) -> Any:
    return f"{value}{token}"


def _apply_if_gt_add(value: Any, gene: Gene, threshold: float, const: float) -> Any:
    num = _coerce_number(value)
    if num > threshold:
        return num + const * (1.0 + gene.strength)
    return num


def _apply_if_lt_sub(value: Any, gene: Gene, threshold: float, const: float) -> Any:
    num = _coerce_number(value)
    if num < threshold:
        return num - const * (1.0 + gene.strength)
    return num


def _apply_if_contains(value: Any, gene: Gene, token: str) -> Any:
    text = str(value)
    if token in text:
        return text + token
    return text


def _build_numeric_templates() -> List[Callable[[int], Parameter]]:
    templates: List[Callable[[int], Parameter]] = []

    def add_param(name: str, builder: Callable[[int], Callable[[Any, Gene], Any]]) -> None:
        def _build(pid: int) -> Parameter:
            return Parameter(pid, name, builder(pid), "numeric")

        templates.append(_build)

    add_param("identity", lambda _: (lambda v, g: v))
    add_param("add_const", lambda pid: (lambda v, g, c=NUM_CONSTS[pid % len(NUM_CONSTS)]: _apply_add(v, g, c)))
    add_param("sub_const", lambda pid: (lambda v, g, c=NUM_CONSTS[pid % len(NUM_CONSTS)]: _apply_sub(v, g, c)))
    add_param("mul_const", lambda pid: (lambda v, g, c=NUM_CONSTS[pid % len(NUM_CONSTS)]: _apply_mul(v, g, c)))
    add_param("div_const", lambda pid: (lambda v, g, c=NUM_CONSTS[pid % len(NUM_CONSTS)]: _apply_div(v, g, c)))
    add_param("mod_const", lambda pid: (lambda v, g, c=NUM_CONSTS[pid % len(NUM_CONSTS)]: _apply_mod(v, g, c)))
    add_param("pow_const", lambda pid: (lambda v, g, c=NUM_CONSTS[pid % len(NUM_CONSTS)]: _apply_pow(v, g, c)))
    add_param("sin", lambda _: _apply_sin)
    add_param("cos", lambda _: _apply_cos)
    add_param("tan", lambda _: _apply_tan)
    add_param("abs", lambda _: _apply_abs)
    add_param("round", lambda pid: (lambda v, g, d=pid % 3: _apply_round(v, g, d)))
    add_param("clamp", lambda _: _apply_clamp)
    add_param(
        "if_gt_add",
        lambda pid: (
            lambda v, g, t=NUM_CONSTS[pid % len(NUM_CONSTS)], c=NUM_CONSTS[(pid + 2) % len(NUM_CONSTS)]: _apply_if_gt_add(
                v, g, t, c
            )
        ),
    )
    add_param(
        "if_lt_sub",
        lambda pid: (
            lambda v, g, t=NUM_CONSTS[pid % len(NUM_CONSTS)], c=NUM_CONSTS[(pid + 3) % len(NUM_CONSTS)]: _apply_if_lt_sub(
                v, g, t, c
            )
        ),
    )
    return templates


def _build_text_templates() -> List[Callable[[int], Parameter]]:
    templates: List[Callable[[int], Parameter]] = []

    def add_param(name: str, builder: Callable[[int], Callable[[Any, Gene], Any]]) -> None:
        def _build(pid: int) -> Parameter:
            return Parameter(pid, name, builder(pid), "text")

        templates.append(_build)

    add_param("identity", lambda _: (lambda v, g: v))
    add_param("to_str", lambda _: _apply_to_str)
    add_param("lower", lambda _: _apply_lower)
    add_param("upper", lambda _: _apply_upper)
    add_param("capitalize", lambda _: _apply_capitalize)
    add_param("swapcase", lambda _: _apply_swapcase)
    add_param("strip", lambda _: _apply_strip)
    add_param("reverse", lambda _: _apply_reverse)
    add_param("first_letter", lambda _: _apply_first_letter)
    add_param("last_letter", lambda _: _apply_last_letter)
    add_param("concat", lambda pid: (lambda v, g, t=TOKENS[pid % len(TOKENS)]: _apply_concat(v, g, t)))
    add_param("append", lambda pid: (lambda v, g, t=TOKENS[pid % len(TOKENS)]: _apply_append(v, g, t)))
    add_param("prepend", lambda pid: (lambda v, g, t=TOKENS[pid % len(TOKENS)]: _apply_prepend(v, g, t)))
    add_param("replace", lambda pid: (lambda v, g, t=TOKENS[pid % len(TOKENS)]: _apply_replace(v, g, t)))
    add_param(
        "if_contains",
        lambda pid: (lambda v, g, t=TOKENS[pid % len(TOKENS)]: _apply_if_contains(v, g, t)),
    )
    return templates


def build_parameter_library(size: int = 1000, domain: str = "numeric") -> List[Parameter]:
    if size < 1:
        raise ValueError("size must be positive")
    templates = _build_numeric_templates() if domain == "numeric" else _build_text_templates()
    params: List[Parameter] = []
    for idx in range(1, size + 1):
        builder = templates[(idx - 1) % len(templates)]
        params.append(builder(idx))
    return params


def build_parameter_pools(numeric_count: int, text_count: int) -> tuple[List[Parameter], List[Parameter]]:
    return build_parameter_library(numeric_count, "numeric"), build_parameter_library(text_count, "text")


def parameter_by_id(params: List[Parameter], param_id: int) -> Parameter:
    if param_id < 1 or param_id > len(params):
        raise ValueError("param_id out of range")
    return params[param_id - 1]
