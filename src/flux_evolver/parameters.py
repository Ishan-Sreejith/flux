from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Callable, List

from .models import Gene


@dataclass(frozen=True)
class Parameter:
    id: int
    name: str
    apply: Callable[[Any, Gene, "random.Random"], Any]


TOKENS = ["a", "b", "c", "x", "y", "z", "0", "1", "_", "-", " "]
NUM_CONSTS = [-8, -5, -3, -1, 1, 2, 3, 5, 8, 13]
FLOAT_CONSTS = [0.1, 0.25, 0.5, 0.75, 1.25, 1.5, 2.0]
SLICE_STARTS = [0, 1, 2, 3, -1, -2, -3]
SLICE_LENS = [1, 2, 3, 4, 5, 6]
ROUND_DIGITS = [0, 1, 2, 3]


PARAM_CATEGORIES = {
    "identity": "core",
    "to_int": "math",
    "to_float": "math",
    "to_str": "text",
    "safe_to_float": "math",
    "add_const": "math",
    "sub_const": "math",
    "mul_const": "math",
    "div_const": "math",
    "mod_const": "math",
    "pow_const": "math",
    "round": "math",
    "safe_round": "math",
    "clamp01": "math",
    "safe_clamp01": "math",
    "sin": "math",
    "cos": "math",
    "tan": "math",
    "abs": "math",
    "append": "text",
    "prepend": "text",
    "replace": "text",
    "slice": "text",
    "take": "text",
    "reverse": "text",
    "upper": "text",
    "lower": "text",
    "strip": "text",
    "length": "text",
    "safe_add_const": "math",
    "safe_mul_const": "math",
    "safe_div_const": "math",
    "list_add_const": "list",
    "list_mul_const": "list",
    "list_div_const": "list",
    "list_sum": "list",
    "list_mean": "list",
    "split_sum": "list",
    "project2": "list",
}


def _pick(seq: List[Any], seed: int) -> Any:
    return seq[seed % len(seq)]


def _coerce_number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "":
            raise ValueError("empty string")
        return float(stripped)
    raise ValueError("not numeric")


def _safe_number(value: Any) -> tuple[bool, float | None]:
    try:
        return True, _coerce_number(value)
    except Exception:
        return False, None


def _noise(gene: Gene, rng: "random.Random") -> float:
    return (rng.random() - 0.5) * 2.0 * gene.randomness


def _apply_add(value: Any, gene: Gene, rng: "random.Random", const: float) -> Any:
    num = _coerce_number(value)
    return num + const * (1.0 + gene.intensity * _noise(gene, rng))


def _apply_mul(value: Any, gene: Gene, rng: "random.Random", const: float) -> Any:
    num = _coerce_number(value)
    factor = const * (1.0 + gene.intensity * _noise(gene, rng))
    return num * factor


def _apply_div(value: Any, gene: Gene, rng: "random.Random", const: float) -> Any:
    num = _coerce_number(value)
    denom = const * (1.0 + gene.intensity * _noise(gene, rng))
    if abs(denom) < 1e-6:
        raise ValueError("division by zero")
    return num / denom


def _apply_mod(value: Any, gene: Gene, rng: "random.Random", const: float) -> Any:
    num = _coerce_number(value)
    mod_val = int(const)
    if mod_val == 0:
        raise ValueError("modulo by zero")
    return int(num) % mod_val


def _apply_pow(value: Any, gene: Gene, rng: "random.Random", const: float) -> Any:
    num = _coerce_number(value)
    exponent = const * (1.0 + gene.intensity * _noise(gene, rng))
    if abs(exponent) > 5:
        exponent = math.copysign(5, exponent)
    return math.pow(num, exponent)


def _apply_to_int(value: Any, gene: Gene, rng: "random.Random") -> Any:
    return int(_coerce_number(value))


def _apply_to_float(value: Any, gene: Gene, rng: "random.Random") -> Any:
    return float(_coerce_number(value))


def _apply_to_str(value: Any, gene: Gene, rng: "random.Random") -> Any:
    return str(value)


def _apply_append(value: Any, gene: Gene, rng: "random.Random", token: str) -> Any:
    return str(value) + token


def _apply_prepend(value: Any, gene: Gene, rng: "random.Random", token: str) -> Any:
    return token + str(value)


def _apply_replace(value: Any, gene: Gene, rng: "random.Random", token_a: str, token_b: str) -> Any:
    return str(value).replace(token_a, token_b)


