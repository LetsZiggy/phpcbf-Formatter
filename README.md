# phpcbf Formatter for Sublime Text

*Please note the plugin hasn't been submitted to [packagecontrol.io](https://packagecontrol.io/). Thus has to be installed manually.*

<br>

### Installation

#### Installing plugin

- `Package Control: Add Repository` Method (Recommended)
	1. Open `Command Palette` (Default: `Primary + Shift + p`)
	2. `Package Control: Add Repository`
	3. `https://raw.githubusercontent.com/LetsZiggy/phpcbf-Formatter/main/repository-package.json`
	4. Open `Command Palette`
	5. `Package Control: Install Package`
	6. `phpcbf-Formatter`
- "Manual" Method (Requires manual update)
	1. Download this repository through `Download ZIP`
	2. Rename folder to `phpcbf-Formatter`
	3. Move folder to `[SublimeText]/Packages` folder
		- To access `[SublimeText]/Packages` folder:
			1. Open/Restart `Sublime Text`
			2. Open the `Command Palette` (Default: `Primary + Shift + p`)
			3. `Preferences: Browse Packages`
	4. Restart `Sublime Text`

---

### Commands

#### Command palette:

- `phpcbf Formatter: Format this file`

#### Shortcut key:

* Linux/Windows: `Ctrl + Shift + ;`
* Mac: `Cmd + Shift + ;`

---

### Usage

#### Using Default Settings ({ format_on_save: false })

1. Save current changes
	- Formatting will only be applied to the saved file and _**not the current buffer**_
2. Use one of the available commands to run phpcbf-Formatter

---

### Configuring Settings

#### To access and modify settings file

Go to `Preferences -> Package Settings -> phpcbf-Formatter -> Settings`

#### To override settings per project basis

To override global plugin configuration for a specific project, add a settings object with a `phpcbf-Formatter` key in your `.sublime-project`. This file is accessible via `Project -> Edit Project`.

```javascript
/* EXAMPLE */
{
  "folders": [
    {
      "path": ".",
    },
  ],
  "settings": {
    "phpcbf-Formatter": {
      "format_on_save": true,
    },
  },
}
```

#### Default settings

```javascript
{
  // Simply using `php` without specifying a path sometimes doesn't work :(
  // https://www.php.net/manual/en/install.php
  // If these are false, we'll invoke the phpcbf binary directly.
  "php_path": {
    "windows": "php.exe",
    "linux": "/usr/bin/php",
    "osx": "/usr/local/bin/php",
  },

  // The location to search for a locally installed phpcbf package
  // These are all relative paths to a project's directory
  // If this is not found or are false, it will try to fallback to a global package
  // (see "phpcbf_path" below)
  "local_phpcbf_path": {
    "windows": "vendor/bin/phpcbf",
    "linux": "vendor/bin/phpcbf",
    "osx": "vendor/bin/phpcbf",
  },

  // The location of the globally installed phpcbf package to use as a fallback
  "phpcbf_path": {
    "windows": "%APPDATA%/Roaming/Composer/vendor/bin/phpcbf",
    "linux": "~/.composer/vendor/bin/phpcbf",
    "osx": "~/.composer/vendor/bin/phpcbf",
  },

  // Specify this path to an phpcbf standard file to override the default behavior
  // Passed to phpcbf as --standard. Read more here:
  // https://github.com/squizlabs/PHP_CodeSniffer/wiki/Configuration-Options
  // If an absolute path is provided, it will use as is.
  // Failing either, it will skip the standard file
  "config_path": "",

  // Pass additional arguments to phpcbf.
  // Read more here: https://cs.symfony.com/doc/usage.html
  // Please note that "-v | -vv | -vvv | -q" args will be edited (see `debug` below)
  "extra_args": [
    "-l",
  ],

  // Automatically format when a file is saved
  "format_on_save": false,

  // Only attempt to format files with whitelisted extensions on save.
  // Leave empty to disable the check
  "format_on_save_extensions": [ "php" ],

  // Logs phpcbf output messages to console when set to true
  // `extra_args` will be edited as below if `debug` set to:
  //   - `false`:
  //     - "-v | -vv | -vvv" will be removed
  //     - "-q" will be added
  //   - `true`:
  //     - "-q" will be removed
  //     - "-vvv" will be added
  "debug": false,
}
```
