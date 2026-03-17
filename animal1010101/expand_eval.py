from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    base = Path(__file__).resolve().parent
    path = base / "eval_questions.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    def add(q: str, expect_any: list[str], prime: str) -> None:
        data.append({"question": q, "expect_any": expect_any, "expect_prime": prime})

    animals = [
        "lion",
        "tiger",
        "wolf",
        "bear",
        "fox",
        "deer",
        "horse",
        "cow",
        "sheep",
        "goat",
        "zebra",
        "rhino",
        "hippo",
        "kangaroo",
        "panda",
        "otter",
        "camel",
        "moose",
        "bison",
        "chimpanzee",
        "gorilla",
        "monkey",
        "dolphin",
        "shark",
        "eagle",
        "owl",
        "falcon",
        "penguin",
        "snake",
        "lizard",
        "frog",
        "toad",
        "whale",
        "seal",
        "rabbit",
        "rat",
        "mouse",
        "giraffe",
        "elephant",
    ]

    for a in animals:
        add(f"Explain {a}", ["animal"], "Animal")
        add(f"What is a {a}?", ["animal"], "Animal")
        add(f"Describe the {a}", ["animal"], "Animal")

    foods = [
        "apple",
        "banana",
        "orange",
        "grape",
        "mango",
        "strawberry",
        "pear",
        "peach",
        "bread",
        "rice",
        "pasta",
        "cheese",
        "milk",
        "egg",
        "chicken",
        "beef",
        "fish",
        "carrot",
        "potato",
        "tomato",
    ]

    for f in foods:
        add(f"Explain {f}", ["edible"], "Food")
        add(f"What is {f}?", ["edible"], "Food")
        add(f"Describe {f}", ["edible"], "Food")

    tools = [
        "hammer",
        "screwdriver",
        "wrench",
        "saw",
        "knife",
        "scissors",
        "computer",
        "phone",
        "car",
        "engine",
        "robot",
        "microscope",
        "telescope",
        "drill",
        "camera",
    ]

    for t in tools:
        add(f"Explain {t}", ["tool", "artificial"], "Object")
        add(f"What is a {t}?", ["tool", "artificial"], "Object")
        add(f"Describe {t}", ["tool", "artificial"], "Object")

    feelings = ["fear", "joy", "anger", "sadness", "peace", "surprise", "anxiety", "calm", "pride", "shame"]
    for f in feelings:
        expect = ["negative"] if f in {"fear", "anger", "sadness", "anxiety", "shame"} else ["friendly"]
        add(f"Explain {f}", expect, "Feeling")
        add(f"What is {f}?", expect, "Feeling")

    actions = ["run", "fight", "attack", "hug", "help", "build", "learn", "teach", "travel", "cook"]
    for a in actions:
        expect = ["friendly"] if a in {"hug", "help", "teach"} else []
        add(f"Explain {a}", expect, "Action")
        add(f"What is {a}?", expect, "Action")


    for q in data:
        q["expect_any"] = [x for x in q.get("expect_any", []) if x]

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
