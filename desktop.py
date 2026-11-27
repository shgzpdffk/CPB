import json
import sys
from pathlib import Path
from search_worker import SearchWorker

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QStackedWidget,
    QScrollArea,
)


def load_known_products(catalog_path):
    with catalog_path.open(encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)

    if not isinstance(catalog, dict) or not isinstance(catalog.get("products"), list):
        raise ValueError("В справочнике products.json нужен список products")

    names = set()
    for name in catalog["products"]:
        if not isinstance(name, str):
            raise ValueError("Названия продуктов в справочнике должны быть строками")

        normalized_name = " ".join(name.split()).casefold()
        if not normalized_name:
            raise ValueError("В справочнике найдено пустое название продукта")

        names.add(normalized_name)

    # Сначала распознаём составные названия, затем короткие.
    return sorted(names, key=lambda name: len(name.split()), reverse=True)


def create_window():
    window = QWidget()
    window.setObjectName("recipeWindow")
    window.setWindowTitle("Че по блюдам")
    window.resize(950, 600)
    window.search_worker = None

    layout = QHBoxLayout(window)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(20)

    form = QWidget()
    form.setObjectName("searchForm")
    form_layout = QVBoxLayout(form)
    form_layout.setSpacing(10)
    form_layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(form, 2)

    results = QWidget()
    results.setObjectName("recipeResults")
    results_layout = QVBoxLayout(results)
    results_layout.setContentsMargins(0, 0, 0, 0)
    results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    pages = QStackedWidget()
    pages.addWidget(results)
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(pages)
    layout.addWidget(scroll_area, 3)

    details = QWidget()
    details_layout = QVBoxLayout(details)
    pages.addWidget(details)

    back_button = QPushButton("Назад к результатам")
    details_layout.addWidget(back_button)

    details_title = QLabel()
    details_title.setObjectName("recipeTitle")
    details_title.setWordWrap(True)
    details_layout.addWidget(details_title)
    details_layout.addWidget(QLabel("Исходные ингредиенты"))

    ingredients_list = QListWidget()
    details_layout.addWidget(ingredients_list)

    details_purchases = QLabel()
    details_purchases.setTextFormat(Qt.TextFormat.PlainText)
    details_purchases.setWordWrap(True)
    details_layout.addWidget(details_purchases)

    details_substitutions = QLabel()
    details_substitutions.setWordWrap(True)
    details_layout.addWidget(details_substitutions)
    details_layout.addWidget(QLabel("Готовка"))

    steps_label = QLabel()
    steps_label.setTextFormat(Qt.TextFormat.PlainText)
    steps_label.setWordWrap(True)
    details_layout.addWidget(steps_label)

    source_link = QLabel()
    source_link.setTextFormat(Qt.TextFormat.RichText)
    source_link.setOpenExternalLinks(True)
    details_layout.addWidget(source_link)

    back_button.clicked.connect(lambda: pages.setCurrentWidget(results))

    product_input = QLineEdit()
    product_input.setObjectName("productInput")
    add_button = QPushButton("Добавить")
    delete_button = QPushButton("Удалить")
    product_list = QListWidget()
    product_list.setObjectName("productList")
    wish_input = QLineEdit()
    wish_input.setObjectName("wishInput")
    search_button = QPushButton("Найти рецепты")
    search_button.setObjectName("searchButton")

    form_layout.addWidget(QLabel("Какие есть продукты?"))
    form_layout.addWidget(product_input)
    form_layout.addWidget(add_button)
    form_layout.addWidget(delete_button)
    form_layout.addWidget(product_list)
    form_layout.addWidget(QLabel("Пожелания по блюдам"))
    form_layout.addWidget(wish_input)
    form_layout.addWidget(search_button)

    catalog_path = Path(__file__).with_name("products.json")
    known_products = load_known_products(catalog_path)

    def split_products(text):
        products = []

        for part in text.split(","):
            words = part.split()
            found_products = []

            while words:
                for known_name in known_products:
                    word_count = len(known_name.split())
                    candidate = " ".join(words[:word_count])

                    if candidate.casefold() == known_name:
                        found_products.append(candidate)
                        words = words[word_count:]
                        break
                else:
                    found_products = [part.strip()]
                    break

            products.extend(found_products)

        return products

    def add_product():
        already_exists = set()
        for index in range(product_list.count()):
            name = product_list.item(index).text()
            already_exists.add(name.casefold())

        for part in split_products(product_input.text()):
            name = part.strip()
            if not name:
                continue

            key = name.casefold()
            if key in already_exists:
                continue

            product_list.addItem(name)
            already_exists.add(key)

        product_input.clear()
    def delete_product():
        selected = product_list.selectedItems()
        if not selected:
            return

        product_list.takeItem(product_list.row(selected[0]))

    def format_substitution(substitution):
        original = substitution["required_ingredient"]
        replacement = substitution["available_ingredient"]
        text = f"Замена: {original} → {replacement}"

        context = substitution.get("context")
        if context:
            text += f" ({context})"

        return text

    def format_purchases(recipe):
        count = recipe["missing_count"]
        if count == 0:
            return "Докупать ничего не нужно"

        names = ', '.join(recipe["missing_required"])
        return f"Докупить: {count} - {names}"
    
    def open_recipe(recipe):
        details_title.setText(recipe["title"])
        ingredients_list.clear()

        for ingredient in recipe["ingredients"]:
            text = ingredient["name"]
            count = ingredient.get("count")

            if count:
                text += f" — {count}"

            ingredients_list.addItem(text)

        substitution_lines = []
        for substitution in recipe["substitutions"]:
            substitution_lines.append(format_substitution(substitution))

        details_substitutions.setText("\n".join(substitution_lines))
        details_purchases.setText(format_purchases(recipe))
        details_substitutions.setVisible(bool(substitution_lines))

        step_lines = []

        for number, step in enumerate(recipe["steps"], start=1):
            step_lines.append(f"{number}. {step}")

        steps_label.setText("\n".join(step_lines))
        pages.setCurrentWidget(details)

    def search_recipes():
        if not search_button.isEnabled():
            return

        search_button.setEnabled(False)
        search_button.setText("Ищем рецепты...")
        load_recipes()

    def finish_search():
        window.search_worker.wait()
        window.search_worker.deleteLater()
        window.search_worker = None

        search_button.setEnabled(True)
        search_button.setText("Найти рецепты")

    def show_error(message):
        print(message)
        results_layout.addWidget(QLabel("Не удалось загрузить рецепты"))

        retry_button = QPushButton("Повторить")
        retry_button.clicked.connect(search_recipes)
        results_layout.addWidget(retry_button)

    def wait_for_search():
        if window.search_worker is not None:
            window.search_worker.wait()

    def load_recipes():
        products = []
        for index in range(product_list.count()):
            products.append(product_list.item(index).text())

        request = {"products": products}
        wish = wish_input.text().strip()
        if wish:
            request["wish"] = wish

        while results_layout.count():
            widget = results_layout.takeAt(0).widget()
            widget.hide()
            widget.deleteLater()

        pages.setCurrentWidget(results)

        worker = SearchWorker(request)
        window.search_worker = worker

        worker.succeeded.connect(
            show_recipes, Qt.ConnectionType.QueuedConnection
        )
        worker.failed.connect(
            show_error, Qt.ConnectionType.QueuedConnection
        )
        worker.finished.connect(
            finish_search, Qt.ConnectionType.QueuedConnection
        )

        worker.start()

    def show_recipes(response):
        recipes = response["recipes"]

        
        if not recipes:
            empty_label = QLabel("По этим продуктам и условиям рецептов не найдено")
            empty_label.setWordWrap(True)
            results_layout.addWidget(empty_label)
            pages.setCurrentWidget(results)
            return

        for recipe in recipes:
            title = recipe["title"].replace("&", "&&")
            card = QGroupBox(title)
            card.setObjectName("recipeCard")
            card.setProperty("recipeId", recipe["id"])
            card_layout = QVBoxLayout(card)

            purchases = QLabel(format_purchases(recipe))
            purchases.setTextFormat(Qt.TextFormat.PlainText)
            purchases.setWordWrap(True)
            card_layout.addWidget(purchases)
            for substitution in recipe["substitutions"]:
                substitution_label = QLabel(format_substitution(substitution))
                substitution_label.setWordWrap(True)
                card_layout.addWidget(substitution_label)

            open_button = QPushButton("Открыть рецепт")
            open_button.clicked.connect(
                lambda checked=False, selected_recipe=recipe: open_recipe(selected_recipe)
            )
            card_layout.addWidget(open_button)

            results_layout.addWidget(card)

    add_button.clicked.connect(add_product)
    delete_button.clicked.connect(delete_product)
    search_button.clicked.connect(search_recipes)
    QApplication.instance().aboutToQuit.connect(wait_for_search)
    style_path = Path(__file__).with_name("style.qss")
    window.setStyleSheet(style_path.read_text(encoding="utf-8"))
    return window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = create_window()
    window.show()
    sys.exit(app.exec())
