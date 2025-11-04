from __future__ import annotations

from collections import UserDict
from typing import Callable, Dict, Tuple, Any, List, Optional
import functools


# ===================== ДЕКОРАТОРИ CLI =====================

def input_error(func: Callable[..., str]) -> Callable[..., str]:
    """
    Єдиний обробник типових помилок на рівні хендлерів команд.
    """
    @functools.wraps(func)
    def inner(*args, **kwargs) -> str:
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            # Якщо хендлер підіймає KeyError(name) — красиво виводимо
            name = (e.args[0] if e.args else "").strip() or "<?>"
            return f"Contact '{name}' not found."
        except IndexError:
            # Невистачає аргументів у команді
            return "Enter the argument for the command"
        except ValueError as e:
            # Валідація, наприклад, телефон не 10 цифр
            msg = (str(e).strip() or "Invalid arguments.")
            return msg
        except TypeError:
            # На випадок некоректного виклику хендлера
            return "Handler received unexpected arguments. Use 'help' to see usage."
    return inner


def skip_empty_input(func: Callable[[str], Tuple[str, ...]]) -> Callable[[str], Tuple[str, ...]]:
    """
    Перехоплює порожній ввід і повертає ('',) як маркер відсутності команди.
    """
    @functools.wraps(func)
    def wrapper(user_input: str) -> Tuple[str, ...]:
        if not user_input.strip():
            return ("",)
        return func(user_input)
    return wrapper


# ===================== ООП-МОДЕЛІ =====================

class Field:
    """
    Базовий клас для полів запису (контейнер для value).
    """
    def __init__(self, value: str):
        self.value = value  # у нащадків може бути валідація через property

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"


class Name(Field):
    """
    Обов'язкове поле — ім'я контакту.
    """
    def __init__(self, value: str):
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty.")
        super().__init__(cleaned)


class Phone(Field):
    """
    Телефон з валідацією: рівно 10 цифр (беремо лише цифри).
    """
    def __init__(self, value: str):
        super().__init__(self._normalize_and_validate(value))

    @staticmethod
    def _normalize_and_validate(raw: str) -> str:
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) != 10:
            raise ValueError("Phone must contain exactly 10 digits.")
        return digits

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, v: str) -> None:
        self._value = self._normalize_and_validate(v)


class Record:
    """
    Один запис адресної книги: ім'я + список телефонів.
    """
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: List[Phone] = []

    # --- операції з телефонами ---

    def add_phone(self, phone: str | Phone) -> None:
        p = phone if isinstance(phone, Phone) else Phone(phone)
        self.phones.append(p)

    def remove_phone(self, phone_value: str) -> bool:
        target = self.find_phone(phone_value)
        if target:
            self.phones.remove(target)
            return True
        return False

    def edit_phone(self, old_value: str, new_value: str) -> bool:
        target = self.find_phone(old_value)
        if not target:
            return False
        target.value = new_value  # валідація у setter Phone.value
        return True

    def find_phone(self, phone_value: str) -> Optional[Phone]:
        try:
            normalized = Phone._normalize_and_validate(phone_value)
        except ValueError:
            return None
        for p in self.phones:
            if p.value == normalized:
                return p
        return None

    def __str__(self) -> str:
        phones_str = "; ".join(p.value for p in self.phones) or "—"
        return f"Contact name: {self.name.value}, phones: {phones_str}"


class AddressBook(UserDict):
    """
    Колекція записів (Record). Ключ — точне ім'я (str).
    """
    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        return self.data.get(name)

    def delete(self, name: str) -> bool:
        if name in self.data:
            del self.data[name]
            return True
        return False


# ===================== CLI: ПАРСЕР ТА ХЕНДЛЕРИ =====================

@skip_empty_input
def parse_input(user_input: str) -> Tuple[str, ...]:
    """
    Повертає кортеж: (команда, *аргументи).
    Порожній ввід обробляється декоратором → ('',).
    """
    parts = user_input.strip().split()
    cmd, *args = parts
    return (cmd.lower(), *args)


