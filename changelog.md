# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [git] - 2020-04-07
(Conform poikilos.py to the mtanalyze version.)
### Added
- `get_initial_value_from_conf`
- `has_dups`
- `find_dup`
- `get_list_from_hex`
- `get_entries_modified_count`
- `singular_or_plural`
- `vec2_not_in`

### Changed
- Conform to PEP8.
- Rename functions.
  - `get_tuple_from_notation` to `s_to_tuple`
  - `load_var_or_ask_console_input` to `load_var`
    (make `interactive_enable` optional)
  - (and more)
- Use `deepcopy` to copy a dict.
- Make use of `input` (formerly `raw_input`) and division compatible
  with Python 2 or 3.

## [git] - 2020-04-07
### Changed
- Rename a developer-specific file to poikilos.py.


## [git] - 2020-04-07
### Changed
- Move changes from readme.md to this Changelog.


## [git] - 2020-04-07
### Changed
- Move changes from readme.md to this Changelog.


## [git] - 2015-11-33
### Added
- parser_op_remove_net_framework: Removes 'object' inheritance


## [git] 2015-11-30
### Added
- Insert note into resulting code that it was processed by this program.

### Fixed
- Always use \n for newline, since python automatically changes
  instances of \n to os.sep and therefore would change os.sep to \r\r\n
- parser_op_remove_net_framework: Use WriteLine("\n") instead of
  WriteLine(+"\n") for streamwriter.WriteLine() with no parameters.
- parser_op_remove_net_framework: Use print("") instead of print() to
  replace Console.Error.WriteLine() with no parameters.
- parser_op_remove_net_framework: Use sys.stderr.write("\n") instead of
  sys.stderr.write(), write("\n"), and flush() to replace
  Console.Error.WriteLine() with no parameters.
