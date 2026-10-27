-- Project contains data from Open Beauty Facts, available under the Open Database License

SELECT ingredient, COUNT(*) AS n
FROM product_ingredients
GROUP BY ingredient
ORDER BY n DESC
LIMIT 10;



-- top10 product in each class


DROP VIEW IF EXISTS vw_class_counts;

CREATE VIEW vw_class_counts AS
SELECT ic.main_class, pi.ingredient, COUNT(DISTINCT pi.code) AS n
FROM product_ingredients pi
JOIN ingredient_classes ic ON pi.ingredient = ic.ingredient
GROUP BY ic.main_class, pi.ingredient;



DROP VIEW IF EXISTS vw_class_ranking10;

CREATE VIEW vw_class_ranking10 AS

WITH ranked_class AS (
    SELECT main_class, ingredient, n,
        ROW_NUMBER() OVER (
            PARTITION BY main_class
            ORDER BY n DESC, ingredient
        ) AS rn
    FROM vw_class_counts
)

SELECT main_class, rn AS ranking, ingredient, n 
FROM ranked_class
WHERE rn <= 10;



DROP VIEW IF EXISTS vw_avg_class;

CREATE VIEW vw_avg_class AS
SELECT main_class,
       COUNT(*) AS n_ingredients,
       ROUND(AVG(n)) AS avg_products_per_ingredient
FROM vw_class_counts
GROUP BY main_class
ORDER BY avg_products_per_ingredient DESC;




DROP VIEW IF EXISTS vw_class_ingredient_count;

CREATE VIEW vw_class_ingredient_count AS
SELECT main_class,
       COUNT(*) AS n_ingredients
FROM ingredient_classes
GROUP BY main_class
ORDER BY n_ingredients DESC;



DROP VIEW IF EXISTS vw_category;

CREATE VIEW IF NOT EXISTS vw_category AS
SELECT pc.category, p.code, p.product_name, p.n_ingredients, pi.ingredient
    FROM products p
    INNER JOIN product_categories pc ON p.code = pc.code
    INNER JOIN product_ingredients pi ON p.code = pi.code
WHERE pc.category IN ('face', 'body', 'suncare') AND p.n_ingredients IS NOT NULL;



DROP VIEW IF EXISTS vw_cat_ranking10;

CREATE VIEW vw_cat_ranking10 AS
SELECT category, ingredient, n_products, ranking
FROM (
    SELECT category, ingredient, n_products,
           RANK() OVER (
               PARTITION BY category
               ORDER BY n_products DESC
           ) AS ranking

    FROM (
        SELECT category, ingredient,
               COUNT(DISTINCT code) AS n_products
        FROM vw_category
        GROUP BY category, ingredient
    )
)
WHERE ranking <= 10;




SELECT main_class, ranking, ingredient, n
FROM vw_class_ranking10
WHERE main_class IN ('active / skin-conditioning ingredient', 'humectant', 'emollient')
  AND ranking <= 3
ORDER BY main_class, ranking;



DROP VIEW IF EXISTS vw_cat_ingredient_share;

CREATE VIEW vw_cat_ingredient_share AS
SELECT c.category, c.ingredient,
       COUNT(DISTINCT c.code) AS n_products,
       t.total,
       ROUND(100.0 * COUNT(DISTINCT c.code) / t.total, 1) AS pct_products
FROM vw_category c
JOIN (SELECT category, COUNT(DISTINCT code) AS total
      FROM vw_category GROUP BY category) t
  ON c.category = t.category
GROUP BY c.category, c.ingredient;



DROP VIEW IF EXISTS vw_avg_category;

CREATE VIEW IF NOT EXISTS vw_avg_category AS
SELECT pc.category, COUNT(*) AS n_products,
       ROUND(AVG(p.n_ingredients), 1) AS avg_n_ingredients,
       MIN(p.n_ingredients) AS min_n, MAX(p.n_ingredients) AS max_n
