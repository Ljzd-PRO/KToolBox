from __future__ import annotations

import json
import pprint
import warnings
import webbrowser
from collections.abc import Callable, Generator, Hashable, Iterable, Sequence
from pathlib import Path
from typing import (
    Any,
    Literal,
    NoReturn,
    TypeVar,
    Union,
    get_args,
)

import urwid
from pydantic import BaseModel

# noinspection PyProtectedMember
from pydantic._internal._model_construction import ModelMetaclass

from ktoolbox import __version__
from ktoolbox.configuration import Configuration, config
from ktoolbox.project_config import ProjectConfigError, ProjectConfigStore

warnings.filterwarnings("ignore")

_T = TypeVar("_T")
__all__ = ["EditWithSignalWidget", "CascadingBoxes", "run_config_editor"]


class EditWithSignalWidget(urwid.Edit):
    """
    Custom ``urwid.Edit``, support callback when changed.
    """

    def __init__(
        self, *args, on_state_change: Callable[[EditWithSignalWidget, _T], Any] | None, user_data: _T | None, **kwargs
    ) -> None:
        self.__on_state_change = on_state_change
        self.__user_data = user_data
        super().__init__(*args, **kwargs)

    def keypress(self, size: tuple[int], key: str) -> str | None:
        ret = super().keypress(size, key)
        self.__on_state_change(self, self.__user_data)
        return ret


class CascadingBoxes(urwid.WidgetPlaceholder):
    max_box_levels = 4

    def __init__(self, box: urwid.Widget) -> None:
        super().__init__(urwid.SolidFill("/"))
        self.box_level = 0
        self.open_box(box)

    def open_box(self, box: urwid.Widget):
        self.original_widget = urwid.Overlay(
            urwid.LineBox(urwid.Padding(box, align=urwid.CENTER, left=2, right=2)),
            self.original_widget,
            align=urwid.CENTER,
            width=(urwid.RELATIVE, 80),
            valign=urwid.MIDDLE,
            height=(urwid.RELATIVE, 80),
            min_width=24,
            min_height=8,
            left=self.box_level * 3,
            right=(self.max_box_levels - self.box_level - 1) * 3,
            top=self.box_level * 2,
            bottom=(self.max_box_levels - self.box_level - 1) * 2,
        )
        self.box_level += 1

    def back(self) -> NoReturn | None:
        self.original_widget = self.original_widget[0]
        self.box_level -= 1
        return None

    def exit(self):
        raise urwid.ExitMainLoop()

    def keypress(self, size, key: str) -> str | NoReturn | None:
        if key == "esc":
            if self.box_level > 1:
                self.back()
            else:
                exit_program()
        return super().keypress(size, key)


def dump_envs(model: BaseModel) -> list[str]:
    """Dump environment variables, with no Env prefix"""
    envs = []
    for field in model.model_fields:
        value = model.__getattribute__(field)
        if isinstance(value, BaseModel):
            for env in dump_envs(value):
                envs.append(f"{field.upper()}__{env}")
        else:
            envs.append(
                f"{field.upper()}="
                f"{json.dumps(list(value)) if isinstance(value, (list, set, tuple, dict)) else model.__pydantic_serializer__.to_python(value)}"
            )
    return envs


def dump_modified_envs(envs: list[str]) -> list[str]:
    """
    Dump modified environment variables, with Env prefix

    :param envs: Current Envs
    """
    return sorted([f"KTOOLBOX_{env}" for env in set(envs) - default_config_envs])


def save_dotenv():
    current_envs = dump_envs(config)
    envs_to_dump = "\n".join(dump_modified_envs(current_envs))
    prod_dotenv_path = Path("prod.env")
    dotenv_path = Path(".env")
    if prod_dotenv_path.is_file():
        with prod_dotenv_path.open("w") as f:
            f.write(envs_to_dump)
    else:
        with dotenv_path.open("w") as f:
            f.write(envs_to_dump)
    initial_envs.clear()
    initial_envs.update(current_envs)


def has_env_changed() -> bool:
    return bool(set(dump_envs(config)) - initial_envs)


def has_changed() -> bool:
    return has_env_changed() or project_toml_editor.edit_text != initial_project_text


def menu_option(widget: urwid.Widget) -> urwid.AttrMap:
    """Return ``focus_map="reversed"`` Widget"""
    return urwid.AttrMap(widget, None, focus_map="reversed")


