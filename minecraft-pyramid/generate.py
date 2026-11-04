"""Генератор датапака «Стеклянная пирамида с фонарями» для Minecraft (Java, 1.18.2 и 1.20.1).

Запуск:  python3 generate.py
Результат: папка build/ с двумя zip-архивами (по одному на версию игры).
"""
import json
import pathlib
import shutil

import lattice

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


CUBE_SIZES = {"small": 15, "medium": 20, "large": 30}  # «радиус» куба: сторона = 2*R+1
GRID_STEP = 4  # шаг сетки внутри куба


def cube_commands(R: int, grid: bool) -> list[str]:
    """Большой стеклянный куб-комната. Игрок стоит в центре пола.
    grid=True — внутри ещё объёмная сетка: стеклянные блоки с фонарями под ними."""
    H = 2 * R  # верхний слой (пол на ~-1, потолок на ~H)
    side = 2 * R + 1
    cmds = [f"# Куб {side}x{side}x{H+2} (с полом и потолком). Центр пола — там, где стоит игрок."]
    cmds.append('tellraw @s {"text":"Строю куб...","color":"gold"}')
    # Внутренность: очищаем послойно (у /fill лимит 32768 блоков за раз)
    for y in range(0, H):
        cmds.append(f"fill ~-{R-1} ~{y} ~-{R-1} ~{R-1} ~{y} ~{R-1} minecraft:air")
    # Пол — чёрный бетон, стены и потолок — стекло
    cmds.append(f"fill ~-{R} ~-1 ~-{R} ~{R} ~-1 ~{R} {FLOOR}")
    cmds.append(f"fill ~-{R} ~{H} ~-{R} ~{R} ~{H} ~{R} {GLASS}")
    cmds.append(f"fill ~-{R} ~0 ~-{R} ~{R} ~{H-1} ~-{R} {GLASS}")
    cmds.append(f"fill ~-{R} ~0 ~{R} ~{R} ~{H-1} ~{R} {GLASS}")
    cmds.append(f"fill ~-{R} ~0 ~-{R} ~-{R} ~{H-1} ~{R} {GLASS}")
    cmds.append(f"fill ~{R} ~0 ~-{R} ~{R} ~{H-1} ~{R} {GLASS}")
    # Фонари вдоль стен по полу внутри (каждые 2 блока) и снаружи по периметру (как в видео)
    rim = R - 1
    for i in range(-rim, rim + 1, 2):
        for x, z in ((i, -rim), (i, rim), (-rim, i), (rim, i)):
            cmds.append(f"setblock ~{x} ~0 ~{z} {LANTERN}")
    out = R + 1
    for i in range(-out, out + 1, 2):
        for x, z in ((i, -out), (i, out), (-out, i), (out, i)):
            cmds.append(f"setblock ~{x} ~-1 ~{z} {FLOOR}")
            cmds.append(f"setblock ~{x} ~0 ~{z} {LANTERN}")
    # Фонари, висящие под потолком (сетка с шагом 4)
    for x in range(-rim + 1, rim, 4):
        for z in range(-rim + 1, rim, 4):
            cmds.append(f"setblock ~{x} ~{H-1} ~{z} {HANGING}")
    if grid:
        # Объёмная сетка: стеклянный блок, под ним висит фонарь
        lo = -(R - 3) + ((R - 3) % GRID_STEP)
        for x in range(lo, R - 2, GRID_STEP):
            for z in range(lo, R - 2, GRID_STEP):
                for y in range(3, H - 2, GRID_STEP):
                    if abs(x) <= 1 and abs(z) <= 1 and y <= 3:
                        continue  # не замуровываем игрока
                    cmds.append(f"setblock ~{x} ~{y} ~{z} {GLASS}")
                    cmds.append(f"setblock ~{x} ~{y-1} ~{z} {HANGING}")
    cmds.append('tellraw @s {"text":"Готово!","color":"green"}')
    return cmds


def cube_remove(R: int) -> list[str]:
    H = 2 * R
    cmds = [f"# Удаляет куб R={R} (стоять там же, где строили)"]
    for y in range(0, H + 1):
        cmds.append(f"fill ~-{R+1} ~{y} ~-{R+1} ~{R+1} ~{y} ~{R+1} minecraft:air")
    cmds.append(f"fill ~-{R+1} ~-1 ~-{R+1} ~{R+1} ~-1 ~{R+1} minecraft:grass_block")
    cmds.append('tellraw @s {"text":"Куб удалён","color":"yellow"}')
    return cmds


def count(cmds: list[str]) -> dict:
    """Точный подсчёт блоков: проигрываем команды на виртуальной сетке."""
    world = {}
    def n(s): return int(s[1:] or 0)
    for c in cmds:
        p = c.split()
        if not p or p[0] not in ("fill", "setblock"):
            continue
        if p[0] == "fill":
            x1, y1, z1, x2, y2, z2 = map(n, p[1:7])
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    for z in range(z1, z2 + 1):
                        world[(x, y, z)] = p[7]
        else:
            world[tuple(map(n, p[1:4]))] = p[4]
    res = {}
    for b in world.values():
        key = "lantern" if "lantern" in b else b.replace("minecraft:", "")
        if key != "air":
            res[key] = res.get(key, 0) + 1
    return res


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
        for name, R in CUBE_SIZES.items():
            (fn_dir / f"cube_{name}.mcfunction").write_text("\n".join(cube_commands(R, False)) + "\n", encoding="utf-8")
            (fn_dir / f"cube_grid_{name}.mcfunction").write_text("\n".join(cube_commands(R, True)) + "\n", encoding="utf-8")
            (fn_dir / f"cube_remove_{name}.mcfunction").write_text("\n".join(cube_remove(R)) + "\n", encoding="utf-8")
        for name, n in lattice.LATTICE_SIZES.items():
            for fname, lines in lattice.files_for(name, n).items():
                (fn_dir / f"{fname}.mcfunction").write_text("\n".join(lines) + "\n", encoding="utf-8")
        shutil.make_archive(str(pack), "zip", pack)
        shutil.rmtree(pack)
    lattice.summary()
    for name, R in SIZES.items():
        s = stats(R)
        print(f"{name:6}: основание {2*R+1}x{2*R+1}, высота {R+1}, стекло {s['glass']}, "
              f"фонари {s['lanterns']}, пол {s['floor']}")
    for name, R in CUBE_SIZES.items():
        for grid in (False, True):
            label = f"cube{'_grid' if grid else ''}_{name}"
            print(f"{label:18}: сторона {2*R+1}, {count(cube_commands(R, grid))}")


if __name__ == "__main__":
    main()
