# Config-Man

Config-Man is a configuration manager for python projects. It helps you handle your project's runtime configurations in
an easy and clean way. It also supports multiple config sources like **json file**, **environment variables**,
**hard coded defaults**, etc.

## Installation

Simply install using pip:

```bash
pip install config-man
```

Keep in mind that Config-Man uses [Python type annotations (PEP 484)](https://www.python.org/dev/peps/pep-0484/), and
[f-Strings (PEP 498)](https://www.python.org/dev/peps/pep-0498/) so you'll need Python 3.6 or higher.

## Usage

### Defining config

In Config-Man, configuration is defined using a class subclassed from `configman.ConfigMan`.
In this class, configurations are static members with [type hints](https://docs.python.org/3/library/typing.html).

Currently Config-Man only supports primitives (bool, int, float, str) and subtypes of `configman.ConfigMan`:

```python
from configman import ConfigMan


class ServerConfig(ConfigMan):
    port: int
    log_level: str
```

For creation of nested configs (for more organized code) simply do the following:

```python
from configman import ConfigMan


class LoggingConfig(ConfigMan):
    log_level: str


class Config(ConfigMan):
    port: int
    logging: LoggingConfig
```

You can add default values during definition simply by assigning a value to it:

```python
from configman import ConfigMan


class ServerConfig(ConfigMan):
    port: int = 80
    log_level: str = "error"
```

### Loading config

First of all, you need to create an instance of your main config:

```python
config = Config()
```

#### Config Sources

Then you need to tell it where to look for configurations. Config-Man supports multiple config sources. Currently it
supports hard-coded, environment variables, json config files and arguments. If there is a config source that you need
and Config-Man does not support feel free to open an issue.

##### 1. hard-coded

Apart from the default value you set during config definition, you can add an other default value during config load
process simply by assigning the default value to it:

```python
config.port = 443
```

##### 2. Environment Variables

Config-Man can read configurations from environment variables.

One way to use env as a source is to assign a specific env to a config:

```python
config.set_env("logging.log_level")
```

By default all dots "." in a variable path will be replaced by double under scores "\_\_", So `logging.log_level` will
be filled by the value of `logging__log_level`.

You can also set a specific name for the env:

```python
config.set_env("logging.log_level", "LOG_LEVEL")
```

Another way is to tell Config-Man to load all possible configs from env

```python
config.set_auto_env()
```

In order to avoid collisions between different programs, you can add a prefix to all envs (in auto_env):

```python
config.set_auto_env("MY_PROGRAM")
```

Now when you load the config, Config-Man tries to read `MY_PROGRAM__PORT` and `MY_PROGRAM__logging__log_level` and put
their values into the corresponding variables.

##### 3. Config File

Currently Config-Man only supports json config files. You can set config file using:

```python
config.set_config_file("config.json")
```

##### 4. Arguments

You can tell Config-Man to read a specific config from arguments using:

```python
import argparse

parser = argparse.ArgumentParser()
config.set_arg("logging.log_level", "log_level", parser)
```

Config-Man automatically adds needed argument to parser. If necessary, you can also define `action`, `help`, and `required`.

#### Loading Configs

Finally you can load the config itself by calling:

```python
config.load()
```

By default configs from file overrides config from env and config from args overrides everything else.

If you like to do things in a different way, you can run `load_from_env`, `load_from_file` and `load_from_args` by
yourself in any order to desire.

### Creating an empty config file

If you wish to create an empty config file, you can do so using `to_dict`:

```python
import json

config = Config()

with open("config.json", "w") as f:
    json.dump(f, config.to_dict(), indent=2)
```

This way config.json will contain an empty config ready for you to fill.

### Full example

```python
import argparse

from configman import ConfigMan


class LoggingConfig(ConfigMan):
    log_level: str = "error"


class Config(ConfigMan):
    port: int
    logging: LoggingConfig


config = Config()
parser = argparse.ArgumentParser()

config.port = 443
config.set_auto_env("MY_PROGRAM")
config.set_env("logging.log_level", "LOG_LEVEL")
config.set_config_file("config.json")
config.set_arg("logging.log_level", "--log_level", "-l", parser)

args = parser.parse_args()

config.load(args)
```
