from typing import Callable
import functools


# Декоратор єдиного оброблення помилок
def input_error(func: Callable[..., str]) -> Callable[..., str]:
    """
    Обгортає хендлер команди та перехоплює типові помилки введення користувача,
    повертаючи дружні повідомлення замість падіння програми.
    """
    # wraps зберігає метадані оригінальної функції (корисно на майбутнє)
    @functools.wraps(func)
    def inner(*args, **kwargs) -> str:
        try:
            # Виклик оригінальної функції-хендлера
            return func(*args, **kwargs)

        # Коли контакт не знайдено (ім'я передається в KeyError)
        except KeyError as e:
            name = (e.args[0] if e.args else "").strip() or "<?>"
            return f"Contact '{name}' not found."

        # Коли бракує або неправильні аргументи
        except IndexError:
            return "Enter the argument for the command"

        # Загальний випадок для некоректних значень, якщо десь з'являться ValueError
        except ValueError as e:
            msg = (str(e).strip() or "Invalid arguments.")
            return msg

    return inner



# Розбір рядка вводу
def parse_input(user_input: str) -> tuple[str, ...]:
    """
    Повертає кортеж: (команда, *аргументи).
    Порожній ввід → ("", []).
    """
    parts = user_input.strip().split()
    if not parts:
        return "", []
    cmd, *args = parts
    return cmd.lower(), *args



# Хелп (викликається окремою командою або з головного циклу)
def help_command() -> str:
    """
    Довідка по доступним командам бота.
    """
    return (
        "Available commands:\n"
        "- hello — greeting\n"
        "- add <name> <phone> — add a new contact\n"
        "- change <name> <new_phone> — update existing contact\n"
        "- phone <name> — show phone number\n"
        "- all — show all contacts\n"
        "- help — show this message\n"
        "- exit / close — quit"
    )



# Хендлери команд
@input_error
def add_contact(args: list[str], contacts: dict[str, str]) -> str:
    """
    add <name> <phone> — додати новий контакт.
    Очікуємо рівно 2 аргументи.
    """
    name, phone = args
    contacts[name] = phone
    return "Contact added."


@input_error
def change_contact(args: list[str], contacts: dict[str, str]) -> str:
    """
    change <name> <new_phone> — змінити номер існуючого контакту.
    Так само очікуємо 2 аргументи. Якщо контакту немає — KeyError(name).
    """
    name, new_phone = args
    _ = contacts[name]  # перевіряємо наявність контакту, KeyError підійме декоратор
    contacts[name] = new_phone
    return "Contact updated."


@input_error
def show_phone(args: list[str], contacts: dict[str, str]) -> str:
    """
    phone <name> — показати номер телефону контакту.
    Без аргументів → IndexError (для уніфікованого повідомлення).
    """
    name = args[0]
    return contacts[name]


@input_error
def show_all(contacts: dict[str, str]) -> str:
    """
    all — вивести всі контакти у форматі 'Name: Phone' по одному в рядку.
    Порожній словник → повідомлення 'No contacts.' (це не помилка).
    """
    contacts_view = "\n".join(f"{n}: {p}" for n, p in contacts.items())
    return contacts_view or "No contacts."



# Головний цикл бота
def main():
    """
    Основний цикл
    """
    contacts: dict[str, str] = {}
    print("Welcome to the assistant bot!")
    while True:
        command, *args = parse_input(input("Enter a command: "))

        if command in ("close", "exit"):
            print("Good bye!")
            break

        if command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, contacts))

        elif command == "change":
            print(change_contact(args, contacts))

        elif command == "phone":
            print(show_phone(args, contacts))

        elif command == "all":
            print(show_all(contacts))

        elif command == "help":
            print(help_command())

        elif command == "":
            # Порожній ввід: підказка користувачу
            print("Enter a command or type 'help'.")

        else:
            # Невідома команда: повідомлення + (за бажанням) help
            print(f"Unknown command: '{command}'")
            # За потреби поведінку можна змінити, закоментувавши наступний рядок
            print(help_command())


if __name__ == "__main__":
    main()
