from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

from dataclasses import dataclass, field
from pathlib import Path


# ============================================================
# МОДЕЛЬ СЦЕНАРИЯ
# ============================================================

@dataclass
class Choice:
    """
    Вариант выбора игрока.

    Например:
        "да" -> scene_3
    """
    text: str
    target: str


@dataclass
class Scene:
    """
    Обычная сцена.
    """

    id: str
    text: str

    # Если сцена просто ведет дальше без выбора:
    next_scene: str | None = None

    # Если после сцены нужно предложить варианты:
    choices: list[Choice] = field(default_factory=list)


@dataclass
class Ending:
    id: str
    text: str


@dataclass
class Story:
    """
    Вся история целиком.
    """

    start: str | None = None

    scenes: dict[str, Scene] = field(default_factory=dict)

    endings: dict[str, Ending] = field(default_factory=dict)

    # Сюда можно складывать и другие типы узлов,
    # если позже они понадобятся.
    nodes: dict[str, dict] = field(default_factory=dict)


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def clean_text(value: str | None) -> str:
    """
    Очищает текст из draw.io.

    draw.io может использовать HTML внутри value:
        <b>Привет</b>
        Ты &amp; я

    Превращаем это в обычный текст.
    """

    if not value:
        return ""

    value = html.unescape(value)

    # <br> превращаем в перенос строки
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)

    # Убираем остальные HTML-теги
    value = re.sub(r"<[^>]+>", "", value)

    return value.strip()


def get_node_type(style: str) -> str:
    """
    Определяет тип узла по стилю draw.io.

    Поддерживаем нашу договоренность:

        triangle  -> start
        rhombus   -> choice
        hexagon   -> ending
        rounded=1 -> scene
    """

    style = style or ""

    if "triangle" in style:
        return "start"

    if "rhombus" in style:
        return "choice"

    if "hexagon" in style:
        return "ending"

    # Наши сцены сделаны как:
    # rounded=1;whiteSpace=wrap;...
    if "rounded=1" in style:
        return "scene"

    return "unknown"


# ============================================================
# ПАРСЕР
# ============================================================

class DrawioParser:

    def parse_file(self, filename: str | Path) -> Story:
        """
        Читает drawio-файл и возвращает Story.
        """

        tree = ET.parse(filename)
        root = tree.getroot()

        return self.parse_xml(root)

    def parse_xml(self, root: ET.Element) -> Story:

        story = Story()

        # ----------------------------------------------------
        # 1. Собираем все vertex-узлы
        # ----------------------------------------------------

        nodes = {}

        for cell in root.iter("mxCell"):

            if cell.get("vertex") != "1":
                continue

            node_id = cell.get("id")

            if not node_id:
                continue

            value = clean_text(cell.get("value"))
            style = cell.get("style", "")

            node_type = get_node_type(style)

            nodes[node_id] = {
                "id": node_id,
                "value": value,
                "style": style,
                "type": node_type,
            }

        # ----------------------------------------------------
        # 2. Собираем связи
        # ----------------------------------------------------

        outgoing: dict[str, list[str]] = {}
        incoming: dict[str, list[str]] = {}

        for cell in root.iter("mxCell"):

            if cell.get("edge") != "1":
                continue

            source = cell.get("source")
            target = cell.get("target")

            if not source or not target:
                continue

            outgoing.setdefault(source, []).append(target)
            incoming.setdefault(target, []).append(source)

        # ----------------------------------------------------
        # 3. Сохраняем информацию о графе
        # ----------------------------------------------------

        story.nodes = nodes

        # ----------------------------------------------------
        # 4. Ищем START
        # ----------------------------------------------------

        start_nodes = [
            node_id
            for node_id, node in nodes.items()
            if node["type"] == "start"
        ]

        if len(start_nodes) == 0:
            raise ValueError("В сценарии не найдено начало (triangle).")

        if len(start_nodes) > 1:
            raise ValueError(
                f"Найдено несколько начал: {start_nodes}"
            )

        start_node = start_nodes[0]

        start_targets = outgoing.get(start_node, [])

        if len(start_targets) != 1:
            raise ValueError(
                "Начало должно вести ровно к одной сцене."
            )

        story.start = start_targets[0]

        # ----------------------------------------------------
        # 5. Обрабатываем сцены
        # ----------------------------------------------------

        for node_id, node in nodes.items():

            if node["type"] != "scene":
                continue

            targets = outgoing.get(node_id, [])

            scene = Scene(
                id=node_id,
                text=node["value"],
            )

            # -----------------------------------------------
            # Нет переходов
            # -----------------------------------------------

            if not targets:
                story.scenes[node_id] = scene
                continue

            # -----------------------------------------------
            # Один переход
            # -----------------------------------------------

            if len(targets) == 1:

                target = targets[0]

                target_node = nodes.get(target)

                if target_node is None:
                    raise ValueError(
                        f"Сцена {node_id} ведет в "
                        f"несуществующий узел {target}"
                    )

                # Если это обычная сцена —
                # просто переход.
                if target_node["type"] == "scene":
                    scene.next_scene = target

                # Если это конец — тоже сохраняем переход.
                elif target_node["type"] == "ending":
                    scene.next_scene = target

                # Если это choice — тоже допустимо.
                elif target_node["type"] == "choice":

                    choice_targets = outgoing.get(target, [])

                    if len(choice_targets) != 1:
                        raise ValueError(
                            f"Вариант '{target_node['value']}' "
                            f"должен вести ровно к одному узлу."
                        )

                    scene.choices.append(
                        Choice(
                            text=target_node["value"],
                            target=choice_targets[0],
                        )
                    )

                else:
                    scene.next_scene = target

            # -----------------------------------------------
            # Несколько переходов
            #
            # Это означает:
            #
            # scene
            #   ├── choice
            #   ├── choice
            #   └── choice
            # -----------------------------------------------

            else:

                for target in targets:

                    target_node = nodes.get(target)

                    if target_node is None:
                        raise ValueError(
                            f"Сцена {node_id} ведет в "
                            f"несуществующий узел {target}"
                        )

                    if target_node["type"] != "choice":
                        raise ValueError(
                            f"Сцена '{node_id}' имеет несколько "
                            f"переходов, но один из них не является "
                            f"вариантом выбора: {target}"
                        )

                    choice_targets = outgoing.get(target, [])

                    if len(choice_targets) != 1:
                        raise ValueError(
                            f"Вариант '{target_node['value']}' "
                            f"должен вести ровно к одному узлу."
                        )

                    scene.choices.append(
                        Choice(
                            text=target_node["value"],
                            target=choice_targets[0],
                        )
                    )

            story.scenes[node_id] = scene

        # ----------------------------------------------------
        # 6. Обрабатываем концовки
        # ----------------------------------------------------

        for node_id, node in nodes.items():

            if node["type"] != "ending":
                continue

            story.endings[node_id] = Ending(
                id=node_id,
                text=node["value"],
            )

        # ----------------------------------------------------
        # 7. Проверяем ссылки
        # ----------------------------------------------------

        known_ids = set(nodes.keys())

        for scene in story.scenes.values():

            if scene.next_scene:
                if scene.next_scene not in known_ids:
                    raise ValueError(
                        f"Сцена '{scene.id}' ведет в "
                        f"несуществующий узел '{scene.next_scene}'"
                    )

            for choice in scene.choices:

                if choice.target not in known_ids:
                    raise ValueError(
                        f"Вариант '{choice.text}' ведет в "
                        f"несуществующий узел '{choice.target}'"
                    )

        return story