def _apply_slice(value: Any, gene: Gene, rng: "random.Random", start: int, length: int) -> Any:
    if length <= 0:
        return [] if isinstance(value, (list, tuple)) else ""
    if isinstance(value, (list, tuple)):
        return list(value[start : start + length])
    text = str(value)
    return text[start : start + length]


def _apply_take(value: Any, gene: Gene, rng: "random.Random", length: int) -> Any:
    if isinstance(value, (list, tuple)):
        return list(value[:length])
    text = str(value)
    return text[:length]


def _apply_reverse(value: Any, gene: Gene, rng: "random.Random") -> Any:
    if isinstance(value, (list, tuple)):
        return list(value[::-1])
    return str(value)[::-1]


def _apply_upper(value: Any, gene: Gene, rng: "random.Random") -> Any:
    if isinstance(value, (list, tuple)):
        return [str(item).upper() for item in value]
    return str(value).upper()


def _apply_lower(value: Any, gene: Gene, rng: "random.Random") -> Any:
    if isinstance(value, (list, tuple)):
        return [str(item).lower() for item in value]
    return str(value).lower()


def _apply_strip(value: Any, gene: Gene, rng: "random.Random") -> Any:
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value]
    return str(value).strip()


def _apply_length(value: Any, gene: Gene, rng: "random.Random") -> Any:
    if isinstance(value, (list, tuple)):
        return len(value)
    return len(str(value))


def _apply_round(value: Any, gene: Gene, rng: "random.Random", digits: int) -> Any:
    num = _coerce_number(value)
    return round(num, digits)


def _apply_sin(value: Any, gene: Gene, rng: "random.Random") -> Any:
    num = _coerce_number(value)
    return math.sin(num)


def _apply_cos(value: Any, gene: Gene, rng: "random.Random") -> Any:
    num = _coerce_number(value)
    return math.cos(num)


def _apply_tan(value: Any, gene: Gene, rng: "random.Random") -> Any:
    num = _coerce_number(value)
    return math.tan(num)


def _apply_abs(value: Any, gene: Gene, rng: "random.Random") -> Any:
    num = _coerce_number(value)
    return abs(num)


def _apply_clamp01(value: Any, gene: Gene, rng: "random.Random") -> Any:
    num = _coerce_number(value)
    return max(0.0, min(1.0, num))


def _apply_safe_to_float(value: Any, gene: Gene, rng: "random.Random") -> Any:
    ok, num = _safe_number(value)
    if not ok or num is None:
        return value
    return float(num)


def _apply_safe_add(value: Any, gene: Gene, rng: "random.Random", const: float) -> Any:
    ok, num = _safe_number(value)
    if not ok or num is None:
        return value
    return num + const * (1.0 + gene.intensity * _noise(gene, rng))


def _apply_safe_mul(value: Any, gene: Gene, rng: "random.Random", const: float) -> Any:
    ok, num = _safe_number(value)
    if not ok or num is None:
        return value
    factor = const * (1.0 + gene.intensity * _noise(gene, rng))
    return num * factor


def _apply_safe_div(value: Any, gene: Gene, rng: "random.Random", const: float) -> Any:
    ok, num = _safe_number(value)
    if not ok or num is None:
        return value
    denom = const * (1.0 + gene.intensity * _noise(gene, rng))
    if abs(denom) < 1e-6:
        return value
    return num / denom


def _apply_safe_round(value: Any, gene: Gene, rng: "random.Random", digits: int) -> Any:
    ok, num = _safe_number(value)
    if not ok or num is None:
        return value
    return round(num, digits)


def _apply_safe_clamp01(value: Any, gene: Gene, rng: "random.Random") -> Any:
    ok, num = _safe_number(value)
    if not ok or num is None:
        return value
    return max(0.0, min(1.0, num))


def _apply_elementwise(value: Any, fn) -> Any:
    if isinstance(value, (list, tuple)):
        return [fn(item) for item in value]
    return fn(value)


def _apply_elementwise_add(value: Any, gene: Gene, rng: "random.Random", const: float) -> Any:
    def _op(item: Any) -> Any:
        ok, num = _safe_number(item)
        if not ok or num is None:
            return item
        return num + const * (1.0 + gene.intensity * _noise(gene, rng))

    return _apply_elementwise(value, _op)


