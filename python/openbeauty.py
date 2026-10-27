# Project contains data from Open Beauty Facts, available under the Open Database License


import pandas as pd
import re
import unicodedata
import os

from pathlib import Path

# project folder = parent of the python/ folder (works wherever the script is started from)
try:
    BASE_DIR = Path(__file__).resolve().parent.parent
except NameError:            # notebook / interactive window
    BASE_DIR = Path.cwd()
RAW_FILE = BASE_DIR / "data" / "raw" / "products.csv"

df = pd.read_csv(r"C:\Users\justa\projekt\projekt_openbeauty\data\raw\products.csv",
                 sep="\t", encoding="utf-8", low_memory=False,
                 on_bad_lines="skip")



#columns in alphabetical order for easier reading

for col in sorted(df.columns):
    print(col)

#checking for missing values in each column

print(df.shape)
fill = df.notna().mean().sort_values(ascending=False)
print(fill.head(40))

filtered_df = df[df['ingredients_text'].notna()]
print("Useful rows:", len(filtered_df), "from", len(df))

# #filtered rows - rows with non-empty ingredients_text column 17628 from 64237

# #checking for results for countries and categories with the largest amount of completely filled rows
# print(filtered_df['countries_tags'].str.split(",").explode().value_counts().head(15))
# print(filtered_df['categories_tags'].str.split(",").explode().value_counts().head(15))

# #France is the country with largest amount of results - 7345 products
# #categories tags are harder to analyze - some of them are too general (hygiene), are not specifically cosmetics categories (open-beauty-facts or non-food-products) or are overlapping (for example "shampoos" and "hair")


# #In this analysis, I will focus on products from France with following categories: "face", "body" and "suncare"
#filtering data by chosen categories - "face", "body" and "suncare"
new_categories = ["en:face", "en:body", "en:suncare"]
CAT_RE = r"(?:^|,)en:(?:face|body|suncare)(?:-[^,]*)?(?:,|$)"
cosmetics_df = filtered_df[filtered_df['categories_tags'].str.contains(CAT_RE, na=False)]
print("Filtered results by chosen categories only:", len(cosmetics_df)) #count: 1879

# #filtering data by chosen categories and country - France
france_df = cosmetics_df[cosmetics_df["countries_tags"].str.contains("en:france", na=False)]
print("Filtered result by chosen categories for France:", len(france_df)) #count: 1009

#checking sample for previously filtered data


sample = france_df.sample(10, random_state=42)

for name, row in sample.iterrows(): #printing results row by row
    print("Product name:", row["product_name"], "Category name:", row["categories_tags"])
    print("Ingredient text:", row["ingredients_text"], "\n")


print(france_df["ingredients_text"].dtype) #checking if ingredients_text is str type

# #making dataframe copy to safely clean data
clean_france = france_df.copy()

#cleaning and modyfying "ingredients_text" column
clean_france["ingredients_text"] = clean_france["ingredients_text"].str.lower() #all lowercase
clean_france["ingredients_text"] = clean_france["ingredients_text"].str.replace("*", "") #removing unwanted stars from ingredients,
clean_france["ingredients_text"] = clean_france["ingredients_text"].str.replace(" - ", ",") #replacing " - " with a comma,
clean_france["ingredients_text"] = clean_france["ingredients_text"].str.replace("°", "") #removing unwanted "°" symbol,
clean_france["ingredients_text"] = clean_france["ingredients_text"].str.replace("•", ",") #replacing "·" with a comma,
clean_france["ingredients_text"] = clean_france["ingredients_text"].str.replace("’", "'") #replacing "’" with "'",
clean_france["ingredients_text"] = clean_france["ingredients_text"].str.replace("⚫", ",")  #replacing "⚫" with a comma
clean_france["ingredients_text"] = clean_france["ingredients_text"].str.replace("&quot", "") #removing unwanted "&quot"
clean_france["ingredients_text"] = clean_france["ingredients_text"].str.replace(r"ingredients[^:,]{0,25}:", "", regex=True)
print(clean_france["ingredients_text"].shape)