FROM products p
JOIN product_categories pc ON p.code = pc.code
WHERE pc.category IN ('face', 'body', 'suncare')
GROUP BY pc.category;


-- data covered in analisys
SELECT ROUND(100.0 * SUM(ic.ingredient IS NOT NULL) / COUNT(*), 1) AS pct_classified
FROM product_ingredients pi
LEFT JOIN ingredient_classes ic ON pi.ingredient = ic.ingredient;



-- allergens

DROP VIEW IF EXISTS vw_allergen_share;

CREATE VIEW vw_allergen_share AS
WITH prod AS (
    SELECT c.category, c.code,
           MAX(CASE WHEN ic.allergen_EU = 'yes'
                     AND c.ingredient <> 'benzyl alcohol'
                    THEN 1 ELSE 0 END) AS has_allergen,
           MAX(CASE WHEN c.ingredient = 'fragrance'
                    THEN 1 ELSE 0 END) AS has_fragrance
    FROM vw_category c
    LEFT JOIN ingredient_classes ic ON c.ingredient = ic.ingredient
    GROUP BY c.category, c.code
)
SELECT category,
       COUNT(*) AS n_products,
       SUM(has_fragrance) AS n_with_fragrance,
       ROUND(100.0 * SUM(has_fragrance) / COUNT(*), 1) AS pct_fragrance,
       SUM(has_allergen) AS n_with_allergen,
       ROUND(100.0 * SUM(has_allergen) / COUNT(*), 1) AS pct_allergen
FROM prod
GROUP BY category;

SELECT category,
       SUM(has_fragrance = 1 AND has_allergen = 0) AS fragrance_no_listed_allergen
FROM (
    SELECT c.category, c.code,
           MAX(c.ingredient = 'fragrance') AS has_fragrance,
           MAX(ic.allergen_EU = 'yes' AND c.ingredient <> 'benzyl alcohol') AS has_allergen
    FROM vw_category c
    LEFT JOIN ingredient_classes ic ON c.ingredient = ic.ingredient
    GROUP BY c.category, c.code
)
GROUP BY category;



SELECT ingredient,
       COALESCE(MAX(CASE WHEN category='face'    THEN pct_products END), 0) AS face,
       COALESCE(MAX(CASE WHEN category='body'    THEN pct_products END), 0) AS body,
       COALESCE(MAX(CASE WHEN category='suncare' THEN pct_products END), 0) AS suncare
FROM vw_cat_ingredient_share
WHERE ingredient IN (SELECT ingredient FROM ingredient_classes)
GROUP BY ingredient
ORDER BY suncare - (face + body) / 2.0 DESC
LIMIT 15;


SELECT COUNT(*) AS products_in_2plus_categories
FROM (SELECT code FROM product_categories
      WHERE category IN ('face','body','suncare')
      GROUP BY code HAVING COUNT(*) > 1);




WITH face_products AS (
    SELECT f.code,
           CASE WHEN EXISTS (SELECT 1 FROM product_categories s
                             WHERE s.code = f.code AND s.category = 'suncare')
                THEN 'face + suncare' ELSE 'face only' END AS grp
    FROM product_categories f
    WHERE f.category = 'face'
),
uv AS (
    SELECT DISTINCT pi.code
    FROM product_ingredients pi
    JOIN ingredient_classes ic ON pi.ingredient = ic.ingredient
    WHERE ic.main_class = 'UV filter'
)
SELECT fp.grp,
       COUNT(*) AS n_products,
       SUM(CASE WHEN uv.code IS NOT NULL THEN 1 ELSE 0 END) AS n_with_uv_filter,
       ROUND(100.0 * SUM(CASE WHEN uv.code IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_with_uv_filter
FROM face_products fp
LEFT JOIN uv ON fp.code = uv.code
GROUP BY fp.grp;


-- Project contains data from Open Beauty Facts, available under the Open Database License