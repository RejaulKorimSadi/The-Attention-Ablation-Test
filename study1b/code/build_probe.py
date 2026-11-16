"""Builds the context-conflict probe (v2): 111 facts x 9 conditions.

Conditions per fact
  baseline                 question only, no context (prior answer)
  conflict_{short,long}_{early,middle,late}
                           false version of the fact planted among filler
                           statements (short = 9 lines, long = 31 lines)
  support_{short,long}_middle
                           true version of the fact planted in the middle
                           (control: can the model read the planted line?)
"""
import json
import re
import unicodedata

# (category, subject, question, statement template, true answer, wrong answer)
CAPITALS = [
    ("France", "Paris", "Lyon"), ("Japan", "Tokyo", "Osaka"), ("Italy", "Rome", "Milan"),
    ("Egypt", "Cairo", "Alexandria"), ("Canada", "Ottawa", "Toronto"),
    ("Australia", "Canberra", "Sydney"), ("Turkey", "Ankara", "Istanbul"),
    ("Brazil", "Brasilia", "Rio de Janeiro"), ("Germany", "Berlin", "Munich"),
    ("Russia", "Moscow", "Saint Petersburg"), ("China", "Beijing", "Shanghai"),
    ("Pakistan", "Islamabad", "Karachi"), ("Nigeria", "Abuja", "Lagos"),
    ("Switzerland", "Bern", "Zurich"), ("Morocco", "Rabat", "Casablanca"),
    ("Vietnam", "Hanoi", "Da Nang"), ("New Zealand", "Wellington", "Auckland"),
    ("Kenya", "Nairobi", "Mombasa"), ("Argentina", "Buenos Aires", "Cordoba"),
    ("Peru", "Lima", "Cusco"), ("Norway", "Oslo", "Bergen"), ("Sweden", "Stockholm", "Gothenburg"),
    ("Poland", "Warsaw", "Krakow"), ("Greece", "Athens", "Thessaloniki"),
    ("Portugal", "Lisbon", "Porto"), ("Thailand", "Bangkok", "Chiang Mai"),
    ("Philippines", "Manila", "Cebu"), ("South Korea", "Seoul", "Busan"),
    ("Iran", "Tehran", "Isfahan"), ("Iraq", "Baghdad", "Basra"),
    ("Saudi Arabia", "Riyadh", "Jeddah"), ("Bangladesh", "Dhaka", "Chittagong"),
    ("Ethiopia", "Addis Ababa", "Gondar"), ("Ghana", "Accra", "Kumasi"),
    ("Chile", "Santiago", "Valparaiso"), ("Colombia", "Bogota", "Medellin"),
    ("Burkina Faso", "Ouagadougou", "Bobo-Dioulasso"), ("Mongolia", "Ulaanbaatar", "Erdenet"),
    ("Bhutan", "Thimphu", "Paro"), ("Laos", "Vientiane", "Luang Prabang"),
    ("Uruguay", "Montevideo", "Salto"), ("Kyrgyzstan", "Bishkek", "Osh"),
    ("Tajikistan", "Dushanbe", "Khujand"), ("Malawi", "Lilongwe", "Blantyre"),
    ("Zambia", "Lusaka", "Ndola"), ("Ecuador", "Quito", "Guayaquil"),
    ("Nepal", "Kathmandu", "Pokhara"), ("Afghanistan", "Kabul", "Kandahar"),
    ("Cuba", "Havana", "Holguin"), ("Jamaica", "Kingston", "Montego Bay"),
    ("Finland", "Helsinki", "Tampere"), ("Denmark", "Copenhagen", "Aarhus"),
    ("Austria", "Vienna", "Salzburg"), ("Hungary", "Budapest", "Debrecen"),
    ("the Czech Republic", "Prague", "Brno"), ("Ireland", "Dublin", "Cork"),
]
SYMBOLS = [
    ("gold", "Au", "Go"), ("iron", "Fe", "Ir"), ("sodium", "Na", "So"), ("silver", "Ag", "Si"),
    ("lead", "Pb", "Le"), ("copper", "Cu", "Co"), ("mercury", "Hg", "Me"), ("tin", "Sn", "Ti"),
    ("calcium", "Ca", "Cl"), ("zinc", "Zn", "Zi"), ("magnesium", "Mg", "Ma"), ("platinum", "Pt", "Pl"),
]
CURRENCIES = [
    ("Japan", "Yen", "Won"), ("India", "Rupee", "Taka"), ("the United States", "Dollar", "Peso"),
    ("the United Kingdom", "Pound", "Euro"), ("Mexico", "Peso", "Real"), ("Thailand", "Baht", "Ringgit"),
    ("Switzerland", "Franc", "Euro"), ("South Korea", "Won", "Yen"), ("Brazil", "Real", "Peso"),
    ("Vietnam", "Dong", "Baht"), ("Turkey", "Lira", "Dinar"), ("Poland", "Zloty", "Koruna"),
    ("Sweden", "Krona", "Euro"), ("Israel", "Shekel", "Dinar"), ("Nigeria", "Naira", "Cedi"),
    ("Indonesia", "Rupiah", "Ringgit"),
]
BOOKS = [
    ("Pride and Prejudice", "Austen", "Bronte"), ("Nineteen Eighty-Four", "Orwell", "Huxley"),
    ("Hamlet", "Shakespeare", "Marlowe"), ("War and Peace", "Tolstoy", "Dostoevsky"),
    ("Moby-Dick", "Melville", "Hawthorne"), ("The Odyssey", "Homer", "Virgil"),
    ("Don Quixote", "Cervantes", "Lorca"), ("On the Origin of Species", "Darwin", "Lamarck"),
    ("Frankenstein", "Shelley", "Byron"), ("Dracula", "Stoker", "Poe"),
    ("The Divine Comedy", "Dante", "Petrarch"), ("Faust", "Goethe", "Schiller"),
    ("Les Miserables", "Hugo", "Dumas"), ("One Hundred Years of Solitude", "Marquez", "Borges"),
    ("Gitanjali", "Tagore", "Nazrul"),
]
PAINTINGS = [
    ("the Mona Lisa", "Vinci", "Raphael"), ("The Starry Night", "Gogh", "Monet"),
    ("The Scream", "Munch", "Klimt"), ("Guernica", "Picasso", "Dali"),
    ("the ceiling of the Sistine Chapel", "Michelangelo", "Raphael"),
    ("The Persistence of Memory", "Dali", "Magritte"),
    ("Girl with a Pearl Earring", "Vermeer", "Rembrandt"), ("The Night Watch", "Rembrandt", "Vermeer"),
    ("Water Lilies", "Monet", "Renoir"),
]
PLANETS = [
    ("which planet is the largest in the solar system?", "The largest planet in the solar system is {}.", "Jupiter", "Saturn"),
    ("which planet is closest to the Sun?", "The planet closest to the Sun is {}.", "Mercury", "Venus"),
    ("which planet is known as the Red Planet?", "The planet known as the Red Planet is {}.", "Mars", "Venus"),
]