# #removing accents in french words - we don't need french words  or special symbols in INCI, because INCI is already standardised 



def strip_accents(t):
    if not isinstance(t, str):
        return t
    return "".join(c for c in unicodedata.normalize("NFKD", t)
                   if not unicodedata.combining(c))

clean_france["ingredients_text"] = clean_france["ingredients_text"].apply(strip_accents)

#second sample fo reviewing cleaning
# sample2 = clean_france.sample(10, random_state=7)

# for name2, row2 in sample2.iterrows():
#     print("Product name", row2["product_name"], "Category name:", row2["categories_tags"])
#     print("Ingredient text:", row2["ingredients_text"], "\n")



#reviewing the longest ingredients_text - detecting if they're real ingredients written down or trash text
print(clean_france["ingredients_text"].str.len().describe()) #statistics for ingredients_text column. min: 1, max 3775. quantiles for ingredient_text: 25% - 291, 50% - 418, 75%- 561

print(clean_france["ingredients_text"].str.len().quantile([0.9, 0.95, 0.99])) #cutoff for 90% (730), 95% (846) and 99% (1359)


      
lengths = clean_france["ingredients_text"].str.len()
above_99 = clean_france[lengths > 1359] #results above 99% quantile
print(f"{len(above_99)} rows are above 99% quantile.")

for _, row in above_99.iterrows():
    print("ABOVE 99%", "\n", row["product_name"], len(row["ingredients_text"]), "characters")
    print(row["ingredients_text"], "\n")

# #overall, almost all of these records are not clean INCI list. records contain warnings, how-to-use instructions, translating for other languages or descriptions of said ingredients. these are not necessary text for ingredients list.
# #in my opinion there is no point in fixing these records - they are very small percentage of all records and it won't impact whole analysis in negative way

#saving copy without unecessary records
before = len(clean_france)
clean_france = clean_france[lengths <= 1359].copy()
print("Removed:", before - len(clean_france), "rows.") #Removed 11 rows

lengths = clean_france["ingredients_text"].str.len()
above_95 = clean_france[lengths > 846] #results above 95% quantile
print(f"{len(above_95)} rows are above 90% quantile.")

for _, row in above_95.iterrows():
     print("ABOVE 95:", "\n",row["product_name"], len(row["ingredients_text"]), "characters")
     print(row["ingredients_text"], "\n")

# #after reviewing data above 95 quantile, there can be observed interesting difference between data over 95 quantile and 99 quantile. data above 99% (with 1359 length), were just INCI list mixed with other unnecessary elements
# #however, after reviewing data above 95 quantile, it is clear, that these results are mostly longer INCI list - just products with longer ingridient list, in most cases clean data
# #some of them are containing pieces of unnecessary informations, but that can be easily cleaned up


inci_containg = clean_france[clean_france["ingredients_text"].str.contains("fil ")]

for _, row in inci_containg.iterrows():
    print(row["product_name"], "\n", row["ingredients_text"])


# print(inci_containg["ingredients_text"])


rev_text = clean_france["ingredients_text"] 

trash_words = ["f.i.l ", "fil ", "(fil ", "code fil", "(f.i.l", "(f.i.l.", "(code fil", "code (fil)", "(code f.i.l.", "(code f.i.l", "(fil:", "(fil.", "filb38770/1)", "constituants naturels" , 
               "made in", "gmbh", "d'origine", "ingredients from", "ingredients issus", "from natural", "www.", "rinse", "◊",  "naturellement", "du total", "99% d'ingredients"]

for phrase in trash_words: #reviewing text, looking for unnecessary information in ingredients_text column
    x = rev_text.str.contains(phrase, regex=False, na=False).sum()
    print(phrase, "->", x)

#result: fil (different variations) - above 130, constituants naturels - 3, made in - 7, gmbh - 3, d'origine - 22, ingredients from - 7, ingrédients issus - 43, from natural - 4, www. - 12, rinse - 1, ◊ - 1, naturellement - 11, du total - 11, 99% d'ingredients - 1]