def help_command() -> str:
    """
    Довідка по доступним командам бота (оновлена під ООП-логіку).
    """
    return (
        "Available commands:\n"
        "- hello — greeting\n"
        "- add <name> <phone> — add a new contact or append phone\n"
        "- change <name> <old_phone> <new_phone> — replace a phone in record\n"
        "- remove <name> <phone> — remove a phone from record\n"
        "- phone <name> — show all phones for contact\n"
        "- delete <name> — delete contact record\n"
        "- all — show all contacts\n"
        "- help — show this message\n"
        "- exit / close — quit"
    )


# ---- Хендлери команд (працюють через AddressBook/Record) ----

@input_error
def handle_add(args: List[str], book: AddressBook) -> str:
    """
    add <name> <phone> — створити запис або додати телефон.
    """
    name, phone = args  # може підняти IndexError — обробить декоратор
    rec = book.find(name)
    if rec is None:
        rec = Record(name)
        rec.add_phone(phone)
        book.add_record(rec)
        return "Contact added."
    else:
        rec.add_phone(phone)
        return "Phone added to existing contact."

@input_error
def handle_change(args: List[str], book: AddressBook) -> str:
    """
    change <name> <old_phone> <new_phone> — заміна телефону у записі.
    """
    name, old_p, new_p = args
    rec = book.find(name)
    if rec is None:
        # Підіймаємо KeyError для уніфікованого повідомлення
        raise KeyError(name)
    ok = rec.edit_phone(old_p, new_p)
    return "Phone updated." if ok else "Old phone not found."

@input_error
def handle_remove(args: List[str], book: AddressBook) -> str:
    """
    remove <name> <phone> — видалити телефон із запису.
    """
    name, phone = args
    rec = book.find(name)
    if rec is None:
        raise KeyError(name)
    ok = rec.remove_phone(phone)
    return "Phone removed." if ok else "Phone not found."

@input_error
def handle_phone(args: List[str], book: AddressBook) -> str:
    """
    phone <name> — показати всі телефони контакту.
    """
    name = args[0]
    rec = book.find(name)
    if rec is None:
        raise KeyError(name)
    phones = "; ".join(p.value for p in rec.phones) or "—"
    return phones

@input_error
def handle_all(args: List[str], book: AddressBook) -> str:
    """
    all — вивести всі записи.
    """
    if not book.data:
        return "No contacts."
    return "\n".join(str(rec) for rec in book.data.values())

@input_error
def handle_delete(args: List[str], book: AddressBook) -> str:
    """
    delete <name> — видалити запис.
    """
    name = args[0]
    ok = book.delete(name)
    return "Contact deleted." if ok else "Contact not found."

def handle_help(args: List[str], book: AddressBook) -> str:
    return help_command()


# Спеціальний маркер для виходу
EXIT_SIGNAL = object()

def handle_exit(args: List[str], book: AddressBook):
    return EXIT_SIGNAL

def handle_empty(args: List[str], book: AddressBook) -> str:
    return "Enter a command or type 'help'."

def handle_unknown(command: str, *, args: List[str], book: AddressBook) -> str:
    return f"Unknown command: '{command}'\n{help_command()}"


# Диспетчер команд
COMMANDS: Dict[str, Callable[..., Any]] = {
    "hello": lambda args, book: "How can I help you?",
    "add": handle_add,
    "change": handle_change,
    "remove": handle_remove,
    "phone": handle_phone,
    "delete": handle_delete,
    "all": handle_all,
    "help": handle_help,
    "exit": handle_exit,
    "close": handle_exit,
    "": handle_empty,  # порожня команда
}


# ===================== ГОЛОВНИЙ ЦИКЛ =====================

def main():
    """
    Основний цикл: читає команду, диспатчить у відповідний хендлер, друкує результат.
    Усередині зберігається ООП-книга контактів AddressBook.
    """
    book = AddressBook()
    print("Welcome to the assistant bot (OOP edition)!")

    while True:
        try:
            command, *args = parse_input(input("Enter a command: "))
        except (KeyboardInterrupt, EOFError):
            print("\nGood bye!")
            break

        handler = COMMANDS.get(command)
        if handler is None:
            print(handle_unknown(command, args=args, book=book))
            continue

        result = handler(args=args, book=book)
        if result is EXIT_SIGNAL:
            print("Good bye!")
            break

        if isinstance(result, str):
            print(result)


if __name__ == "__main__":
    main()
