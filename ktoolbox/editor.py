from __future__ import annotations

import pprint
import warnings
from pathlib import Path
from typing import get_args, Literal, Union, TypeVar, Optional, Tuple, Any, Callable, Hashable, Iterable, NoReturn, \
    List, Generator

import urwid
from pydantic import BaseModel
# noinspection PyProtectedMember
from pydantic._internal._model_construction import ModelMetaclass

from ktoolbox.configuration import config, Configuration

warnings.filterwarnings("ignore")

_T = TypeVar("_T")
__all__ = ["EditWithSignalWidget", "CascadingBoxes", "run_config_editor"]


class EditWithSignalWidget(urwid.Edit):
    """
    Custom ``urwid.Edit``, support callback when changed.
    """

    def __init__(
            self,
            *args,
            on_state_change: Optional[Callable[[EditWithSignalWidget, _T], Any]],
            user_data: Optional[_T],
            **kwargs
    ) -> None:
        self.__on_state_change = on_state_change
        self.__user_data = user_data
        super().__init__(*args, **kwargs)

    def keypress(self, size: Tuple[int], key: str) -> Union[str, None]:
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
            urwid.LineBox(box),
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

    def back(self) -> Optional[NoReturn]:
        self.original_widget = self.original_widget[0]
        self.box_level -= 1
        return None

    def exit(self):
        raise urwid.ExitMainLoop()

    def keypress(self, size, key: str) -> Union[str, NoReturn, None]:
        if key == "esc":
            if self.box_level > 1:
                self.back()
            else:
                exit_program()
        return super().keypress(size, key)


def dump_envs(model: BaseModel) -> List[str]:
    """Dump environment variables, with no Env prefix"""
    envs = []
    for field in model.model_fields:
        value = model.__getattribute__(field)
        if isinstance(value, BaseModel):
            for env in dump_envs(value):
                envs.append(f"{field.upper()}__{env}")
        else:
            envs.append(f"{field.upper()}={model.__pydantic_serializer__.to_python(value, mode='json')}")
    return envs


def dump_modified_envs(envs: List[str]) -> List[str]:
    """
    Dump modified environment variables, with Env prefix

    :param envs: Current Envs
    """
    return sorted([
        f"KTOOLBOX_{env}" for env in set(envs) - default_config_envs
    ])


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


def has_changed() -> bool:
    return bool(set(dump_envs(config)) - initial_envs)


def menu_button(
        caption: Union[str, Tuple[Hashable, str], List[Union[str, Tuple[Hashable, str]]]],
        callback: Callable[[urwid.Button], Any],
) -> urwid.AttrMap:
    """The button contains in a menu"""
    button = urwid.Button(caption, on_press=callback)
    return urwid.AttrMap(button, None, focus_map="reversed")


def sub_menu(
        caption: Union[str, Tuple[Hashable, str], List[Union[str, Tuple[Hashable, str]]]],
        choices: Iterable[urwid.Widget],
) -> urwid.Widget:
    contents = menu(
        caption,
        list(choices) + [urwid.Divider(bottom=2), menu_button("Back", lambda x: top.back())]
    )

    def open_menu(_: urwid.Button) -> None:
        return top.open_box(contents)

    return menu_button([caption, "..."], open_menu)


def menu(
        title: Union[str, Tuple[Hashable, str], List[Union[str, Tuple[Hashable, str]]]],
        choices: Iterable[urwid.Widget],
) -> urwid.ListBox:
    body = [urwid.Text(title, align=urwid.Align.CENTER), urwid.Divider(), *choices]
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))


def on_radio_button_change(_: urwid.RadioButton, state: bool, user_data: Tuple[BaseModel, str, Any]):
    if state:
        model, field, value = user_data
        model.__setattr__(field, value)


def on_checkbox_change(_: urwid.CheckBox, state: bool, user_data: Tuple[BaseModel, str]):
    model, field = user_data
    model.__setattr__(field, state)


def on_edit_change(widget: urwid.EditWithSignalWidget, user_data: Tuple[BaseModel, str, Iterable[type]]):
    model, field, annotation = user_data
    for field_type in annotation:
        try:
            model.__setattr__(field, field_type(widget.get_edit_text()))
        except ValueError:
            continue
        else:
            break