#building function that can help determine if slice of text is supposed to be removed. showing context of needed word 
def show_context(series, phrase, n=10):
    found = series[series.str.contains(phrase, regex=False, na=False)]

    for t in found.head(n):
        i = t.find(phrase)
        print("...", t[max(0, i-60):i+60], "...")
        print()

show_context(clean_france["ingredients_text"], "naturellement")
show_context(clean_france["ingredients_text"], "f.i.l")
show_context(clean_france["ingredients_text"], "d'origine")


#cleaning text from unnecessary words/sentences

#building function to remove tail
def remove_trash_tail(t):
    if not isinstance(t, str):
        return t
    positions = []
    for marker in trash_words:
        i = t.find(marker)
        if i != -1:
            positions.append(i)
    if positions:
        cut = min(positions)
        return t[:cut].strip()
    else:
        return t




clean_france["inci_trimmed"] = clean_france["ingredients_text"].apply(remove_trash_tail)

for _, row in clean_france.iterrows():
    print(row["product_name"], "\n", "\n", row["inci_trimmed"], "\n")


#how many records were affected

rows_affected = (clean_france["ingredients_text"] != clean_france["inci_trimmed"])
print("Rows affected:", rows_affected.sum()) #.sum to see how many records are different in ingredients_text and inci_trimmed. result: 174

#preview - reviewing if every of trash word were deleted

pattern = "|".join(re.escape(w) for w in trash_words)

if_contains = clean_france["inci_trimmed"].str.contains(pattern, regex=True, na=False)
print("Marker words not deleted:", if_contains.sum()) #.sum to see hif there are any words that were not deleted, but were supposed to be deleted. result: 0

#difference between original rows and deleted rows

diff = clean_france["ingredients_text"].str.len() - clean_france["inci_trimmed"].str.len()
print("Diff describe", diff.describe())
print((diff > 0).sum(), "records deleted") #result matches rows_affected. 

#reviewing affected rows with the biggest number of characters trimmed
big_cut = clean_france[diff > 300]
print("big cut", len(big_cut))

for _, row in big_cut.iterrows():
    print(row["product_name"], "| removed:", len(row["ingredients_text"]) - len(row["inci_trimmed"]))
    print("BEFORE:", row["ingredients_text"])
    print("AFTER:", row["inci_trimmed"], "\n")

#affected rows seems good - removed parts of the text were additional informations ex. addresses, instructions, warnings etc.



#synonyms standarization dictionary
synonyms = {

#shea butter
    "butyrospermum parkii (shea) butter" : "butyrospermum parkii butter",
    "butyrospermum parkii butter / shea butter" : "butyrospermum parkii butter",
    "butyrospermum parkii butter/shea butter" : "butyrospermum parkii butter",
    "butyrospermum parkii butter (shea butter)" : "butyrospermum parkii butter",
    "butyrospermum parkii butter (shea)" : "butyrospermum parkii butter",
    "butyrospermum parkii butter (shea) butter" : "butyrospermum parkii butter",
    "butyrospermum parkii butter (shea] butter" : "butyrospermum parkii butter",

# aloe leaf juice. note "aloe leaf juice" and "aloe leaf extract" are NOT the same thing

    "aloe barbadensis leaf juice powder" : "aloe barbadensis leaf juice",
    "aloe barbadensis leaf juice" : "aloe barbadensis leaf juice",
    "aloe barbadensis aloe barbadensis/leaf juice" : "aloe barbadensis leaf juice",
    "aloe barbadensis (aloe vera) leaf juice" : "aloe barbadensis leaf juice",

#sweet almond oil
    "prunus amygdalus dulcis oil" : "prunus amygdalus dulcis oil", 
    "prunus amygdalus dulcis (sweet almond) oil" : "prunus amygdalus dulcis oil",
    "prunus amygdalus dulcis oil / sweet almond oil" : "prunus amygdalus dulcis oil", 
    "_prunus amygdalus_ dulcis (sweet _almond_) oil" : "prunus amygdalus dulcis oil",

#jojoba oil

    "simmondsia chinensis (jojoba) seed oil" : "simmondsia chinensis seed oil",
    "simmondsia chinensis oil" : "simmondsia chinensis seed oil",

#grape seed oil

    "vitis vinifera (grape) seed oil" : "vitis vinifera seed oil",

#parafinum liqiudum

    "paraffinum liquidum / mineral oil" : "paraffinum liquidum",
    "mineral oil (paraffinum liquidum)" : "paraffinum liquidum",
    "paraffinum liquidum (mineral oil)" : "paraffinum liquidum",

#sunflower oil
    "helianthus annuus (sunflower) seed oil" : "helianthus annuus seed oil"

}


