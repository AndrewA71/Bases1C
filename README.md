# Bases 1C

Программа для получения информации о базах 1С и очистки кэша баз.

**Основные возможности:**
1. Вывод списка баз.
2. Очистка кеша баз.

## Параметры запуска

Для запуска приложения из командной строки использовуется модуль bases_1c.py

```
usage: bases_1c.py [-h] [-V] {list,clear} ...
```

### Получение списка баз

```
usage: bases_1c.py list [-h] 
                        [--fields [{id,name,connect,folder,common,roaming_path,roaming_size,local_path,local_size,size} ...]]
                        [--order [{id,name,connect,folder,common,roaming_path,roaming_size,local_path,local_size,size} ...]] 
                        [--delimiter DELIMITER] [--quote QUOTE]
                        [--cache | --no-cache] [--base | --no-base]
                        [--id [ID ...]]
                        [--name NAME] [--regexp] [--ignore-case] [--compare-type {any,start,full}]

Параметры:
  -h, --help                Отобразить этот текст и выйти
  --fields [{id,name,connect,folder,common,roaming_path,roaming_size,local_path,local_size,size} ...]
                            Список полей для вывода, пустой список для вывода всех полей
  --order [{id,name,connect,folder,common,roaming_path,roaming_size,local_path,local_size,size} ...]
                            Список полей для сортировки, пустой параметр для отмены сортировки. См. Список доступных полей 
  --delimiter DELIMITER     Разделитель полей
  --quote QUOTE             Quote delimiter char
  --id [ID ...]             Фильтровать базы по ижентификаторам
  --cache, --no-cache       Фильтровать базы [с/без] кэшем
  --base, --no-base         Фильтровать базы, которые [в/не в] файле ibases.v8i

Фильтр по имена базы:
  --name NAME               Фильтровать базы по имени
  --regexp                  Использовать регулярное выражение
  --ignore-case             Игнорировать регистр символов 
  --compare-type {any,start,full}
                            Тип сравнения (с любой частью/с начала/полное)
```

<a id="fields" />**Список доступных полей:**
* id - идентификатор базы
* name - название базы
* connect - строка соединения
* folder - каталог базы в списке баз
* common - база взята из общего списка баз 
* roaming_path - путь к кэшу roaming 
* roaming_size - размер файлов кэша roaming
* local_path - путь к кэшу local
* local_size - размер файлов кэша local
* size - общий размер файлов кэша

### Очистка кэша баз

```
usage: bases_1c.py clear [-h] 
                         [--local | --no-local] [--roaming | --no-roaming]
                         [--no-base] 
                         [--id [ID ...]] 
                         [--name NAME] [--regexp] [--ignore-case] [--compare-type {any,start,full}]

Параметры:
  -h, --help                Отобразить этот текст и выйти
  --local, --no-local       Очищать/не очищать local кеш
  --roaming, --no-roaming   Очищать/не очищать roaming кеш
  --id [ID ...]             Фильтровать базы по ижентификаторам
  --no-base                 Фильтровать базы, которые не в файле ibases.v8i

Фильтр по имена базы:
  --name NAME               Фильтровать базы по имени
  --regexp                  Использовать регулярное выражение
  --ignore-case             Игнорировать регистр символов 
  --compare-type {any,start,full}
                            Тип сравнения (с любой частью/с начала/полное)
```