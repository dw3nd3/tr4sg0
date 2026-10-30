<h1 align="center">tr4sg0</h1>

An extensible browser for the [dw3nd3 web](https://github.com/dw3nd3/d33-specification/wiki) written in python. Reference implementation of the d33 specification.

## Usage

Install it:

```bash
git clone https://github.com/dw3nd3/tr4sg0
cd tr4sg0
pip install .
```
Launch it:
```bash
t40 https://github.com/dw3nd3/d33-specification/wiki/1-Tutorial
```
You can also open local files:
```bash
t40 file-with-a-hidden-room.html
```
Use the dev mode (`-d` or `--dev`) to enable hot reload. This is useful to edit rooms live.

## Additional features

Instead of using it as a browser you can use it to print minified or expanded room definitions, in order to embed or inspect them more easily.

```bash
t40 --minify file-with-a-big-room.html
t40 --expand file-with-a-small-room.html
```

Files are not edited in-situ, the output goes to stdout.

## Make a plugin

Until a fully fledged developer documentation comes out, the files inside `t40/plugin` can be used as a reference to implement plugins for tr4sg0.

## Contributors

This section is empty for now.

## License

t40 - An extensible browser for the dw3nd3 web.

Copyright (C) 2026 MiguelMJ

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.