#building functions to make clean list, without additional symbols or white spaces
def make_list(t):
    if not isinstance(t, str):
        return []
    items = [x.strip(" ,.;:") for x in re.split(r",(?!\d)", t)]
    return [x for x in items if x]


def normalize(s):
    s = re.sub(r"\[.*?\]", "", s)           # [fpt0666], [n2001/c]
    s = s.replace("_", "")                  # _geraniol_
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" .,;:-/*()[]")
    return s


def is_junk(s):
    if len(s) < 3 or len(s) > 80:
        return True
    if not re.search(r"[a-z]{3}", s):
        return True
    if re.search(r"\d{4,}", s) and not re.match(r"^ci \d{5}$", s):
        return True
    return False


# different variants of some ingredients: "water" and "parfum"
WATER = re.compile(r"^(aqua|water|eau)(\W+(aqua|water|eau))*$")
PARFUM = re.compile(r"^(parfum|fragrance|fragance)(\W+(parfum|fragrance|fragance))*$")

def canonical(s):
    if WATER.match(s):
        return "water"
    if PARFUM.match(s):
        return "fragrance"
    return synonyms.get(s, s)


def clean_list(items):
    out = []
    for x in items:
        x = normalize(x)
        if is_junk(x):
            continue
        x = canonical(x)
        if x not in out:                    # without duplicates by each product
            out.append(x)
    return out


clean_france["ingredients_list"] = clean_france["inci_trimmed"].apply(make_list)
clean_france["ingredients_list"] = clean_france["ingredients_list"].apply(clean_list)

#lists validation

clean_france["is_valid"] = clean_france["ingredients_list"].apply(len) >= 3

clean_france_valid = clean_france[clean_france["is_valid"]]

print("Total valid lists count:", len(clean_france_valid)) #result: 924

show_context(clean_france["inci_trimmed"], "ingredients from") #randomly verifying data after cleaning - no results - good

show_context(clean_france["inci_trimmed"], "constituants naturels") #randomly verifying data after cleaning - no results - good


#general list for all ingredients
inci_general = clean_france_valid["ingredients_list"].explode()





#top20 ingredients overall
rank_overall = (inci_general.value_counts())
print("Top20 most used ingredients - overall:", rank_overall.head(20))

#lists organized by categories tags

category_face = clean_france_valid[clean_france_valid["categories_tags"].str.contains(r"(?:^|,)en:face(?:-[^,]*)?(?:,|$)", na=False)]
category_body = clean_france_valid[clean_france_valid["categories_tags"].str.contains(r"(?:^|,)en:body(?:-[^,]*)?(?:,|$)", na=False)]
category_suncare = clean_france_valid[clean_france_valid["categories_tags"].str.contains(r"(?:^|,)en:suncare(?:-[^,]*)?(?:,|$)", na=False)]

#top20 ingredients per category
face_inci_rank = category_face["ingredients_list"].explode().value_counts()
body_inci_rank = category_body["ingredients_list"].explode().value_counts()
suncare_inci_rank = category_suncare["ingredients_list"].explode().value_counts()


#average ingredients number per category
face_inci_avg = category_face["ingredients_list"].apply(len).mean()
print(f"Average numbers of ingredients in face category: {face_inci_avg:.2f}")

body_inci_avg = category_body["ingredients_list"].apply(len).mean()
print(f"Average numbers of ingredients in body category: {body_inci_avg:.2f}")

suncare_inci_avg = category_suncare["ingredients_list"].apply(len).mean()
print(f"Average numbers of ingredients in suncare category: {suncare_inci_avg:.2f}")