def _apply_elementwise_mul(value: Any, gene: Gene, rng: "random.Random", const: float) -> Any:
    def _op(item: Any) -> Any:
        ok, num = _safe_number(item)
        if not ok or num is None:
            return item
        factor = const * (1.0 + gene.intensity * _noise(gene, rng))
        return num * factor

    return _apply_elementwise(value, _op)


def _apply_elementwise_div(value: Any, gene: Gene, rng: "random.Random", const: float) -> Any:
    def _op(item: Any) -> Any:
        ok, num = _safe_number(item)
        if not ok or num is None:
            return item
        denom = const * (1.0 + gene.intensity * _noise(gene, rng))
        if abs(denom) < 1e-6:
            return item
        return num / denom

    return _apply_elementwise(value, _op)


def _apply_list_sum(value: Any, gene: Gene, rng: "random.Random") -> Any:
    if not isinstance(value, (list, tuple)):
        return value
    total = 0.0
    for item in value:
        ok, num = _safe_number(item)
        if ok and num is not None:
            total += num
    return total


def _apply_list_mean(value: Any, gene: Gene, rng: "random.Random") -> Any:
    if not isinstance(value, (list, tuple)):
        return value
    nums = []
    for item in value:
        ok, num = _safe_number(item)
        if ok and num is not None:
            nums.append(num)
    if not nums:
        return value
    return sum(nums) / len(nums)


def _apply_split_sum(value: Any, gene: Gene, rng: "random.Random") -> Any:
    if not isinstance(value, (list, tuple)):
        return value
    if len(value) < 2:
        return list(value)
    mid = len(value) // 2
    left = _apply_list_sum(value[:mid], gene, rng)
    right = _apply_list_sum(value[mid:], gene, rng)
    return [left, right]


def _apply_project2(value: Any, gene: Gene, rng: "random.Random", seed: int) -> Any:
    if not isinstance(value, (list, tuple)):
        return value
    if not value:
        return [0.0, 0.0]
    local = random.Random(seed)
    weights_a = [local.uniform(-1.5, 1.5) for _ in range(len(value))]
    weights_b = [local.uniform(-1.5, 1.5) for _ in range(len(value))]
    acc_a = 0.0
    acc_b = 0.0
    for item, wa, wb in zip(value, weights_a, weights_b):
        ok, num = _safe_number(item)
        if not ok or num is None:
            continue
        acc_a += num * wa
        acc_b += num * wb
    return [acc_a, acc_b]


