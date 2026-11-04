"""Генератор датапака «Стеклянная пирамида с фонарями» для Minecraft (Java, 1.18.2 и 1.20.1).

Запуск:  python3 generate.py
Результат: папка build/ с двумя zip-архивами (по одному на версию игры).
"""
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).parent
BUILD = ROOT / "build"

# Размеры: имя -> «радиус» основания (основание = 2*R+1 блоков, высота = R+1)
SIZES = {"small": 15, "medium": 25, "large": 40}

# Версия игры -> pack_format датапака
VERSIONS = {"1.18.2": 9, "1.20.1": 15}

GLASS = "minecraft:glass"
FLOOR = "minecraft:black_concrete"
LANTERN = "minecraft:lantern"
HANGING = "minecraft:lantern[hanging=true]"
CHAIN = "minecraft:chain"


def build_commands(R: int) -> list[str]:
    cmds = [f"# Пирамида: основание {2*R+1}x{2*R+1}, высота {R+1}. Центр — там, где стоит игрок."]
    cmds.append('tellraw @s {"text":"Строю пирамиду...","color":"gold"}')
    # Пол
    cmds.append(f"fill ~-{R} ~-1 ~-{R} ~{R} ~-1 ~{R} {FLOOR}")
    # Слои: на каждом уровне y — квадратное кольцо стекла радиуса R-y, внутри — воздух
    for y in range(R + 1):
        r = R - y
        cmds.append(f"fill ~-{r} ~{y} ~-{r} ~{r} ~{y} ~{r} {GLASS}")
        if r >= 1:
            ri = r - 1
            cmds.append(f"fill ~-{ri} ~{y} ~-{ri} ~{ri} ~{y} ~{ri} minecraft:air")
    # Фонари на полу вдоль стен (каждые 2 блока)
    rim = R - 1
    for i in range(-rim, rim + 1, 2):
        for x, z in ((i, -rim), (i, rim), (-rim, i), (rim, i)):
            cmds.append(f"setblock ~{x} ~0 ~{z} {LANTERN}")
    # Висячие фонари под наклонными стенами: каждые 3 слоя вверх, каждые 4 блока вдоль
    for k in range(3, R - 1, 3):
        rr = R - k  # радиус стеклянного кольца на слое k; фонарь висит под ним на слое k-1
        for i in range(-(rr - 1), rr, 4):
            for x, z in ((i, -rr), (i, rr), (-rr, i), (rr, i)):
                cmds.append(f"setblock ~{x} ~{k-1} ~{z} {HANGING}")
    # Большой фонарь на цепи в центре, под вершиной
    top = R - 1  # самый верхний воздушный слой под вершиной
    chain_len = max(1, R // 4)
    for j in range(chain_len):
        cmds.append(f"setblock ~0 ~{top - j} ~0 {CHAIN}")
    cmds.append(f"setblock ~0 ~{top - chain_len} ~0 {HANGING}")
    cmds.append('tellraw @s {"text":"Готово!","color":"green"}')
    return cmds


def remove_commands(R: int) -> list[str]:
    return [
        f"# Удаляет пирамиду размера R={R} вокруг игрока (стоять там же, где строили)",
        f"fill ~-{R} ~0 ~-{R} ~{R} ~{R} ~{R} minecraft:air",
        f"fill ~-{R} ~-1 ~-{R} ~{R} ~-1 ~{R} minecraft:grass_block",
        'tellraw @s {"text":"Пирамида удалена","color":"yellow"}',
    ]


def stats(R: int) -> dict:
    glass = sum((2 * (R - y) + 1) ** 2 - (max(0, 2 * (R - y) - 1)) ** 2 for y in range(R + 1))
    cmds = build_commands(R)
    lanterns = sum(1 for c in cmds if "lantern" in c and c.startswith("setblock"))
    return {"glass": glass, "lanterns": lanterns, "floor": (2 * R + 1) ** 2}


def main():
    if BUILD.exists():
        shutil.rmtree(BUILD)
    for version, fmt in VERSIONS.items():
        pack = BUILD / f"pyramid-datapack-{version}"
        fn_dir = pack / "data" / "pyramid" / "functions"
        fn_dir.mkdir(parents=True)
        (pack / "pack.mcmeta").write_text(json.dumps(
            {"pack": {"pack_format": fmt, "description": f"Стеклянная пирамида с фонарями (MC {version})"}},
            ensure_ascii=False, indent=2), encoding="utf-8")
        for name, R in SIZES.items():
            (fn_dir / f"build_{name}.mcfunction").write_text("\n".join(build_commands(R)) + "\n", encoding="utf-8")
            (fn_dir / f"remove_{name}.mcfunction").write_text("\n".join(remove_commands(R)) + "\n", encoding="utf-8")
        shutil.make_archive(str(pack), "zip", pack)
        shutil.rmtree(pack)
    for name, R in SIZES.items():
        s = stats(R)
        print(f"{name:6}: основание {2*R+1}x{2*R+1}, высота {R+1}, стекло {s['glass']}, "
              f"фонари {s['lanterns']}, пол {s['floor']}")


if __name__ == "__main__":
    main()
