from __future__ import annotations

from collections import UserDict
from typing import List, Optional


# ===== БАЗОВІ ТИПИ ПОЛІВ =====================================================

class Field:
    """
    Базовий клас для полів запису (узагальнений контейнер для value).
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
    (Додаткової валідації тут не потрібно, але можна нормалізувати пробіли.)
    """
    def __init__(self, value: str):
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty.")
        super().__init__(cleaned)


class Phone(Field):
    """
    Телефон з валідацією: рівно 10 цифр.
    Дозволяємо на вхід сирий рядок, обробляємо/перевіряємо у сеттері.
    """
    def __init__(self, value: str):
        super().__init__(self._normalize_and_validate(value))

    @staticmethod
    def _normalize_and_validate(raw: str) -> str:
        s = "".join(ch for ch in raw if ch.isdigit())  # залишаємо тільки цифри
        if len(s) != 10:
            raise ValueError("Phone must contain exactly 10 digits.")
        return s

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, v: str) -> None:
        # setter викликається і з __init__, і при подальших змінах
        self._value = self._normalize_and_validate(v)


# ===== ЗАПИС КОНТАКТУ ========================================================

class Record:
    """
    Один запис адресної книги: ім'я + список телефонів.
    - name: об'єкт Name
    - phones: список об'єктів Phone
    """
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: List[Phone] = []

    # --- операції з телефонами ---

    def add_phone(self, phone: str | Phone) -> None:
        """
        Додає телефон. Приймає або сирий рядок (10 цифр), або готовий Phone.
        Дублікати не забороняємо за умовчанням (ТЗ не вимагає), але можна
        легко додати перевірку у майбутньому.
        """
        p = phone if isinstance(phone, Phone) else Phone(phone)
        self.phones.append(p)

    def remove_phone(self, phone_value: str) -> bool:
        """
        Видаляє ПЕРШИЙ знайдений телефон за значенням (рядок з 10 цифр).
        Повертає True, якщо видалили; False — якщо не знайдено.
        """
        target = self.find_phone(phone_value)
        if target:
            self.phones.remove(target)
            return True
        return False

    def edit_phone(self, old_value: str, new_value: str) -> bool:
        """
        Знаходить перший телефон зі значенням old_value і заміняє його на new_value.
        Повертає True, якщо успішно; False — якщо старий не знайдено.
        """
        target = self.find_phone(old_value)
        if not target:
            return False
        target.value = new_value  # валідація відбудеться у Phone.value.setter
        return True

    def find_phone(self, phone_value: str) -> Optional[Phone]:
        """
        Повертає об'єкт Phone за значенням (10 цифр) або None, якщо не знайдено.
        Приймає як «сирий» рядок (може містити нецифрові символи) — нормалізуємо.
        """
        try:
            normalized = Phone._normalize_and_validate(phone_value)
        except ValueError:
            # якщо вхід не 10 цифр — одразу None (шукати нема сенсу)
            return None

        for p in self.phones:
            if p.value == normalized:
                return p
        return None

    def __str__(self) -> str:
        phones_str = "; ".join(p.value for p in self.phones)
        return f"Contact name: {self.name.value}, phones: {phones_str}"


# ===== АДРЕСНА КНИГА =========================================================

class AddressBook(UserDict):
    """
    Колекція записів (Record), ключ — ІМ'Я (рядок). Спадкуємося від UserDict
    для зручності, зберігаємо у self.data словник {name_str: Record}.
    """

    def add_record(self, record: Record) -> None:
        """
        Додає запис у книгу. Ключ — точне ім'я (як у record.name.value).
        Якщо ім'я вже існує, перезаписує (можна змінити поведінку за потреби).
        """
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        """
        Пошук запису за ІМ'ЯМ (точний збіг, регістр важливий як у прикладі ТЗ).
        За потреби можна зробити case-insensitive варіант.
        """
        return self.data.get(name)

    def delete(self, name: str) -> bool:
        """
        Видалення запису за ІМ'ЯМ. Повертає True — якщо видалили, False — якщо ні.
        """
        if name in self.data:
            del self.data[name]
            return True
        return False


# ===== ДЕМО-СЦЕНАРІЙ З ТЗ ====================================================
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
    book.delete("Jane")
    
    print("\nAfter deleting Jane:")
    for name, record in book.data.items():
        print(record)
