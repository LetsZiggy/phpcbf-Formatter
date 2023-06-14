from os import path as os_path
from pathlib import Path as pathlib_Path
from subprocess import PIPE, Popen
from typing import Any, Dict, Literal, Tuple, TypedDict, Union

import sublime
import sublime_plugin

PROJECT_NAME = "phpcbf-Formatter"
SETTINGS_FILE = f"{PROJECT_NAME}.sublime-settings"
PLATFORM = sublime.platform()
ARCHITECTURE = sublime.arch()
KEYMAP_FILE = f"Default ({PLATFORM}).sublime-keymap"
IS_WINDOWS = PLATFORM == "windows"
CODE_COMMAND_NOT_FOUND = 127


class SettingsData(TypedDict):
	variables: Dict[str, Any]
	config: Dict[str, Any]


class Settings:
	data: SettingsData = {
		"variables": {},
		"config": {},
	}

	@classmethod
	def set_settings(cls, view: sublime.View, variables: Dict[str, str]) -> None:
		settings_default = sublime.load_settings(SETTINGS_FILE).to_dict()
		settings_default = {k: v for k, v in Settings.flatten_dict(settings_default)}
		cls.data["config"] = settings_default

		settings_user = view.settings().to_dict()
		settings_user = {k: v for k, v in settings_user.items() if "phpcbf-Formatter" in k}
		settings_user = {k[17:]: v for k, v in Settings.flatten_dict(settings_user)}
		cls.data["config"].update(settings_user)

		variables.update({k: v for k, v in cls.data["config"].items() if "." not in k and isinstance(v, str)})
		cls.data["variables"] = variables

		for k, v in cls.data["config"].items():
			if isinstance(v, str) and "${" in v and "}" in v:
				v = sublime.expand_variables(v, cls.data["variables"])
				cls.data["config"][k] = v

			if isinstance(v, str) and "path" in k:
				v = os_path.normpath(os_path.expanduser(v))
				cls.data["config"][k] = v

	@classmethod
	def flatten_dict(cls, obj: Dict[str, Any], keystring: str = ""):
		if isinstance(obj, dict):
			keystring = f"{keystring}." if keystring else keystring

			for k in obj:
				yield from Settings.flatten_dict(obj[k], keystring + str(k))
		else:
			yield keystring, obj

	@classmethod
	def verify_settings(cls) -> None:
		php_path_exist: Union[Literal[True], Tuple[str, str]] = True
		phpcbf_path_exist: Dict[Literal["local", "fallback"], Union[Literal[True], Tuple[str, str]]] = {
			"local": True,
			"fallback": True,
		}

		for k, v in cls.data["config"].items():
			if isinstance(v, str) and "php_" in k and "path" in k and PLATFORM.lower() in k:
				php_path_exist = True if os_path.exists(v) else (k, v)

			if isinstance(v, str) and "phpcbf_" in k and "path" in k and PLATFORM.lower() in k:
				if "local" in k:
					phpcbf_path_exist["local"] = True if os_path.exists(v) else (k, v)

				if "local" not in k:
					phpcbf_path_exist["fallback"] = True if os_path.exists(v) else (k, v)

		if php_path_exist is not True:
			sublime.error_message("php path does not exist. See console output.")
			raise Exception(f"\n>>> `php_path` does not exist: {php_path_exist[0]} -> {php_path_exist[1]}")

		if phpcbf_path_exist["local"] is not True and phpcbf_path_exist["fallback"] is not True:
			sublime.error_message("phpcbf path does not exist. See console output.")
			raise Exception(
				"\n>>> `local_phpcbf_path` does not exist: "
				+ f"{phpcbf_path_exist['local'][0]} -> {phpcbf_path_exist['local'][1]}"
				+ "\n>>> `phpcbf_path` does not exist: "
				+ f"{phpcbf_path_exist['fallback'][0]} -> {phpcbf_path_exist['fallback'][1]}"
			)

	@staticmethod
	def get_settings(view: Union[sublime.View, None]) -> SettingsData:
		variables = view.window().extract_variables()

		if view is not None and (
			variables["file_extension"] == "sublime-project"
			or len(Settings.data["variables"]) == 0
			or len(Settings.data["config"]) == 0
			or Settings.data["variables"]["file_extension"] != variables["file_extension"]
		):
			Settings.set_settings(view, variables)

		return Settings.data


