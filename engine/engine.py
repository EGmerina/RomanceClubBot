from __future__ import annotations

from dataclasses import dataclass, field

from .parser import Story


@dataclass
class PlayerState:
    """
    Состояние конкретного игрока.

    Здесь позже можно добавить:

        romance_alex
        money
        courage
        flags
        inventory
        etc.
    """

    current_node: str

    variables: dict[str, int | float | str | bool] = field(
        default_factory=dict
    )


@dataclass
class Screen:
    """
    То, что нужно показать пользователю.
    """

    text: str

    choices: list[tuple[str, str]] = field(
        default_factory=list
    )

    ending: bool = False


class StoryEngine:

    def __init__(self, story: Story):
        self.story = story

    # ========================================================
    # Создание игрока
    # ========================================================

    def new_player(self) -> PlayerState:

        if self.story.start is None:
            raise ValueError("У сценария нет начальной сцены.")

        return PlayerState(
            current_node=self.story.start
        )

    # ========================================================
    # Получение текущего экрана
    # ========================================================

    def get_screen(self, player: PlayerState) -> Screen:

        node_id = player.current_node

        # ----------------------------------------------------
        # Сцена
        # ----------------------------------------------------

        if node_id in self.story.scenes:

            scene = self.story.scenes[node_id]

            # Есть варианты выбора
            if scene.choices:

                choices = [
                    (choice.text, choice.target)
                    for choice in scene.choices
                ]

                return Screen(
                    text=scene.text,
                    choices=choices,
                )

            # Просто сцена
            return Screen(
                text=scene.text
            )

        # ----------------------------------------------------
        # Концовка
        # ----------------------------------------------------

        if node_id in self.story.endings:

            ending = self.story.endings[node_id]

            return Screen(
                text=ending.text,
                ending=True
            )

        raise ValueError(
            f"Неизвестный узел сценария: {node_id}"
        )

    # ========================================================
    # Переход дальше
    # ========================================================

    def choose(
        self,
        player: PlayerState,
        target: str
    ) -> Screen:

        # Проверяем, что такой переход действительно
        # существует из текущей сцены.

        current = self.story.scenes.get(
            player.current_node
        )

        if current is None:
            raise ValueError(
                "Текущий узел не является сценой."
            )

        allowed_targets = []

        # Обычный переход
        if current.next_scene:
            allowed_targets.append(
                current.next_scene
            )

        # Варианты
        for choice in current.choices:
            allowed_targets.append(choice.target)

        if target not in allowed_targets:
            raise ValueError(
                f"Недопустимый переход: "
                f"{player.current_node} -> {target}"
            )

        player.current_node = target

        return self.get_screen(player)

    # ========================================================
    # Автоматически перейти по единственному переходу
    # ========================================================

    def advance(
        self,
        player: PlayerState
    ) -> Screen:

        current = self.story.scenes.get(
            player.current_node
        )

        if current is None:
            return self.get_screen(player)

        if current.choices:
            return self.get_screen(player)

        if current.next_scene is None:
            return self.get_screen(player)

        player.current_node = current.next_scene

        return self.get_screen(player)