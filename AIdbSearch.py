import sqlite3
import spacy
import re

nlp = spacy.load('pl_core_news_sm')

def fetch_criteria():
    conn = sqlite3.connect('samochody.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT lower(Kolor) FROM Samochody")
    colors = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT lower(Typ_Nadwozia) FROM Samochody")
    body_types = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT lower(Rodzaj_Paliwa) FROM Samochody")
    fuel_types = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT lower(Model) FROM Samochody")
    car_models = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT lower(Marka) FROM Samochody")
    car_marks = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "colors": colors,
        "body_types": body_types,
        "fuel_types": fuel_types,
        "car_models": car_models,
        "car_marks": car_marks
    }

def parse_query(query, criteria):
    search_criteria = {
        "Kolor": None,
        "Typ_Nadwozia": None,
        "Rodzaj_Paliwa": None,
        "Rok_Produkcji": None,
        "Moc": None,
        "Marka": None,
        "Model": None
    }

    power_match = re.search(r'(\d+)(?:km)?', query)
    if power_match:
        search_criteria["Moc"] = power_match.group(1)
        query = query.replace(power_match.group(), "")

    doc = nlp(query.lower())

    colors = criteria["colors"]
    body_types = criteria["body_types"]
    fuel_types = criteria["fuel_types"]
    car_models = criteria["car_models"]
    car_marks = criteria["car_marks"]

    for token in doc:
        lemma = token.lemma_
        text = token.text

        if lemma in colors:
            search_criteria["Kolor"] = lemma
        elif lemma in body_types:
            search_criteria["Typ_Nadwozia"] = lemma
        elif text in fuel_types:
            search_criteria["Rodzaj_Paliwa"] = text
        elif token.like_num and len(token.text) == 4:
            search_criteria["Rok_Produkcji"] = token.text
        elif lemma in car_marks:
            search_criteria["Marka"] = lemma
        elif text in car_models:
            search_criteria["Model"] = text

    return {k: v for k, v in search_criteria.items() if v is not None}

def search_cars(search_criteria):
    conn = sqlite3.connect('samochody.db')
    cursor = conn.cursor()

    def build_query_and_execute(conditions, values):
        query = "SELECT * FROM Samochody WHERE " + " AND ".join(conditions)
        cursor.execute(query, values)
        return cursor.fetchall()

    conditions = []
    values = []

    for key, value in search_criteria.items():
        conditions.append(f"lower({key}) = ?")
        values.append(value)

    if not conditions:
        print("Brak kryteriów do wyszukiwania.")
        return []

    results = build_query_and_execute(conditions, values)
    if not results:
        capitalized_values = [v.capitalize() for v in values]
        results = build_query_and_execute(conditions, capitalized_values)
    
    conn.close()
    return results

def main():
    criteria = fetch_criteria()
    user_input = input("Wpisz swoje zapytanie: ")
    search_criteria = parse_query(user_input, criteria)
    
    if not search_criteria:
        print("Brak kryteriów do wyszukiwania.")
        return
    
    results = search_cars(search_criteria)
    
    if not results:
        print("Brak wyników dla podanego zapytania.")
    else:
        for result in results:
            print(result)

if __name__ == "__main__":
    main()