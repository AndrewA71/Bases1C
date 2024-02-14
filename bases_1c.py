import os
import re
from pathlib import Path
import shutil
import argparse
from dataclasses import dataclass
from operator import attrgetter
from _version import __version__
from enum import StrEnum


@dataclass
class BaseInfo:
    id: str
    name: str = ""
    common: bool = False
    connect: str = ""
    folder: str = ""
    roaming_path: Path = None
    roaming_size: int = 0
    local_path: Path = None
    local_size: int = 0
    size: int = 0

    def __post_init__(self):
        self.size = self.roaming_size + self.local_size


class CompareType(StrEnum):
    Any = 'any',
    Start = 'start',
    Full = 'full'


field_list = ['id', 'name', 'connect', 'folder', 'common', 'roaming_path', 'roaming_size', 'local_path',
              'local_size', 'size']


class CompareParameter:
    def __init__(self, pattern: str, is_regex: bool, compare_type: CompareType, ignore_case: bool):
        self.is_regex = is_regex
        self.compare_type = compare_type
        self.ignore_case = False
        if is_regex:
            self.pattern = re.compile(pattern, flags=re.IGNORECASE if ignore_case else 0)
        else:
            self.pattern = pattern.lower() if ignore_case else pattern
            self.ignore_case = ignore_case

    def compare(self, text: str) -> bool:
        if self.ignore_case:
            text = text.lower()
        match self.compare_type:
            case CompareType.Any:
                return re.search(self.pattern, text) if self.is_regex else (self.pattern in text)
            case CompareType.Start:
                return re.match(self.pattern, text) if self.is_regex else (text.startswith(self.pattern))
            case CompareType.Full:
                return re.fullmatch(self.pattern, text) if self.is_regex else (text == self.pattern)


