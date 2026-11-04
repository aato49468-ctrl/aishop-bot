"""Генератор «стеклянной решётки» — копия постройки из видео.

Огромный куб, заполненный стеклянными блоками через один (стекло — пустота — стекло по всем трём осям),
внутри разбросаны обычные фонари (стоят на стекле и висят под стеклом).

Как строится внутри игры (чтобы уложиться в лимиты Minecraft 1.18.2):
  1. forceload — загружаем все чанки под постройкой, ставим невидимый маркер в точке игрока;
  2. через 2 секунды: очищаем объём, строим одну «плитку» 32x32x32 (4096 стёкол + фонари),
     затем копируем её /clone на весь объём (у /fill и /clone лимит 32768 блоков за раз).
Вызывается из generate.py.
"""
import random

T = 32  # размер плитки
# имя -> количество плиток по каждой оси
LATTICE_SIZES = {"small": 2, "medium": 4, "large": 6, "huge": 7}
LANTERNS_PER_TILE = 140
GLASS = "minecraft:glass"
LANTERN = "minecraft:lantern"
HANGING = "minecraft:lantern[hanging=true]"
FLOOR = "minecraft:black_concrete"


def tile_cells(seed: int = 52):
    """Стекло в позициях (чёт, чёт, чёт); фонари — в клетках (чёт, нечёт, чёт): над ними и под ними стекло."""
    glass = [(x, y, z) for x in range(0, T, 2) for y in range(0, T, 2) for z in range(0, T, 2)]
    rnd = random.Random(seed)
    spots = [(x, y, z) for x in range(0, T, 2) for y in range(1, T - 1, 2) for z in range(0, T, 2)]
    lanterns = [(p, rnd.random() < 0.5) for p in rnd.sample(spots, LANTERNS_PER_TILE)]
    return glass, lanterns


