# TSPosp – Příprava na TSP

Webová aplikace pro přípravu na Test studijních předpokladů (TSP) – přijímací zkoušku Masarykovy univerzity.

## Rychlý start

### 1. Klonování repozitáře

```bash
git clone https://github.com/ondiskokundisko/tsposp.git
cd tsposp
```

### 2. Vytvoření virtuálního prostředí a instalace závislostí

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Použití databáze ⚠️

Databázový soubor (`db.sqlite3`) není součástí repozitáře. Je nutné ho vytvořit spuštěním migrací:

```bash
python manage.py migrate
```

### 4. Vytvoření administrátorského účtu

```bash
python manage.py createsuperuser
```

### 5. Sestavení CSS (volitelné – při úpravách šablon)

Tailwind CSS je předkompilovaný v `static/css/tailwind.css`. Pokud upravíte šablony a přidáváte nové třídy, přestavte CSS:

```bash
npm install
npx tailwindcss -i static/css/input.css -o static/css/tailwind.css --minify
```

### 6. Spuštění vývojového serveru

```bash
python manage.py runserver
```

Aplikace poběží na [http://127.0.0.1:8000](http://127.0.0.1:8000).  
Administrace je dostupná na [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

---

## Proměnné prostředí (produkce)

| Proměnná | Výchozí hodnota | Popis |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure dev key | Tajný klíč Django |
| `DJANGO_DEBUG` | `True` | Nastavte na `False` v produkci |
| `DJANGO_ALLOWED_HOSTS` | *(prázdné)* | Čárkou oddělené povolené domény |

---

## Struktura projektu

```
tsposp/
├── accounts/       # Uživatelské účty a profily
├── core/           # Domovská stránka, O nás, Ceny, Kontakt
├── practice/       # Procvičování a zkušební testy
├── questions/      # Otázky a odpovědi
├── templates/      # HTML šablony
├── static/         # CSS a statické soubory
└── tsp_project/    # Nastavení Django projektu
```