FACTS = []
for c, t, w in CAPITALS:
    FACTS.append(dict(category="capital", subject=f"the capital of {c}",
                      question=f"what is the capital of {c}?",
                      statement=f"The capital of {c} is {{}}.", true=t, wrong=w))
for e, t, w in SYMBOLS:
    FACTS.append(dict(category="symbol", subject=f"the chemical symbol of {e}",
                      question=f"what is the chemical symbol of {e}?",
                      statement=f"The chemical symbol of {e} is {{}}.", true=t, wrong=w))
for c, t, w in CURRENCIES:
    FACTS.append(dict(category="currency", subject=f"the currency of {c}",
                      question=f"what is the currency of {c}?",
                      statement=f"The currency of {c} is the {{}}.", true=t, wrong=w))
for b, t, w in BOOKS:
    FACTS.append(dict(category="author", subject=f"the author of {b}",
                      question=f"who wrote {b}?",
                      statement=f"{b} was written by {{}}.", true=t, wrong=w))
for p, t, w in PAINTINGS:
    FACTS.append(dict(category="painter", subject=f"the painter of {p}",
                      question=f"who painted {p}?",
                      statement=f"{p[0].upper() + p[1:]} was painted by {{}}.", true=t, wrong=w))
for q, st, t, w in PLANETS:
    FACTS.append(dict(category="planet", subject=q, question=q, statement=st, true=t, wrong=w))

FILLER = [
    "The sky appears blue during a clear day.", "Water freezes at zero degrees Celsius.",
    "A triangle has three sides.", "The sun rises in the east.", "Honey is produced by bees.",
    "A week has seven days.", "Ice is the solid form of water.", "A year has twelve months.",
    "Spiders have eight legs.", "A square has four equal sides.", "Most plants need sunlight to grow.",
    "Fish breathe through gills.", "A day has twenty-four hours.", "Snow is made of ice crystals.",
    "Cows produce milk.", "A circle has no corners.", "Birds lay eggs.", "Rain falls from clouds.",
    "An hour has sixty minutes.", "Bread is usually baked in an oven.", "Trees have roots.",
    "Wood floats on water.", "The moon orbits the Earth.", "Sugar tastes sweet.",
    "A minute has sixty seconds.", "Grass is usually green.", "Fire produces heat.",
    "Bees can fly.", "Salt dissolves in water.", "Leaves fall from many trees in autumn.",
]

INSTR = "Read the text and answer using ONLY what the text says.\n\n"


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def has(text, ans):
    return re.search(r"(?<![a-z0-9])" + re.escape(fold(ans)) + r"(?![a-z0-9])", fold(text)) is not None


def context_prompt(fact, planted, n_lines, position):
    filler = FILLER[: n_lines - 1]
    line = fact["statement"].format(planted)
    idx = {"early": 0, "middle": len(filler) // 2, "late": len(filler)}[position]
    lines = filler[:idx] + [line] + filler[idx:]
    text = "\n".join("- " + x for x in lines)
    return f"{INSTR}Text:\n{text}\n\nQuestion: According to the text, {fact['question']}\nAnswer:"


def main():
    for f in FACTS:
        assert not has(f["wrong"], f["true"]) and not has(f["true"], f["wrong"]), f
    items = []
    for i, f in enumerate(FACTS, 1):
        base = dict(fact_id=f"F{i:03d}", category=f["category"], subject=f["subject"],
                    real_answer=f["true"], context_answer=f["wrong"])
        items.append(dict(base, condition="baseline", length="none", position="none",
                          planted="none", prompt=f"Question: {f['question']}\nAnswer:"))
        for length, n in (("short", 9), ("long", 31)):
            for pos in ("early", "middle", "late"):
                items.append(dict(base, condition="conflict", length=length, position=pos,
                                  planted="wrong", prompt=context_prompt(f, f["wrong"], n, pos)))
            items.append(dict(base, condition="support", length=length, position="middle",
                              planted="true", prompt=context_prompt(f, f["true"], n, "middle")))
    for k, it in enumerate(items, 1):
        it["item_id"] = f"V2_{k:04d}"
    json.dump(items, open("pool_probe_v2.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"facts: {len(FACTS)}  items: {len(items)}  -> pool_probe_v2.json")


if __name__ == "__main__":
    main()