def get_bases_info(file_name: Path | str, is_common: bool) -> dict:
    bases_info = {}
    base_info = None
    base_id = None
    base_pattern = re.compile(r'\[(.*)]')
    value_pattern = re.compile(r'(\w+)=(.*)')
    with open(file_name, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.search(base_pattern, line)
            if m:
                if base_id:
                    bases_info[base_id] = base_info
                    base_id = None
                base_info = {'name': m.group(1), 'common': is_common}
                is_base = False
            else:
                if m := re.search(value_pattern, line):
                    match m.group(1):
                        case 'ID':
                            if is_base:
                                base_info['id'] = m.group(2)
                                base_id = m.group(2)
                        case 'Folder':
                            base_info['folder'] = m.group(2)
                        case 'Connect':
                            base_info['connect'] = m.group(2)
                            is_base = True
        if base_id:
            bases_info[base_id] = base_info
    return bases_info


def get_all_bases_info() -> dict:
    bases_info = get_bases_info(os.path.expandvars(r'%APPDATA%\1C\1CEStart\ibases.v8i'), False)
    common_info_bases_cfg = Path(os.path.expandvars(r'%APPDATA%\1C\1CEStart\1CEStart.cfg'))
    if common_info_bases_cfg.is_file():
        with open(common_info_bases_cfg, "r", encoding='utf-16-le') as f:
            for line in f:
                line = line.strip().strip('\n')
                if line.startswith('CommonInfoBases='):
                    common_info_bases = Path(line.split('=')[1])
                    if common_info_bases.is_file():
                        for key, value in get_bases_info(common_info_bases, True).items():
                            if key in bases_info:
                                bases_info[key]['common'] = True
                            else:
                                bases_info[key] = value
    return bases_info


def get_bases_path(path_list: list[Path], prefix: str) -> dict:
    return {
        f.name: {'id': f.name, f'{prefix}_path': f,
                 f'{prefix}_size': sum([s.stat().st_size for s in f.rglob('*') if s.is_file()])}
        for path in filter(lambda x: x.exists(), path_list)
        for f in filter(lambda x: (x.is_dir() and
                                   x.match('????????-????-????-????-????????????') and
                                   x.name != '00000000-0000-0000-0000-000000000000'), path.iterdir())
    }


def clear_cache(bases: list[BaseInfo], clear_local: bool, clear_roaming: bool) -> None:
    path_types = []
    if clear_local:
        path_types.append('local_path')
    if clear_roaming:
        path_types.append('roaming_path')
    for base_info in bases:
        for path_type in path_types:
            path = base_info.__getattribute__(path_type)
            if path and path.is_dir():
                print(f'Delete dir {base_info.__getattribute__(path_type)}...', end='')
                try:
                    shutil.rmtree(base_info.__getattribute__(path_type))
                    print(' - Ok!')
                except Exception as e:
                    print(' - Error!')
                    print(e)


def base_filter(base_info: BaseInfo, args: argparse.Namespace) -> bool:
    if args.id and base_info.id not in args.id:
        return False
    if args.name:
        return args.name.compare(base_info.name)
    if 'cache' in args and args.cache is not None:
        if (base_info.roaming_path is not None or base_info.local_path is not None) != args.cache:
            return False
    if 'base' in args and args.base is not None:
        if (base_info.name is not None) != args.base:
            return False
    if 'no_base' in args and args.no_base:
        if base_info.name is not None:
            return False
    return True


def quote_delimiter(text: str, delimiter: str, quote: str = '"') -> str:
    result = text
    if quote and delimiter in text:
        result = quote + result.replace(quote, quote + quote) + quote
    return result


def get_args() -> argparse.Namespace:
    def add_name_group(argument_parser: argparse.ArgumentParser):
        name_group = argument_parser.add_argument_group('Name filter')
        name_group.add_argument('--name',
                                help='Filter a bases with name')
        name_group.add_argument('--regexp', action='store_true',
                                help='Use regexp')
        name_group.add_argument('--ignore-case', action='store_true',
                                help='Ignore case')
        choices = [x.value for x in CompareType]
        name_group.add_argument('--compare-type', choices=choices, default=choices[0],
                                help='Compare type')

    parser = argparse.ArgumentParser(description=f'1C bases tool, v{__version__}')
    parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {__version__}')
    subparsers = parser.add_subparsers(dest='command')
    subparser = subparsers.add_parser('list', help='list bases')
    default_fields = ['id', 'name']
    default_order = ['name']
    subparser.add_argument('--fields', nargs='*', choices=field_list, default=default_fields,
                           help='Fields to show, empty parameter for show all fields')
    subparser.add_argument('--order', nargs='*', choices=field_list, default=default_order,
                           help='Fields to sort the list, empty parameter to cancel sorting')
    subparser.add_argument('--delimiter', default=';',
                           help='Field delimiter')
    subparser.add_argument('--quote', default='"',
                           help='Quote delimiter char')
    subparser.add_argument('--id', nargs='*',
                           help='Filter a bases with IDs')
    subparser.add_argument('--cache', action=argparse.BooleanOptionalAction,
                           help='Filter a bases [with/without] disk cache')
    subparser.add_argument('--base', action=argparse.BooleanOptionalAction,
                           help='Filter a bases that [in/not in] the ibases.v8i file')
    add_name_group(subparser)

    subparser = subparsers.add_parser('clear', help='clear bases cache')
    subparser.add_argument('--local', action=argparse.BooleanOptionalAction, default=True,
                           help='Clear/not clear local cache')
    subparser.add_argument('--roaming', action=argparse.BooleanOptionalAction, default=True,
                           help='Clear/not clear roaming cache')
    subparser.add_argument('--id', nargs='*',
                           help='Filter a bases with IDs')
    subparser.add_argument('--no-base', action="store_true",
                           help='Filter a bases that is not in the ibases.v8i file')
    add_name_group(subparser)

    args = parser.parse_args()
    print(args)

    match args:
        case argparse.Namespace(command=None):
            parser.print_help()
            parser.error('One of the commands is required')
        case argparse.Namespace(command='list'):
            if not args.fields:
                args.fields = field_list
        case argparse.Namespace(command='clear', id=None, name=None, no_base=False):
            parser.error('One or more of options required')
    if args.name:
        try:
            args.name = CompareParameter(str(args.name), args.regexp, args.compare_type, args.ignore_case)
        except Exception as err:
            parser.error(f'Error parce regexp {args.name}: {err}')
    return args


def main():
    args = get_args()
    # %APPDATA%\1C\1Cv8 / %APPDATA%\1C\1Cv82
    # %LOCALAPPDATA%\1C\1Cv8 / %LOCALAPPDATA%\1C\1Cv82
    bases_info = get_all_bases_info()
    bases_roaming = get_bases_path([Path(os.path.expandvars(r'%APPDATA%\1C\1Cv8')),
                                    Path(os.path.expandvars(r'%APPDATA%\1C\1Cv82'))], 'roaming')
    bases_local = get_bases_path([Path(os.path.expandvars(r'%LOCALAPPDATA%\1C\1Cv8')),
                                  Path(os.path.expandvars(r'%LOCALAPPDATA%\1C\1Cv82'))], 'local')
    bases = {base_id: {} for base_id in
             set(bases_info.keys()) | set(bases_roaming.keys()) | set(bases_local.keys())}
    for base_id in bases.keys():
        if base_id in bases_info:
            bases[base_id].update(bases_info[base_id])
        if base_id in bases_roaming:
            bases[base_id].update(bases_roaming[base_id])
        if base_id in bases_local:
            bases[base_id].update(bases_local[base_id])
    base_list = [BaseInfo(**x) for x in bases.values()]
    match args.command:
        case 'list':
            if args.order:
                # base_list.sort(key=lambda x: x.__getattribute__(args.order))
                base_list.sort(key=attrgetter(*args.order))
            fields = args.fields if args.fields else field_list
            # Преобразование '\\t' -> '\t'
            delimiter = str(args.delimiter).encode().decode("unicode_escape")
            print(delimiter.join(args.fields))
            for base_info in filter(
                    lambda item: base_filter(item, args), base_list):
                print(delimiter.join(map(lambda x: quote_delimiter(str(base_info.__getattribute__(x)),
                                                                   delimiter=delimiter, quote=args.quote), fields)))
        case 'clear':
            clear_cache(list(filter(
                lambda item: base_filter(item, args), base_list)), args.local, args.roaming)


if __name__ == '__main__':
    main()