def on_save_dotenv(_: urwid.Button):
    if has_changed():
        pile = urwid.Pile([
            urwid.Text("Your changes have been saved."),
            urwid.Divider(),
            menu_button("OK", lambda x: top.back()),
        ])
        try:
            save_dotenv()
        except Exception as e:
            pile = urwid.Pile([
                urwid.Text("Unable to save changes!"),
                urwid.Divider(),
                urwid.Text(f"{type(e).__name__}: {e}"),
                urwid.Divider(),
                menu_button("OK", lambda x: top.back()),
            ])
    else:
        pile = urwid.Pile([
            urwid.Text("Nothing has changed, no need to save."),
            urwid.Divider(),
            menu_button("OK", lambda x: top.back()),
        ])
    top.open_box(urwid.Filler(pile))


def exit_program(_: urwid.Button = None) -> Optional[NoReturn]:
    if has_changed():
        top.open_box(
            urwid.Filler(
                urwid.Pile([
                    urwid.Text("Any unsaved changes will be lost. Are you sure you want to EXIT?"),
                    urwid.Divider(),
                    menu_button("NO", lambda x: top.back()),
                    menu_button("YES", lambda x: top.exit()),
                ])
            )
        )
    else:
        top.exit()


def model_to_widgets(model: BaseModel, fields: Iterable[str] = None) -> Generator[urwid.Widget, Any, None]:
    """
    Generate urwid widgets for Pydantic model

    :param model: Pydantic model
    :param fields: Only generate for these fields, default to all fields.
    """
    for field, field_info in model.model_fields.items():
        if fields is not None and field not in fields:
            continue
        origin_annotation = getattr(field_info.annotation, '__origin__', None)
        annotation = get_args(field_info.annotation) if origin_annotation is Union else [field_info.annotation]

        if origin_annotation is Literal:
            radio_buttons = []
            for value in get_args(field_info.annotation):
                urwid.RadioButton(
                    radio_buttons,
                    str(value),
                    model.__getattribute__(field) == value,
                    on_radio_button_change,
                    (model, field, value)
                )
            yield sub_menu(field, radio_buttons)
        elif bool in annotation:
            yield urwid.CheckBox(
                field,
                model.__getattribute__(field),
                on_state_change=on_checkbox_change,
                user_data=(model, field)
            )
        elif any(map(lambda x: x in annotation, [str, int, float, Path])):
            yield urwid.Columns([
                urwid.Text(field, align=urwid.Align.LEFT),
                EditWithSignalWidget(
                    edit_text=str(model.__getattribute__(field)),
                    align=urwid.Align.RIGHT,
                    on_state_change=on_edit_change,
                    user_data=(model, field, annotation)
                )
            ])
        elif isinstance(field_info.annotation, ModelMetaclass):
            yield sub_menu(field, model_to_widgets(model.__getattribute__(field)))
        else:
            yield sub_menu(
                field,
                [urwid.Text(
                    f"This option ({repr(field_info.annotation)}) is currently not supported for editing in "
                    "the graphical interface; please edit it in the '.env' or 'prod.env' file in the working directory."
                )]
            )


def run_config_editor():
    urwid.MainLoop(top, palette=[("reversed", "standout", "")]).run()


default_config = Configuration()
default_config_envs = set(dump_envs(default_config))
initial_envs = set(dump_envs(config))
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
                urwid.Divider()
            ] + list(model_to_widgets(config, ["ssl_verify", "json_dump_indent", "use_uvloop"])),
        ),
        menu_button(
            "JSON Preview",
            lambda x: top.open_box(menu(
                "JSON",
                [
                    urwid.Text(
                        pprint.pformat(config.model_dump(mode="python"))
                    )
                ]
            )),
        ),
        menu_button(
            "DotEnv Preview",
            lambda x: top.open_box(menu(
                "DotEnv",
                [
                    urwid.Text(
                        "\n".join(dump_modified_envs(dump_envs(config))) or "Same as the default configuration, "
                                                                            "DotEnv will be left empty."
                    )
                ]
            )),
        ),
        sub_menu(
            "Save",
            [
                menu_button(
                    "Save to '.env' / 'prod.env' file",
                    on_save_dotenv
                )
            ],
        ),
        urwid.Divider(bottom=2),
        menu_button("Exit", exit_program),
        urwid.Divider(bottom=2),
        urwid.Text(
            "For detailed information, please refer to "
            "https://ktoolbox.readthedocs.io/latest/configuration/reference/",
            align=urwid.Align.CENTER
        )
    ],
)
top = CascadingBoxes(menu_top)