def build_parameter_library(size: int = 300) -> List[Parameter]:
    import random

    if size < 1 or size > 300:
        raise ValueError("size must be within 1..300")

    base_ops: List[Callable[[int], Parameter]] = []

    def add_param(name: str, func_factory: Callable[[int], Callable[[Any, Gene, random.Random], Any]]) -> None:
        def _builder(param_id: int) -> Parameter:
            return Parameter(param_id, name, func_factory(param_id))

        base_ops.append(_builder)

    add_param("identity", lambda _: (lambda value, gene, rng: value))
    add_param("to_int", lambda _: _apply_to_int)
    add_param("to_float", lambda _: _apply_to_float)
    add_param("to_str", lambda _: _apply_to_str)
    add_param("safe_to_float", lambda _: _apply_safe_to_float)
    add_param("sin", lambda _: _apply_sin)
    add_param("cos", lambda _: _apply_cos)
    add_param("tan", lambda _: _apply_tan)
    add_param("abs", lambda _: _apply_abs)

    add_param(
        "add_const",
        lambda pid: (lambda value, gene, rng, c=_pick(NUM_CONSTS, pid): _apply_add(value, gene, rng, c)),
    )
    add_param(
        "sub_const",
        lambda pid: (lambda value, gene, rng, c=_pick(NUM_CONSTS, pid): _apply_add(value, gene, rng, -c)),
    )
    add_param(
        "mul_const",
        lambda pid: (lambda value, gene, rng, c=_pick(FLOAT_CONSTS, pid): _apply_mul(value, gene, rng, c)),
    )
    add_param(
        "div_const",
        lambda pid: (lambda value, gene, rng, c=_pick(FLOAT_CONSTS, pid): _apply_div(value, gene, rng, c)),
    )
    add_param(
        "safe_add_const",
        lambda pid: (lambda value, gene, rng, c=_pick(NUM_CONSTS, pid): _apply_safe_add(value, gene, rng, c)),
    )
    add_param(
        "safe_mul_const",
        lambda pid: (lambda value, gene, rng, c=_pick(FLOAT_CONSTS, pid): _apply_safe_mul(value, gene, rng, c)),
    )
    add_param(
        "safe_div_const",
        lambda pid: (lambda value, gene, rng, c=_pick(FLOAT_CONSTS, pid): _apply_safe_div(value, gene, rng, c)),
    )
    add_param(
        "mod_const",
        lambda pid: (lambda value, gene, rng, c=_pick(NUM_CONSTS, pid): _apply_mod(value, gene, rng, c)),
    )
    add_param(
        "pow_const",
        lambda pid: (lambda value, gene, rng, c=_pick(FLOAT_CONSTS, pid): _apply_pow(value, gene, rng, c)),
    )
    add_param("round", lambda pid: (lambda value, gene, rng, d=_pick(ROUND_DIGITS, pid): _apply_round(value, gene, rng, d)))
    add_param(
        "safe_round",
        lambda pid: (lambda value, gene, rng, d=_pick(ROUND_DIGITS, pid): _apply_safe_round(value, gene, rng, d)),
    )
    add_param("clamp01", lambda _: _apply_clamp01)
    add_param("safe_clamp01", lambda _: _apply_safe_clamp01)
    add_param(
        "list_add_const",
        lambda pid: (lambda value, gene, rng, c=_pick(NUM_CONSTS, pid): _apply_elementwise_add(value, gene, rng, c)),
    )
    add_param(
        "list_mul_const",
        lambda pid: (lambda value, gene, rng, c=_pick(FLOAT_CONSTS, pid): _apply_elementwise_mul(value, gene, rng, c)),
    )
    add_param(
        "list_div_const",
        lambda pid: (lambda value, gene, rng, c=_pick(FLOAT_CONSTS, pid): _apply_elementwise_div(value, gene, rng, c)),
    )
    add_param("list_sum", lambda _: _apply_list_sum)
    add_param("list_mean", lambda _: _apply_list_mean)
    add_param("split_sum", lambda _: _apply_split_sum)
    add_param("project2", lambda pid: (lambda value, gene, rng, s=pid: _apply_project2(value, gene, rng, s)))
    add_param(
        "append",
        lambda pid: (lambda value, gene, rng, t=_pick(TOKENS, pid): _apply_append(value, gene, rng, t)),
    )
    add_param(
        "prepend",
        lambda pid: (lambda value, gene, rng, t=_pick(TOKENS, pid): _apply_prepend(value, gene, rng, t)),
    )
    add_param(
        "replace",
        lambda pid: (
            lambda value, gene, rng, a=_pick(TOKENS, pid), b=_pick(TOKENS, pid + 3): _apply_replace(value, gene, rng, a, b)
        ),
    )
    add_param(
        "slice",
        lambda pid: (
            lambda value, gene, rng, s=_pick(SLICE_STARTS, pid), l=_pick(SLICE_LENS, pid): _apply_slice(value, gene, rng, s, l)
        ),
    )
    add_param(
        "take",
        lambda pid: (lambda value, gene, rng, l=_pick(SLICE_LENS, pid): _apply_take(value, gene, rng, l)),
    )
    add_param("reverse", lambda _: _apply_reverse)
    add_param("upper", lambda _: _apply_upper)
    add_param("lower", lambda _: _apply_lower)
    add_param("strip", lambda _: _apply_strip)
    add_param("length", lambda _: _apply_length)

    params: List[Parameter] = []
    op_count = len(base_ops)
    for idx in range(1, size + 1):
        op_builder = base_ops[(idx - 1) % op_count]
        param = op_builder(idx)
        params.append(param)

    return params


def parameter_by_id(params: List[Parameter], param_id: int) -> Parameter:
    if param_id < 1 or param_id > len(params):
        raise ValueError("param_id out of range")
    return params[param_id - 1]


def filter_param_ids(params: List[Parameter], mode: str) -> List[int]:
    if mode == "all":
        return [p.id for p in params]
    allowed = []
    for param in params:
        category = PARAM_CATEGORIES.get(param.name, "core")
        if mode == "math" and category in ("math", "core", "list"):
            allowed.append(param.id)
        elif mode == "text" and category in ("text", "core"):
            allowed.append(param.id)
        elif mode == "list" and category in ("list", "math", "core"):
            allowed.append(param.id)
    if not allowed:
        allowed = [p.id for p in params]
    return allowed