def sub_menu_with_menu_widget(
    caption: str | tuple[Hashable, str] | list[str | tuple[Hashable, str]],
    choices: Iterable[urwid.Widget],
) -> tuple[urwid.AttrMap[urwid.Button], urwid.ListBox]:
    contents = menu(
        caption, list(choices) + [urwid.Divider(bottom=2), menu_option(urwid.Button("Back", lambda x: top.back()))]
    )

    return menu_option(urwid.Button([caption, "..."], lambda x: top.open_box(contents))), contents


def sub_menu(
    caption: str | tuple[Hashable, str] | list[str | tuple[Hashable, str]],
    choices: Iterable[urwid.Widget],
) -> urwid.AttrMap[urwid.Button]:
    button, _ = sub_menu_with_menu_widget(caption, choices)
    return button


def menu(
    title: str | tuple[Hashable, str] | list[str | tuple[Hashable, str]],
    choices: Iterable[urwid.Widget],
) -> urwid.ListBox:
    body = [urwid.Text(title, align=urwid.CENTER), urwid.Divider(), *choices]
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))


def on_radio_button_change(_: urwid.RadioButton, state: bool, user_data: tuple[BaseModel, str, Any]):
    if state:
        model, field, value = user_data
        model.__setattr__(field, value)


def on_checkbox_change(_: urwid.CheckBox, state: bool, user_data: tuple[BaseModel, str]):
    model, field = user_data
    model.__setattr__(field, state)


def on_add_item(
    _: urwid.Button,
    user_data: tuple[
        BaseModel,
        str,
        Callable[[], Any | None],
        list[_T] | list[None],
        Callable[[], _T],
        urwid.MonitoredFocusList[_T] | urwid.ListWalker,
    ],
):
    """
    Call when add item to List/Set/Tuple field

    :param _: Widget
    :param user_data: (model, field, () -> (default value), item list, () -> (new item), menu widget)
    """
    model, field, get_default, item_list, get_new_widget, widget = user_data
    values = list(model.__getattribute__(field))
    values.append(get_default())
    model.__setattr__(field, values)
    new_widget = get_new_widget()
    item_list.append(new_widget)
    widget.append(new_widget)


def on_remove_item(
    _: urwid.Button,
    user_data: tuple[BaseModel, str, list[_T] | list[None], _T, urwid.MonitoredFocusList[_T] | urwid.ListWalker],
):
    """
    Call when remove item to List/Set/Tuple field

    :param _: Widget
    :param user_data: (model, field, item list, item, menu widget)
    """
    model, field, item_list, item, widget = user_data
    values = list(model.__getattribute__(field))
    index = item_list.index(item)
    values.pop(index)
    model.__setattr__(field, values)
    item_list.pop(index)
    widget.remove(item)


def on_item_changed(
    widget: EditWithSignalWidget,
    user_data: tuple[BaseModel, str, Callable[[EditWithSignalWidget], Any], list[_T] | list[None], _T],
):
    """
    Call when List/Set/Tuple field item changed

    :param widget: Widget
    :param user_data: (model, field, (edit widget) -> (value), item list, item)
    """
    model, field, get_value_callback, item_list, item = user_data
    values = list(model.__getattribute__(field))
    index = item_list.index(item)
    values[index] = get_value_callback(widget)
    model.__setattr__(field, values)


def on_edit_change(widget: urwid.EditWithSignalWidget, user_data: tuple[BaseModel, str, Iterable[type]]):
    model, field, annotation = user_data
    for field_type in annotation:
        try:
            model.__setattr__(field, field_type(widget.get_edit_text()))
        except ValueError:
            continue
        else:
            break


def on_save_dotenv(_: urwid.Button):
    if has_env_changed():
        pile = urwid.Pile(
            [
                urwid.Text("Your changes have been saved."),
                urwid.Divider(),
                menu_option(urwid.Button("OK", lambda x: top.back())),
            ]
        )
        try:
            save_dotenv()
        except Exception as e:
            pile = urwid.Pile(
                [
                    urwid.Text("Unable to save changes!"),
                    urwid.Divider(),
                    urwid.Text(f"{type(e).__name__}: {e}"),
                    urwid.Divider(),
                    menu_option(urwid.Button("OK", lambda x: top.back())),
                ]
            )
    else:
        pile = urwid.Pile(
            [
                urwid.Text("Nothing has changed, no need to save."),
                urwid.Divider(),
                menu_option(urwid.Button("OK", lambda x: top.back())),
            ]
        )
    top.open_box(urwid.Filler(pile))


