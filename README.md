# ProyectoReal LLC Project

The clean, fast and right way to start a new Django `4.1.4` powered website.

## Getting Started

```bash
$ Python3 -m venv .venv # hidden venv files
$ source .venv/bin/activate
$ pip install -r requirements.txt
# You may want to change the name `realproject`.
$ django-admin startproject realproject # or clone the repository with git@github.com:JesusAlmirco/realproject.git
$ cd realproject/

$ python manage.py makemigrations
$ python manage.py migrate
$ python manage.py runserver
```

## Features

* App scaffolding (commands, templatetags, statics, media files, etc).
* Split settings in two files. `settings.py` for specific environment settings (localhost, production, etc). `realproject/settings.py` for core settings.

## Contributing

I love contributions, so please feel free to fix bugs, improve things, provide documentation. Just send a pull request.