class PhpcbfFormatterEventListeners(sublime_plugin.EventListener):
	@staticmethod
	def should_run_command(view: sublime.View, settings: SettingsData) -> bool:
		extensions = settings["config"]["format_on_save_extensions"]
		extension = settings["variables"]["file_extension"] or settings["variables"]["file_name"].split(".")[-1]

		return not extensions or extension in extensions

	@staticmethod
	def on_pre_save(view: sublime.View) -> None:
		settings = Settings.get_settings(view)

		if settings["config"]["format_on_save"] and PhpcbfFormatterEventListeners.should_run_command(view, settings):
			view.run_command("format_phpcbf")


class FormatPhpcbfCommand(sublime_plugin.TextCommand):
	def run(self, edit) -> None:
		settings = Settings.get_settings(self.view)

		if not PhpcbfFormatterEventListeners.should_run_command(self.view, settings):
			print(">>> phpcbf-Formatter: File type not supported")
			return
		else:
			Settings.verify_settings()

		viewport_position = self.view.viewport_position()
		selections = list(self.view.sel())
		folded_regions = [self.view.substr(region) for region in self.view.folded_regions()]

		cmd_phpcbf = [
			settings["config"][f"local_phpcbf_path.{PLATFORM}".lower()]
			or settings["config"][f"phpcbf_path.{PLATFORM}".lower()]
		]
		is_bin_cmd_phpcbf = len(pathlib_Path(cmd_phpcbf[0]).suffix) == 0
		cmd_php = [settings["config"][f"php_path.{PLATFORM}".lower()]] if not is_bin_cmd_phpcbf else []
		cmd_config = [f"--standard={settings['config']['config_path']}"] if settings["config"]["config_path"] else []
		cmd_extra = list(
			filter(
				lambda v: v not in {"-v", "-vv", "-vvv", "-q"},
				settings["config"]["extra_args"],
			)
		) + (["-vvv"] if settings["config"]["debug"] else ["-q"])
		cmd_filename = [f"--stdin-path={settings['variables']['file']}"]
		cmd = [v for v in (cmd_php + cmd_phpcbf + cmd_config + cmd_extra + cmd_filename) if len(v)]

		buffer_region = sublime.Region(0, self.view.size())
		content = self.view.substr(buffer_region)
		content = content.encode("utf-8")

		try:
			p = Popen(
				cmd + ["-"],
				stdout=PIPE,
				stdin=PIPE,
				stderr=PIPE,
				cwd=settings["variables"]["project_path"] or settings["variables"]["file_path"],
				shell=IS_WINDOWS,
			)
		except OSError:
			sublime.error_message("Couldn't find php. See console output.")
			raise Exception(
				"\n>>> Couldn't find php. Make sure it's in your $PATH by running `php -v` in your command-line."
			)

		stdout, stderr = p.communicate(input=content)
		stdout = stdout.decode("utf-8")
		stderr = stderr.decode("utf-8")

		if stderr and settings["config"]["debug"]:
			print(">>> phpcbf-Formatter:", " ".join(cmd + ["- <BUFFER>"]))
			print(">>> Debug:", stderr)
		elif stderr:
			sublime.error_message(stderr)
			raise Exception(f"Error: {stderr}")
		elif p.returncode == CODE_COMMAND_NOT_FOUND:
			sublime.error_message(stderr or stdout)
			raise Exception(f"Error: {(stderr or stdout)}")
		elif stdout is None or len(stdout) < 1:
			return
		elif stdout != content:
			self.view.replace(edit, buffer_region, stdout)

			if not settings["config"]["debug"]:
				print(">>> phpcbf-Formatter (success):", " ".join(cmd + ["- <BUFFER>"]))

		# Reapply code folds
		self.view.unfold(sublime.Region(0, len(stdout)))
		region_start = -1
		region_end = 0

		for region in folded_regions:
			try:
				region_start = stdout.find(region, region_end)
			finally:
				if region_start > -1:
					region_end = region_start + len(region)
					self.view.fold(sublime.Region(region_start, region_end))

		# Reapply viewport position
		self.view.set_viewport_position((0, 0), False)
		self.view.set_viewport_position(viewport_position, False)
		self.view.sel().clear()

		# Reapply cursor position and buffer selections
		for selection in selections:
			self.view.sel().add(selection)