def on_save_project(_: urwid.Button):
    global initial_project_text
    try:
        project_store.replace_text(project_toml_editor.edit_text)
        normalized = project_store.load_text()
        project_toml_editor.set_edit_text(normalized)
        initial_project_text = normalized
        message = urwid.Text(f"Project configuration saved to {project_store.path}.")
    except ProjectConfigError as error:
        message = urwid.Text(f"Unable to save project configuration:\n{error}")
    top.open_box(
        urwid.Filler(
            urwid.Pile(
                [
                    message,
                    urwid.Divider(),
                    menu_option(urwid.Button("OK", lambda button: top.back())),
                ]
            )
        )
    )


def exit_program(_: urwid.Button = None) -> NoReturn | None:
    if has_changed():
        top.open_box(
            urwid.Filler(
                urwid.Pile(
                    [
                        urwid.Text("Any unsaved changes will be lost. Are you sure you want to EXIT?"),
                        urwid.Divider(),
                        menu_option(urwid.Button("NO", lambda x: top.back())),
                        menu_option(urwid.Button("YES", lambda x: top.exit())),
                    ]
                )
            )
        )
    else:
        top.exit()


def get_value(item_types: Sequence[type]) -> Callable[[EditWithSignalWidget], Any | None]:
    def inner(w: EditWithSignalWidget = None):
        for t in item_types:
            try:
                return t(w.get_edit_text()) if w is not None else t()
            except ValueError:
                continue
        return None

    return inner


def get_item(
    model: BaseModel,
    field: str,
    get_value_callback: Callable[[EditWithSignalWidget], Any | None],
    widget_list: list[urwid.WidgetPlaceholder],
    list_walker: urwid.ListWalker,
) -> Callable[[str], urwid.WidgetPlaceholder]:
    def inner(edit_text: str = ""):
        item = urwid.WidgetPlaceholder(urwid.Widget())
        edit_widget = EditWithSignalWidget(
            edit_text=edit_text,
            align=urwid.LEFT,
            on_state_change=on_item_changed,
            user_data=(model, field, get_value_callback, widget_list, item),
        )
        columns_widget = urwid.Columns(
            [
                edit_widget,
                urwid.Divider(),
                urwid.Divider(),
                urwid.Button("Remove -", on_remove_item, (model, field, widget_list, item, list_walker)),
            ]
        )
        item.original_widget = columns_widget
        return item

    return inner


def model_to_widgets(model: BaseModel, fields: Iterable[str] = None) -> Generator[urwid.Widget, Any, None]:
    """
    Generate urwid widgets for Pydantic model

    :param model: Pydantic model
    :param fields: Only generate for these fields, default to all fields.
    """
    for field, field_info in model.model_fields.items():
        if fields is not None and field not in fields:
            continue
        origin_annotation = getattr(field_info.annotation, "__origin__", None)
        annotation = get_args(field_info.annotation) if origin_annotation is Union else [field_info.annotation]

        if origin_annotation is Literal:
            radio_buttons = []
            for value in get_args(field_info.annotation):
                menu_option(
                    urwid.RadioButton(
                        radio_buttons,
                        str(value),
                        model.__getattribute__(field) == value,
                        on_radio_button_change,
                        (model, field, value),
                    )
                )
            yield sub_menu(field, radio_buttons)
        elif bool in annotation:
            yield menu_option(
                urwid.CheckBox(
                    field, model.__getattribute__(field), on_state_change=on_checkbox_change, user_data=(model, field)
                )
            )
        elif any(map(lambda x: x in annotation, [str, int, float, Path])):
            yield menu_option(
                urwid.Columns(
                    [
                        urwid.Text(f"{' ' * 4}{field}", align=urwid.LEFT),
                        EditWithSignalWidget(
                            edit_text=str(model.__getattribute__(field)),
                            align=urwid.RIGHT,
                            on_state_change=on_edit_change,
                            user_data=(model, field, annotation),
                        ),
                    ]
                )
            )
        elif origin_annotation in [list, set, tuple]:
            item_types = get_args(field_info.annotation)
            widget_list = []
            widget, menu_widget = sub_menu_with_menu_widget(field, [])
            list_walker: urwid.SimpleFocusListWalker = menu_widget.body  # type: ignore
            widget_list.extend(
                [
                    get_item(model, field, get_value(item_types), widget_list, list_walker)(str(existed))
                    for existed in model.__getattribute__(field)
                ]
            )
            # noinspection PyTypeChecker
            option_widget = menu_option(
                urwid.Button(
                    "Add +",
                    on_add_item,
                    (
                        model,
                        field,
                        get_value(item_types),
                        widget_list,
                        get_item(model, field, get_value(item_types), widget_list, list_walker),
                        list_walker,
                    ),
                )
            )
            list_walker.extend([urwid.Divider(), option_widget, urwid.Divider()])
            list_walker.extend(widget_list)
            yield widget
        elif isinstance(field_info.annotation, ModelMetaclass):
            yield sub_menu(field, model_to_widgets(model.__getattribute__(field)))
        else:
            yield sub_menu(
                field,
                [
                    urwid.Text(
                        f"This option ({repr(field_info.annotation)}) is currently not supported for editing in "
                        "the graphical interface; please edit it in the '.env' or 'prod.env' file in the working directory."
                    )
                ],
            )
    yield urwid.Divider()
    yield menu_option(
        urwid.Button(
            f"View Document: {type(model).__name__}",
            lambda x: webbrowser.open(
                f"https://ktoolbox.readthedocs.io/latest/configuration/reference/#ktoolbox.configuration.{type(model).__name__}"
            ),
        )
    )