all_items = clean_france["ingredients_list"].explode()

#saving file to csv
clean_france_valid.to_csv(BASE_DIR / "france_clean.csv", index=False, encoding="utf-8-sig")

#preparing table for ingredient classification
ing_table = rank_overall.reset_index()
ing_table.columns = ["ingredient", "n_product"]
ing_table["class"] = ""
ing_table.head(200).to_csv(BASE_DIR / "ingredients_to_clasify.csv", index=False, encoding="utf-8-sig", sep=";")

#saving tables for SQL and Power BI
TABLES_DIR = BASE_DIR / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

products = clean_france_valid.assign(
    n_ingredients=clean_france_valid["ingredients_list"].apply(len))[["code", "product_name", "n_ingredients"]]

pi = (clean_france_valid[["code", "ingredients_list"]]
      .explode("ingredients_list")
      .rename(columns={"ingredients_list": "ingredient"}))
pi["position"] = pi.groupby("code").cumcount() + 1

pcat = pd.concat([
    category_face.assign(category="face"),
    category_body.assign(category="body"),
    category_suncare.assign(category="suncare")])[["code", "category"]].drop_duplicates()

products.to_csv(TABLES_DIR / "products_table.csv", index=False, encoding="utf-8-sig")
pi[["code", "position", "ingredient"]].to_csv(TABLES_DIR / "product_ingredients.csv", index=False, encoding="utf-8-sig")
pcat.to_csv(TABLES_DIR / "product_categories.csv", index=False, encoding="utf-8-sig")

print("Files saved to:", TABLES_DIR.resolve())
print("Number of products:", len(products))
print("Number of product ingredients:", len(pi))
print("Number of product category assignments:", len(pcat))


#Project contains data from Open Beauty Facts, available under the Open Database License

#________________
#notes

# #ingredients name standarization - some ingredients appear twice, under slightly difftent names

# # # #shea butter
# # print(all_items[all_items.str.contains("parkii", na = False)].value_counts().head(20))
# # # "butyrospermum parkii (shea) butter", "butyrospermum parkii butter / shea butter", butyrospermum parkii butter/shea butter" butyrospermum parkii butter (shea butter), butyrospermum parkii butter (shea), butter butyrospermum parkii butter (shea butter) extract, 
# # # butyrospermum parkii butter (shea) butter, butyrospermum parkii butter (shea] butter, 

# # #  #aloe leaf juice. note "aloe leaf juice" and "aloe leaf extract" are NOT the same thing
# # print(all_items[all_items.str.contains("aloe", na = False)].value_counts().head(20))
# # # "aloe barbadensis leaf juice powder", "aloe barbadensis leaf juice", "aloe barbadensis aloe barbadensis/leaf juice", aloe barbadensis (aloe vera) leaf juice

# # #sweet almond oil
# # print(all_items[all_items.str.contains("amygdalus", na = False)].value_counts().head(20))
# # #prunus amygdalus dulcis oil, prunus amygdalus dulcis (sweet almond) oil, prunus amygdalus dulcis oil / sweet almond oil, _prunus amygdalus_ dulcis (sweet _almond_) oil

# # #simmondsia chinensis (jojoba) seed oil
# # print(all_items[all_items.str.contains("chinensis", na = False)].value_counts().head(20))
# # # simmondsia chinensis seed oil, simmondsia chinensis (jojoba) seed oil,  simmondsia chinensis oil

# # #grape seed oil
# # print(all_items[all_items.str.contains("vinifera", na = False)].value_counts().head(20))
# # #vitis vinifera (grape) seed oil, vitis vinifera seed oil, 

# # #parafinum liqiudum
# # print(all_items[all_items.str.contains("paraffinum", na = False)].value_counts().head(20))
# # # paraffinum liquidum,, paraffinum liquidum / mineral oil, mineral oil (paraffinum liquidum), paraffinum liquidum (mineral oil)

# # #sunflower oil
# # print(all_items[all_items.str.contains("annuus", na = False)].value_counts().head(20))
# # #helianthus annuus seed oil, helianthus annuus (sunflower) seed oil
