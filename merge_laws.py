import os

files = [
    "data/ИЖС_статьи.docx",
    "data/ОЦС.txt",
    "data/ижс_услуги.txt",
    "data/спросидомрф.txt",
    "data/Федеральный закон от 13 июля 2015 г N 218 ФЗ О государственной регистрации недви.docx",
    "data/ВРИ.txt",
    "data/проекты_домов.txt"
]

all_text = []

for file in files:
    if not os.path.exists(file):
        print(f"Нет файла: {file}")
        continue

    if file.endswith(".docx"):
        import docx

        doc = docx.Document(file)
        for p in doc.paragraphs:
            if p.text.strip():
                all_text.append(p.text.strip())
    else:
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_text.append(line.strip())

# Сохраняем как TXT (без проблем с XML)
with open("законы_объединенные.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(all_text))

print(f"Объединено {len(all_text)} фрагментов в законы_объединенные.txt")