def run_config_editor(project_config_path: Path | None = None):
    global project_store, initial_project_text
    project_store = ProjectConfigStore(project_config_path)
    initial_project_text = load_project_editor_text(project_store)
    project_toml_editor.set_edit_text(initial_project_text)
    urwid.MainLoop(top, palette=[("reversed", "standout", "")]).run()


def load_project_editor_text(store: ProjectConfigStore) -> str:
    try:
        return store.load_text()
    except ProjectConfigError as error:
        return f"# {error}\n"


default_config = Configuration(_env_file="")
default_config_envs = set(dump_envs(default_config))
initial_envs = set(dump_envs(config))
project_store = ProjectConfigStore()
initial_project_text = load_project_editor_text(project_store)
project_toml_editor = urwid.Edit(edit_text=initial_project_text, multiline=True)
menu_top = menu(
    "KToolBox Configuration Editor",
    [
        sub_menu(
            "Edit",
            [
                sub_menu(
                    "API",
                    model_to_widgets(config.api),
                ),
                sub_menu(
                    "Downloader",
                    model_to_widgets(config.downloader),
                ),
                sub_menu(
                    "Job",
                    model_to_widgets(config.job),
                ),
                sub_menu(
                    "Logger",
                    model_to_widgets(config.logger),
                ),
                sub_menu(
                    "Project roster and blockers (TOML)",
                    [project_toml_editor],
                ),
                urwid.Divider(),
            ]
            + list(model_to_widgets(config, ["ssl_verify", "json_dump_indent", "use_uvloop"])),
        ),
        urwid.Divider(),
        menu_option(
            urwid.Button(
                "JSON Preview",
                lambda x: top.open_box(
                    sub_menu_with_menu_widget("JSON Preview", [urwid.Text(config.model_dump_json(indent=4))])[1]
                ),
            )
        ),
        menu_option(
            urwid.Button(
                "JSON Preview (Python Mode)",
                lambda x: top.open_box(
                    sub_menu_with_menu_widget(
                        "JSON Preview (Python Serialize Mode)",
                        [urwid.Text(pprint.pformat(config.model_dump(mode="python"), sort_dicts=False))],
                    )[1]
                ),
            )
        ),
        menu_option(
            urwid.Button(
                "DotEnv Preview (.env / prod.env)",
                lambda x: top.open_box(
                    sub_menu_with_menu_widget(
                        "DotEnv Preview (.env / prod.env)",
                        [
                            urwid.Text(
                                "\n".join(dump_modified_envs(dump_envs(config)))
                                or "Same as the default configuration, DotEnv will be left empty."
                            )
                        ],
                    )[1]
                ),
            )
        ),
        urwid.Divider(),
        sub_menu(
            "Save",
            [
                menu_option(urwid.Button("Save to '.env' / 'prod.env' file", on_save_dotenv)),
                menu_option(urwid.Button("Save project roster and blockers", on_save_project)),
            ],
        ),
        urwid.Divider(bottom=2),
        menu_option(
            urwid.Button(
                "Help", lambda x: webbrowser.open("https://ktoolbox.readthedocs.io/latest/configuration/guide/")
            )
        ),
        menu_option(urwid.Button("Exit", exit_program)),
        urwid.Divider(bottom=2),
        urwid.Text("For detailed information, please refer to https://ktoolbox.readthedocs.io", align=urwid.CENTER),
        urwid.Divider(),
        urwid.Text(__version__, align=urwid.CENTER),
    ],
)
top = CascadingBoxes(menu_top)
