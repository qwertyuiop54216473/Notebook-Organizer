import json
from datetime import datetime
from typing import List

DATA_FILE = "notes.json"

class Note:
    def __init__(self, title, text, tags, date=None):
        self.title = title
        self.text = text
        self.tags = tags
        self.date = date if date else datetime.today().strftime("%Y-%m-%d")

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "title": self.title,
            "text": self.text,
            "tags": self.tags,
            "date": self.date,
        }

    @classmethod
    def from_dict(cls, d):
        if d["type"] == "VoiceNote":
            return VoiceNote(d["title"], d["text"], d["tags"], d["date"], d.get("voice_path"))
        return TextNote(d["title"], d["text"], d["tags"], d["date"])

    def __str__(self):
        return f"{self.date} | {self.title} | Tags: {', '.join(self.tags)}"

class TextNote(Note):
    pass

class VoiceNote(Note):
    def __init__(self, title, text, tags, date=None, voice_path="voice.wav"):
        super().__init__(title, text, tags, date)
        self.voice_path = voice_path

    def to_dict(self):
        d = super().to_dict()
        d["voice_path"] = self.voice_path
        return d

    def __str__(self):
        return super().__str__() + f" | Voice: {self.voice_path}"

class UndoStack:
    def __init__(self):
        self.stack = []

    def push(self, notes):
        self.stack.append(json.dumps([n.to_dict() for n in notes]))

    def pop(self):
        if self.stack:
            return [Note.from_dict(d) for d in json.loads(self.stack.pop())]
        return None

class Notebook:
    def __init__(self):
        self.notes: List[Note] = self.load()
        self.undo_stack = UndoStack()

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([n.to_dict() for n in self.notes], f, ensure_ascii=False, indent=2)

    def load(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return [Note.from_dict(d) for d in json.load(f)]
        except:
            return []

    def add_note(self, note):
        self.undo_stack.push(self.notes[:])
        self.notes.append(note)
        self.save()

    def edit_note(self, index, title=None, text=None, tags=None):
        if 0 <= index < len(self.notes):
            self.undo_stack.push(self.notes[:])
            if title: self.notes[index].title = title
            if text: self.notes[index].text = text
            if tags: self.notes[index].tags = tags
            self.save()

    def delete_note(self, index):
        if 0 <= index < len(self.notes):
            self.undo_stack.push(self.notes[:])
            del self.notes[index]
            self.save()

    def filter_notes(self, tag=None, date=None):
        filtered = self.notes
        if tag:
            filtered = [n for n in filtered if tag in n.tags]
        if date:
            filtered = [n for n in filtered if n.date == date]
        return filtered

    def undo(self):
        prev = self.undo_stack.pop()
        if prev is not None:
            self.notes = prev
            self.save()

def input_tags():
    tags = input("Теги (через запятую): ").split(",")
    return [t.strip() for t in tags if t.strip()]

def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except:
        return False

def main():
    nb = Notebook()
    menu = (
        "1. Создать текстовую заметку\n"
        "2. Создать голосовую заметку\n"
        "3. Просмотреть все\n"
        "4. Редактировать\n"
        "5. Удалить\n"
        "6. Фильтрация\n"
        "7. Отмена\n"
        "0. Выйти\n"
    )
    while True:
        print(menu)
        cmd = input("Выберите действие: ")
        if cmd == "1":
            title = input("Заголовок: ").strip()
            text = input("Текст: ").strip()
            tags = input_tags()
            date = input("Дата (ГГГГ-ММ-ДД, пусто = сегодня): ").strip() or datetime.today().strftime("%Y-%m-%d")
            if not title:
                print("Заголовок обязателен.")
                continue
            if not text:
                print("Текст обязателен.")
                continue
            if not validate_date(date):
                print("Неверный формат даты!")
                continue
            nb.add_note(TextNote(title, text, tags, date))
            print("Заметка добавлена.")
        elif cmd == "2":
            title = input("Заголовок: ").strip()
            text = input("Текст: ").strip()
            tags = input_tags()
            voice_path = input("Файл голосовой записи (путь): ").strip() or "voice.wav"
            date = input("Дата (ГГГГ-ММ-ДД, пусто = сегодня): ").strip() or datetime.today().strftime("%Y-%m-%d")
            if not title or not text:
                print("Заголовок и текст обязательны.")
                continue
            if not validate_date(date):
                print("Неверный формат даты!")
                continue
            nb.add_note(VoiceNote(title, text, tags, date, voice_path))
            print("Голосовая заметка добавлена.")
        elif cmd == "3":
            for i, n in enumerate(nb.notes):
                print(f"{i}. {n}")
                print(f"   {n.text}")
        elif cmd == "4":
            try:
                idx = int(input("Номер заметки для редактирования: "))
                if not (0 <= idx < len(nb.notes)):
                    print("Нет такой заметки.")
                    continue
                title = input(f"Новый заголовок ({nb.notes[idx].title}): ").strip()
                text = input(f"Новый текст ({nb.notes[idx].text}): ").strip()
                tags = input_tags() or nb.notes[idx].tags
                nb.edit_note(idx, title or None, text or None, tags or None)
                print("Заметка изменена.")
            except:
                print("Ошибка ввода.")
        elif cmd == "5":
            try:
                idx = int(input("Номер заметки для удаления: "))
                nb.delete_note(idx)
                print("Заметка удалена.")
            except:
                print("Ошибка удаления.")
        elif cmd == "6":
            tag = input("Тег для фильтрации (пусто — пропустить): ").strip()
            date = input("Дата для фильтрации (ГГГГ-ММ-ДД, пусто — пропустить): ").strip()
            filtered = nb.filter_notes(tag or None, date or None)
            if filtered:
                for n in filtered:
                    print(n)
                    print(f"   {n.text}")
            else:
                print("Нет соответствующих заметок.")
        elif cmd == "7":
            nb.undo()
            print("Последнее действие отменено.")
        elif cmd == "0":
            break
        else:
            print("Неизвестная команда.")

if __name__ == "__main__":
    main()
