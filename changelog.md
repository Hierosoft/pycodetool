# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).


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
