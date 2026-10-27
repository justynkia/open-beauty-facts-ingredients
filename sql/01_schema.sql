-- Project contains data from Open Beauty Facts, available under the Open Database License

DROP TABLE IF EXISTS product_ingredients;
DROP TABLE IF EXISTS product_categories;
DROP TABLE IF EXISTS ingredient_classes;
DROP TABLE IF EXISTS products;

CREATE TABLE products(
    code TEXT PRIMARY KEY,
    product_name TEXT,
    n_ingredients INTEGER
);

CREATE TABLE product_categories(
    code TEXT NOT NULL,
    category TEXT NOT NULL,
    PRIMARY KEY (code, category)
);

CREATE TABLE product_ingredients(
    code TEXT NOT NULL,
    position INTEGER NOT NULL,
    ingredient TEXT NOT NULL,
    PRIMARY KEY (code, position),
    FOREIGN KEY (code) REFERENCES products(code)
);

CREATE TABLE ingredient_classes(
    ingredient TEXT PRIMARY KEY,
    main_class TEXT,
    second_class TEXT,
    allergen_EU TEXT
);

-- Project contains data from Open Beauty Facts, available under the Open Database License