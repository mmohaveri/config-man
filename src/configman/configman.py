import os
import json

from typing import Optional, Dict, Any, Callable, get_type_hints, Union, Type
from argparse import Namespace, Action, ArgumentParser

from glom import glom, assign

from .exceptions import InvalidConfigNameError, IncompatibleTypeError


PRIMITIVE_TYPES = (int, float, str, bool)


class ConfigMan(object):
    def __init__(self):
        self._config_file: str = ""
        self._envs: Dict[str][str] = {}
        self._args: Dict[str][str] = {}

    def set_config_file(self, file_name: str) -> None:
        self._config_file = file_name

    def set_env(self, config_name: str, env_name: str = None) -> None:
        if env_name is None:
            env_name = self._get_env_name(config_name)

        self._envs[env_name] = config_name

    def set_arg(self, config_name: str, *arg_name_or_flags: str, parser: ArgumentParser,
                action: Union[str, Type[Action]] = None,
                required: bool = None,
                help_str: str = None) -> None:
        arg_dest = arg_name_or_flags[0]
        uses_flag = False

        if arg_dest.startswith("--"):
            arg_dest = arg_dest[2:]
            uses_flag = True

        self._args[arg_dest] = config_name

        kwargs = {
            "dest": arg_dest,
            "type": self._get_type(config_name)
        }

        for arg, key in ((action, "action"), (required, "required"), (help_str, "help")):
            if arg is not None:
                kwargs[key] = arg

        if kwargs.get("action", None) is not None:
            del kwargs["type"]

        if uses_flag:
            parser.add_argument(*arg_name_or_flags, **kwargs)
        else:
            parser.add_argument(**kwargs)

    def set_auto_env(self, prefix: str = "") -> None:
        def func(attr_path: str, _: type) -> None:
            env_name = self._get_env_name(attr_path, prefix)
            self._envs[env_name] = attr_path

        self._run_func_for_all_premitives(func)

    def load(self, args: Namespace = None) -> None:
        self.load_from_env()
        self.load_from_file()
        self.load_from_args(args)

    def load_from_env(self) -> None:
        for env_name, full_conf_name in self._envs.items():
            env_val = os.getenv(env_name, None)

            if env_val is not None:
                conf_val = self._get_value_in_correct_type(full_conf_name, env_val)
                assign(self, full_conf_name, conf_val)

    def load_from_file(self) -> None:
        if self._config_file == "":
            return

        with open(self._config_file, "r") as f:
            config_dict = json.load(f)

        def func(attr_path: str, _: type) -> None:
            conf_val = glom(config_dict, attr_path, default=None)

            if conf_val is not None:
                assign(self, attr_path, conf_val)

        self._run_func_for_all_premitives(func)

    def load_from_args(self, args: Optional[Namespace]) -> None:
        for arg_name, full_conf_name in self._args.items():
            arg_val = getattr(args, arg_name, None)

            if arg_val is not None:
                conf_val = self._get_value_in_correct_type(full_conf_name, arg_val)
                assign(self, full_conf_name, conf_val)

    def to_dict(self) -> Dict[str, Any]:
        result = {}

        def func(attr_path: str, attr_type: type) -> None:
            conf_val = glom(self, attr_path, default=attr_type())
            assign(result, attr_path, conf_val, missing=dict)

        self._run_func_for_all_premitives(func)

        return result

    def _get_value_in_correct_type(self, full_conf_name: str, value: Any) -> Any:
        conf_type = self._get_type(full_conf_name)
        try:
            return conf_type(value)
        except ValueError as e:
            raise IncompatibleTypeError(f"can not cast types: {e}")

    def _get_type(self, full_conf_name: str) -> type:
        conf_name_parts = full_conf_name.split(".")
        conf_parent = ".".join(conf_name_parts[:-1])
        conf_name = conf_name_parts[-1]

        parent_obj = self if conf_parent == "" else glom(self, conf_parent)

        type_hints = get_type_hints(parent_obj)

        try:
            conf_type = type_hints[conf_name]
        except KeyError as e:
            raise InvalidConfigNameError(f"bad config name: {e}")

        return conf_type

    def _get_env_name(self, path: str, prefix: str = None) -> str:
        path_parts = path.split(".")

        if prefix is not None:
            path_parts.insert(0, prefix)

        return "__".join(path_parts)

    def _run_func_for_all_premitives(self, func: Callable[[str, type], None]):
        objects = [(self, "")]

        while len(objects) != 0:
            obj, obj_path = objects.pop(0)

            for attr_name, attr_type in get_type_hints(obj).items():
                attr_path = f"{obj_path}.{attr_name}" if obj_path != "" else attr_name

                if attr_type not in PRIMITIVE_TYPES:
                    attr = getattr(obj, attr_name)
                    objects.append((attr, attr_path))
                else:
                    func(attr_path, attr_type)