def files_for(name: str, n: int) -> dict[str, list[str]]:
    S = n * T          # сторона куба
    h = S // 2         # центр по X/Z — там, где стоит игрок; низ — на уровне ног
    tag = f"lat_{name}"
    start = [
        f"# Решётка {S}x{S}x{S}. Шаг 1: грузим чанки и ставим маркер.",
        f"kill @e[type=marker,tag={tag}]",
        f"forceload add ~-{h+2} ~-{h+2} ~{h+2} ~{h+2}",
        f'summon marker ~ ~ ~ {{Tags:["{tag}"]}}',
        f'tellraw @a {{"text":"Готовлю место под куб {S}x{S}x{S}... (2 сек)","color":"gold"}}',
        f"schedule function pyramid:lattice_{name}_go 40t",
    ]
    go = [
        f"execute as @e[type=marker,tag={tag},limit=1] at @s run function pyramid:lattice_{name}_build",
        f"execute as @e[type=marker,tag={tag},limit=1] at @s run forceload remove ~-{h+2} ~-{h+2} ~{h+2} ~{h+2}",
        f"kill @e[type=marker,tag={tag}]",
        'tellraw @a {"text":"Готово! Свет может догружаться несколько секунд.","color":"green"}',
    ]
    b = [f"# Решётка {S}x{S}x{S}, угол (~-{h}, ~0, ~-{h})"]
    x0, z0 = -h, -h
    # пол из чёрного бетона (с запасом 2 блока) и очистка объёма — кусками по 32x32x32
    for ix in range(n):
        for iz in range(n):
            ax, az = x0 + ix * T, z0 + iz * T
            b.append(f"fill ~{ax} ~-1 ~{az} ~{ax+T-1} ~-1 ~{az+T-1} {FLOOR}")
            for iy in range(n):
                ay = iy * T
                b.append(f"fill ~{ax} ~{ay} ~{az} ~{ax+T-1} ~{ay+T-1} ~{az+T-1} minecraft:air")
    for i in range(-h - 2, h + 2):  # кайма пола
        for x, z in ((i, -h - 2), (i, h + 1), (-h - 2, i), (h + 1, i), (i, -h - 1), (i, h), (-h - 1, i), (h, i)):
            if not (-h <= x < h and -h <= z < h):
                b.append(f"setblock ~{x} ~-1 ~{z} {FLOOR}")
    # фонари по периметру снаружи (как в видео)
    for i in range(-h - 1, h + 1, 2):
        for x, z in ((i, -h - 2), (i, h + 1), (-h - 2, i), (h + 1, i)):
            b.append(f"setblock ~{x} ~0 ~{z} {LANTERN}")
    # первая плитка
    glass, lanterns = tile_cells()
    for x, y, z in glass:
        b.append(f"setblock ~{x0+x} ~{y} ~{z0+z} {GLASS}")
    for (x, y, z), hanging in lanterns:
        b.append(f"setblock ~{x0+x} ~{y} ~{z0+z} {HANGING if hanging else LANTERN}")
    # копируем плитку на весь объём
    sx2, sz2 = x0 + T - 1, z0 + T - 1
    for ix in range(n):
        for iy in range(n):
            for iz in range(n):
                if ix == iy == iz == 0:
                    continue
                b.append(f"clone ~{x0} ~0 ~{z0} ~{sx2} ~{T-1} ~{sz2} ~{x0+ix*T} ~{iy*T} ~{z0+iz*T}")
    remove_start = [
        f"# Удаление решётки {S}x{S}x{S}. Встаньте туда же, где строили.",
        f"kill @e[type=marker,tag={tag}_rm]",
        f"forceload add ~-{h+2} ~-{h+2} ~{h+2} ~{h+2}",
        f'summon marker ~ ~ ~ {{Tags:["{tag}_rm"]}}',
        f"schedule function pyramid:lattice_remove_{name}_go 40t",
    ]
    rm = []
    for ix in range(n):
        for iz in range(n):
            ax, az = x0 + ix * T, z0 + iz * T
            for iy in range(n):
                rm.append(f"fill ~{ax} ~{iy*T} ~{az} ~{ax+T-1} ~{iy*T+T-1} ~{az+T-1} minecraft:air")
    rm.append(f"fill ~{-h-2} ~0 ~{-h-2} ~{h+1} ~0 ~{-h-1} minecraft:air")
    rm.append(f"fill ~{-h-2} ~0 ~{h} ~{h+1} ~0 ~{h+1} minecraft:air")
    rm.append(f"fill ~{-h-2} ~0 ~{-h-2} ~{-h-1} ~0 ~{h+1} minecraft:air")
    rm.append(f"fill ~{h} ~0 ~{-h-2} ~{h+1} ~0 ~{h+1} minecraft:air")
    remove_go = [
        f"execute as @e[type=marker,tag={tag}_rm,limit=1] at @s run function pyramid:lattice_remove_{name}_do",
        f"execute as @e[type=marker,tag={tag}_rm,limit=1] at @s run forceload remove ~-{h+2} ~-{h+2} ~{h+2} ~{h+2}",
        f"kill @e[type=marker,tag={tag}_rm]",
        'tellraw @a {"text":"Решётка удалена","color":"yellow"}',
    ]
    return {
        f"lattice_{name}": start,
        f"lattice_{name}_go": go,
        f"lattice_{name}_build": b,
        f"lattice_remove_{name}": remove_start,
        f"lattice_remove_{name}_go": remove_go,
        f"lattice_remove_{name}_do": rm,
    }


def summary():
    glass, lanterns = tile_cells()
    for name, n in LATTICE_SIZES.items():
        S = n * T
        tiles = n ** 3
        print(f"lattice_{name:6}: куб {S}x{S}x{S}, стекла {len(glass)*tiles:,}, фонарей {len(lanterns)*tiles:,}"
              f" (+{2*S+4} снаружи), нужно стоять не выше Y={320-S}")
