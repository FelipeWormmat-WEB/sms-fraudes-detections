import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report
import pickle

# Caminho absoluto para a pasta datasets
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets"))

files = [
    os.path.join(BASE_DIR, "2.csv"),
]

dfs = []
for f in files:
    try:
        df = pd.read_csv(f, encoding="utf-8", on_bad_lines='skip')
        dfs.append(df)
        print(f"Lido com sucesso: {f}")
    except Exception as e:
        print(f"Erro ao ler {f}: {e}")

if not dfs:
    raise ValueError("Nenhum dataset pôde ser lido! Verifique os caminhos dos arquivos.")

full_df = pd.concat(dfs, ignore_index=True)

if 'label' not in full_df.columns or 'message' not in full_df.columns:
    # Divide a primeira coluna pelo primeiro TAB encontrado
    full_df[['label', 'message']] = full_df.iloc[:,0].str.split('\t', n=1, expand=True)
    print("Colunas corrigidas usando split por TAB")

full_df = full_df.dropna(subset=['label', 'message'])

X = full_df['message'].astype(str)
y = full_df['label'].astype(str)


print("\nDistribuição das classes:")
print(y.value_counts())

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

vectorizer = TfidfVectorizer(stop_words=None, max_features=5000, ngram_range=(1, 2))
X_train_vect = vectorizer.fit_transform(X_train)
X_test_vect = vectorizer.transform(X_test)

# Modelo Naive Bayes
model = MultinomialNB()
model.fit(X_train_vect, y_train)

y_pred = model.predict(X_test_vect)
print("\n📊 Resultados do Modelo:")
print("Acurácia:", accuracy_score(y_test, y_pred))
print("Relatório de Classificação:\n", classification_report(y_test, y_pred))

models_dir = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(models_dir, exist_ok=True)

model_file = os.path.join(models_dir, "sms_classifier.pkl")
vectorizer_file = os.path.join(models_dir, "vectorizer.pkl")

with open(model_file, "wb") as f:
    pickle.dump(model, f)

with open(vectorizer_file, "wb") as f:
    pickle.dump(vectorizer, f)

print("\n✅ Modelo e vetorizer salvos em 'gateway-service/models/'")
