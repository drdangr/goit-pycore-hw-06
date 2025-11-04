from __future__ import annotations

from collections import UserDict
from typing import List, Optional


# ===================== БАЗОВІ ПОЛЯ =====================

class Field:
    """
    Базовий клас для полів запису (контейнер для value).
    """
    def __init__(self, value: str):
        # У нащадків може бути валідація через property/setter.
        self.value = value

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
        # Залишаємо лише цифри
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) != 10:
            raise ValueError("Phone must contain exactly 10 digits.")
        return digits

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, v: str) -> None:
        # Валідація/нормалізація і при ініціалізації, і при редагуванні
        self._value = self._normalize_and_validate(v)


# ===================== ЗАПИС (КОНТАКТ) =====================

class Record:
    """
    Один запис адресної книги: ім'я + список телефонів.
    - name: Name
    - phones: list[Phone]
    """
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: List[Phone] = []

    # ---- операції з телефонами ----

    def add_phone(self, phone: str | Phone) -> None:
        """
        Додає телефон (рядок або об'єкт Phone).
        """
        p = phone if isinstance(phone, Phone) else Phone(phone)
        self.phones.append(p)

    def remove_phone(self, phone_value: str) -> bool:
        """
        Видаляє перший знайдений телефон за значенням (10 цифр).
        Повертає True, якщо видалено; False — якщо не знайдено.
        """
        target = self.find_phone(phone_value)
        if target:
            self.phones.remove(target)
            return True
        return False

    def edit_phone(self, old_value: str, new_value: str) -> bool:
        """
        Замінює перший знайдений телефон old_value на new_value.
        Повертає True, якщо успішно; False — якщо не знайдено.
        """
        target = self.find_phone(old_value)
        if not target:
            return False
        target.value = new_value  # валідація у setter Phone.value
        return True

    def find_phone(self, phone_value: str) -> Optional[Phone]:
        """
        Повертає Phone із таким значенням або None.
        На вхід можна дати «сирий» рядок — він нормалізується.
        """
        try:
            normalized = Phone._normalize_and_validate(phone_value)
        except ValueError:
            return None

        for p in self.phones:
            if p.value == normalized:
                return p
        return None

    def __str__(self) -> str:
        phones_str = "; ".join(p.value for p in self.phones)
        return f"Contact name: {self.name.value}, phones: {phones_str}"


# ===================== АДРЕСНА КНИГА =====================

class AddressBook(UserDict):
    """
    Колекція записів (Record). Ключ — точне ім'я (str).
    Зберігається у self.data як {name: Record}.
    """

    def add_record(self, record: Record) -> None:
        """
        Додає запис у книгу за ключем record.name.value.
        Якщо ключ існує — перезаписує.
        """
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        """
        Знаходить запис за іменем (точний збіг).
        """
        return self.data.get(name)

    def delete(self, name: str) -> bool:
        """
        Видаляє запис за іменем. True — якщо видалено; False — якщо не знайдено.
        """
        if name in self.data:
            del self.data[name]
            return True
        return False


# ===================== ДЕМО З ТЗ =====================

if __name__ == "__main__":
    # Створення нової адресної книги
    book = AddressBook()

    # Створення запису для John
    john_record = Record("John")
    john_record.add_phone("1234567890")
    john_record.add_phone("5555555555")

    # Додавання запису John до адресної книги
    book.add_record(john_record)

    # Створення та додавання нового запису для Jane
    jane_record = Record("Jane")
    jane_record.add_phone("9876543210")
    book.add_record(jane_record)

    # Виведення всіх записів у книзі
    for name, record in book.data.items():
        print(record)


    # Знаходження та редагування телефону для John
    john = book.find("John")
    john.edit_phone("1234567890", "1112223333")

    print(john)  # Виведення: Contact name: John, phones: 1112223333; 5555555555
    
    # Пошук конкретного телефону у записі John
    found_phone = john.find_phone("5555555555")
    print(f"{john.name}: {found_phone}")  # Виведення: 5555555555
    
    # Видалення запису Jane
    removed = book.delete("Jane")
    print("Jane removed:", removed)
