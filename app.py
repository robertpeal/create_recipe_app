import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "dev-secret-key"
DB_PATH = "recipes.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS recipe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            prep_time INTEGER,
            cook_time INTEGER,
            servings INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ingredient (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            quantity TEXT,
            unit TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipe(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS step (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            step_order INTEGER NOT NULL,
            instruction TEXT NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES recipe(id)
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db()
    recipes = conn.execute("SELECT * FROM recipe ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", recipes=recipes)


@app.route("/recipes/new", methods=["GET", "POST"])
def new_recipe():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        prep_time = request.form.get("prep_time") or None
        cook_time = request.form.get("cook_time") or None
        servings = request.form.get("servings") or None

        if not title:
            flash("Title is required.")
            return redirect(url_for("new_recipe"))

        ingredients = request.form.getlist("ingredient_name[]")
        quantities = request.form.getlist("ingredient_quantity[]")
        units = request.form.getlist("ingredient_unit[]")

        steps = request.form.getlist("step_instruction[]")

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO recipe (title, prep_time, cook_time, servings) VALUES (?, ?, ?, ?)",
            (title, prep_time, cook_time, servings),
        )
        recipe_id = cur.lastrowid

        for i, name in enumerate(ingredients):
            name = name.strip()
            if name:
                qty = quantities[i] if i < len(quantities) else ""
                unit = units[i] if i < len(units) else ""
                cur.execute(
                    "INSERT INTO ingredient (recipe_id, name, quantity, unit) VALUES (?, ?, ?, ?)",
                    (recipe_id, name, qty, unit),
                )

        for order, instruction in enumerate(steps, start=1):
            instruction = instruction.strip()
            if instruction:
                cur.execute(
                    "INSERT INTO step (recipe_id, step_order, instruction) VALUES (?, ?, ?)",
                    (recipe_id, order, instruction),
                )

        conn.commit()
        conn.close()
        flash("Recipe saved successfully!")
        return redirect(url_for("view_recipe", recipe_id=recipe_id))

    return render_template("new_recipe.html")


@app.route("/recipes/<int:recipe_id>")
def view_recipe(recipe_id):
    conn = get_db()
    recipe = conn.execute("SELECT * FROM recipe WHERE id = ?", (recipe_id,)).fetchone()
    if recipe is None:
        flash("Recipe not found.")
        return redirect(url_for("index"))

    ingredients = conn.execute(
        "SELECT * FROM ingredient WHERE recipe_id = ?", (recipe_id,)
    ).fetchall()
    steps = conn.execute(
        "SELECT * FROM step WHERE recipe_id = ? ORDER BY step_order", (recipe_id,)
    ).fetchall()
    conn.close()
    return render_template(
        "view_recipe.html", recipe=recipe, ingredients=ingredients, steps=steps
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
