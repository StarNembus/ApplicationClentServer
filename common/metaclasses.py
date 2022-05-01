import dis
from pprint import pprint


# Метакласс для проверки соответствия сервера:
class ServerMaker(type):

    def __init__(cls, clsname, bases, clsdict):
        """
        :param clsname: - экземпляр метакласса - Server
        :param bases: кортеж базовых классов - ()
        :param clsdict: словарь атрибутов и методов экземпляра метакласса
        """
        # Список методов, которые используются в функциях класса:
        methods = []  # с помощью 'LOAD_GLOBAL'
        methods_2 = []  # методы, обёрнутые декораторами попадают  не в 'LOAD_GLOBAL', а в 'LOAD_METHOD'
        # Атрибуты, используемые в функциях классов
        attrs = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
            # Если  функция разбираем код, получая используемые методы и атрибуты.
                for i in ret:
                    print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            # заполняем список методами, использующимися в функциях класса
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_METHOD':
                        if i.argval not in methods_2:
                            methods_2.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            # заполняем список атрибутами, использующимися в функциях класса
                            attrs.append(i.argval)

        print(20 * '-', 'methods', 20 * '-')
        pprint(methods)
        print(20 * '-', 'methods_2', 20 * '-')
        pprint(methods_2)
        print(20 * '-', 'attrs', 20 * '-')
        pprint(attrs)
        print(50 * '-')

        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо в серверном классе')

        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')

        # Вызываем конструктор предка

        super().__init__(clsname, bases, clsdict)


# Метакласс для проверки корректности клиентов:
class ClientMaker(type):
    def __init__(cls, clsname, bases, clsdict):
        # Список методов, которые используются в функциях класса:
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
                # Если не функция то ловим исключение
            except TypeError:
                pass
            else:
                #Если функция разбираем код, получая используемые методы.
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        # Если обнаружено использование недопустимого метода accept, listen, socket бросаем исключение:
        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('В классе обнаружено использование запрещённого метода')
        # Вызов get_message или send_message из utils считаем корректным использованием сокетов
        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')

        super().__init__(clsname, bases, clsdict)







