import os
import sys
import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)
from scipy.sparse import hstack

from preprocess import TextPreprocessor
from features import FeatureExtractor

class SMSSpamClassifier:
    """
    Sistema completo de classificação de spam em SMS.
    Inclui pré-processamento, feature engineering e treinamento de modelos.
    """
    
    def __init__(self, dataset_path: str, models_dir: str = "../models"):
        self.dataset_path = dataset_path
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        self.preprocessor = TextPreprocessor()
        self.feature_extractor = FeatureExtractor()
        self.vectorizer = None
        self.model = None
        self.feature_names = None
        self.metrics = {}
        
    def load_data(self):
        """Carrega e valida o dataset."""
        print("📂 Carregando dataset...")
        
        try:
            df = pd.read_csv(
                self.dataset_path, 
                sep='\t', 
                header=None, 
                names=['label', 'message'],
                encoding='utf-8'
            )
            
            # Limpeza básica
            df = df.dropna(subset=['label', 'message'])
            df['label'] = df['label'].str.lower().str.strip()
            df = df[df['label'].isin(['spam', 'ham'])]
            
            print(f"✅ Dataset carregado: {len(df)} mensagens")
            print(f"\n📊 Distribuição das classes:")
            print(df['label'].value_counts())
            print(f"\nBalanceamento: {df['label'].value_counts(normalize=True).round(3).to_dict()}")
            
            return df
            
        except Exception as e:
            print(f"❌ Erro ao carregar dataset: {e}")
            sys.exit(1)
    
    def preprocess_data(self, df):
        """Aplica pré-processamento nos textos."""
        print("\n🔧 Aplicando pré-processamento...")
        
        # Pré-processar textos
        df['processed_text'] = self.preprocessor.preprocess_batch(df['message'].tolist())
        
        # Extrair features adicionais
        print("🔧 Extraindo features adicionais...")
        features_array, self.feature_names = self.feature_extractor.extract_features_batch(
            df['message'].tolist()
        )
        
        # Adicionar features ao dataframe
        for i, fname in enumerate(self.feature_names):
            df[fname] = features_array[:, i]
        
        print(f"✅ {len(self.feature_names)} features extraídas")
        
        return df
    
    def prepare_features(self, df):
        """Prepara features para treinamento."""
        print("\n🔤 Vetorizando textos com TF-IDF...")
        
        X_text = df['processed_text']
        X_features = df[self.feature_names].values
        y = df['label']
        
        # Dividir em treino e teste (estratificado)
        X_text_train, X_text_test, X_feat_train, X_feat_test, y_train, y_test = train_test_split(
            X_text, X_features, y,
            test_size=0.2,
            random_state=42,
            stratify=y
        )
        
        # TF-IDF
        self.vectorizer = TfidfVectorizer(
            max_features=3000,
            ngram_range=(1, 2),  # Unigrams e bigrams
            min_df=2,
            max_df=0.8,
            strip_accents='unicode'
        )
        
        X_text_train_vec = self.vectorizer.fit_transform(X_text_train)
        X_text_test_vec = self.vectorizer.transform(X_text_test)
        
        # Combinar features textuais + features adicionais
        X_train = hstack([X_text_train_vec, X_feat_train])
        X_test = hstack([X_text_test_vec, X_feat_test])
        
        print(f"✅ Vocabulário: {len(self.vectorizer.vocabulary_)} palavras")
        print(f"✅ Features totais: {X_train.shape[1]}")
        print(f"✅ Treino: {X_train.shape[0]} amostras")
        print(f"✅ Teste: {X_test.shape[0]} amostras")
        
        return X_train, X_test, y_train, y_test
    
    def train_models(self, X_train, X_test, y_train, y_test):
        """Treina múltiplos modelos e escolhe o melhor."""
        print("\n🤖 Treinando modelos...")
        
        models = {
            'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42, C=1.0),
            'Naive Bayes': MultinomialNB(alpha=0.1),
            'Linear SVM': LinearSVC(max_iter=2000, random_state=42, C=1.0),
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, max_depth=20)
        }
        
        results = {}
        
        for name, model in models.items():
            print(f"\n📈 {name}:")
            
            # Treinar
            model.fit(X_train, y_train)
            
            # Predição
            y_pred = model.predict(X_test)
            
            # Métricas
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, pos_label='spam')
            rec = recall_score(y_test, y_pred, pos_label='spam')
            f1 = f1_score(y_test, y_pred, pos_label='spam')
            
            # Validação cruzada (5-fold)
            cv_scores = cross_val_score(
                model, X_train, y_train, 
                cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
                scoring='accuracy'
            )
            
            results[name] = {
                'model': model,
                'accuracy': acc,
                'precision': prec,
                'recall': rec,
                'f1_score': f1,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'y_pred': y_pred
            }
            
            print(f"   Acurácia: {acc:.4f}")
            print(f"   Precisão: {prec:.4f}")
            print(f"   Recall: {rec:.4f}")
            print(f"   F1-Score: {f1:.4f}")
            print(f"   CV (5-fold): {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
        
        # Escolher melhor modelo por F1-Score
        best_name = max(results, key=lambda k: results[k]['f1_score'])
        self.model = results[best_name]['model']
        self.metrics = results[best_name]
        
        print(f"\n🏆 Melhor modelo: {best_name}")
        print(f"   F1-Score: {self.metrics['f1_score']:.4f}")
        
        return best_name, results, y_test, self.metrics['y_pred']
    
    def evaluate_model(self, y_test, y_pred):
        """Avaliação detalhada do modelo."""
        print("\n" + "="*80)
        print("📊 AVALIAÇÃO DETALHADA DO MODELO")
        print("="*80)
        
        # Classification Report
        print("\n📋 Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['ham', 'spam']))
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred, labels=['ham', 'spam'])
        print("\n🔢 Confusion Matrix:")
        print(f"                  Predito")
        print(f"                Ham    Spam")
        print(f"Real   Ham     {cm[0,0]:<6} {cm[0,1]:<6}")
        print(f"       Spam    {cm[1,0]:<6} {cm[1,1]:<6}")
        
        print(f"\n✅ Verdadeiros Negativos (ham correto): {cm[0,0]}")
        print(f"⚠️  Falsos Positivos (ham como spam): {cm[0,1]}")
        print(f"⚠️  Falsos Negativos (spam como ham): {cm[1,0]}")
        print(f"✅ Verdadeiros Positivos (spam correto): {cm[1,1]}")
        
        # Salvar confusion matrix
        self.metrics['confusion_matrix'] = cm.tolist()
    
    def test_generalization(self):
        """Testa o modelo com mensagens não vistas."""
        print("\n" + "="*80)
        print("🧪 TESTE DE GENERALIZAÇÃO")
        print("="*80)
        
        test_messages = [
            ("PARABÉNS! Você ganhou R$ 50.000! Clique aqui URGENTE!", "spam"),
            ("Oi tudo bem? Vamos almoçar amanhã às 12h?", "ham"),
            ("FREE iPhone! Click here to claim your prize NOW!", "spam"),
            ("Thanks for yesterday, you're amazing!", "ham"),
            ("URGENTE: Seu CPF tem pendências. Ligue 0800-999-9999", "spam"),
            ("Obrigado pela ajuda ontem, você é demais!", "ham"),
            ("Win £1000 cash! Text WIN to 12345 now!", "spam"),
            ("See you tomorrow at the meeting, don't forget!", "ham"),
        ]
        
        print("\nTestando mensagens não vistas no treinamento:\n")
        
        correct = 0
        for msg, expected in test_messages:
            # Preprocessar
            processed = self.preprocessor.preprocess(msg)
            
            # Vetorizar
            vec = self.vectorizer.transform([processed])
            
            # Extrair features
            feats = np.array([list(self.feature_extractor.extract_features(msg).values())])
            
            # Combinar
            combined = hstack([vec, feats])
            
            # Predizer
            pred = self.model.predict(combined)[0]
            
            # Probabilidade
            try:
                proba = self.model.predict_proba(combined)[0]
                conf = max(proba)
                status = "✅" if pred == expected else "❌"
                correct += (pred == expected)
                print(f"{status} '{msg[:50]}...'")
                print(f"   Real: {expected} | Previsto: {pred} (confiança: {conf:.2%})\n")
            except:
                status = "✅" if pred == expected else "❌"
                correct += (pred == expected)
                print(f"{status} '{msg[:50]}...'")
                print(f"   Real: {expected} | Previsto: {pred}\n")
        
        acc = correct / len(test_messages)
        print(f"Acurácia na generalização: {acc:.2%} ({correct}/{len(test_messages)})")
    
    def save_model(self):
        """Salva o modelo e componentes."""
        print("\n💾 Salvando modelo...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salvar modelo
        model_path = self.models_dir / "best_classifier.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(self.model, f)
        
        # Salvar vectorizer
        vectorizer_path = self.models_dir / "tfidf_vectorizer.pkl"
        with open(vectorizer_path, "wb") as f:
            pickle.dump(self.vectorizer, f)
        
        # Salvar feature names
        features_path = self.models_dir / "feature_names.pkl"
        with open(features_path, "wb") as f:
            pickle.dump(self.feature_names, f)
        
        # Salvar métricas
        metrics_to_save = {
            'accuracy': float(self.metrics['accuracy']),
            'precision': float(self.metrics['precision']),
            'recall': float(self.metrics['recall']),
            'f1_score': float(self.metrics['f1_score']),
            'cv_mean': float(self.metrics['cv_mean']),
            'cv_std': float(self.metrics['cv_std']),
            'confusion_matrix': self.metrics['confusion_matrix'],
            'timestamp': timestamp,
            'model_type': type(self.model).__name__
        }
        
        metrics_path = self.models_dir / "metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics_to_save, f, indent=2)
        
        print(f"✅ Modelo salvo: {model_path}")
        print(f"✅ Vectorizer salvo: {vectorizer_path}")
        print(f"✅ Métricas salvas: {metrics_path}")
    
    def run_pipeline(self):
        """Executa o pipeline completo."""
        print("\n" + "="*80)
        print("🚀 INICIANDO PIPELINE DE TREINAMENTO")
        print("="*80)
        
        # 1. Carregar dados
        df = self.load_data()
        
        # 2. Pré-processar
        df = self.preprocess_data(df)
        
        # 3. Preparar features
        X_train, X_test, y_train, y_test = self.prepare_features(df)
        
        # 4. Treinar modelos
        best_name, results, y_test, y_pred = self.train_models(X_train, X_test, y_train, y_test)
        
        # 5. Avaliar
        self.evaluate_model(y_test, y_pred)
        
        # 6. Testar generalização
        self.test_generalization()
        
        # 7. Salvar
        self.save_model()

        # Teste rápido
        test_msg = "Urgente! Seu PIX foi bloqueado. Clique no link para desbloquear: http://fake.com"
        processed = self.preprocessor.preprocess(test_msg)
        vec = self.vectorizer.transform([processed])
        feats = np.array([list(self.feature_extractor.extract_features(test_msg).values())])
        combined = hstack([vec, feats])
        pred = self.model.predict(combined)[0]
        conf = max(self.model.predict_proba(combined)[0])
        print(f"Teste: '{test_msg}' → {pred} (conf: {conf:.2%})")
        
        print("\n" + "="*80)
        print("🎉 TREINAMENTO CONCLUÍDO COM SUCESSO!")
        print("="*80)
        print(f"\n📊 Resumo Final:")
        print(f"   Modelo: {type(self.model).__name__}")
        print(f"   Acurácia: {self.metrics['accuracy']:.2%}")
        print(f"   Precisão: {self.metrics['precision']:.2%}")
        print(f"   Recall: {self.metrics['recall']:.2%}")
        print(f"   F1-Score: {self.metrics['f1_score']:.2%}")
        print(f"\n✅ Modelo pronto para uso em produção!")
        print(f"✅ Arquivos salvos em: {self.models_dir}")


if __name__ == "__main__":
    # Configurar caminhos
    base_dir = Path(__file__).parent.parent
    dataset_path = base_dir / "classification-service" / "datasets" / "2.csv"
    models_dir = base_dir / "models"
    
    # Criar e executar pipeline
    classifier = SMSSpamClassifier(
        dataset_path=r"C:\Users\felip\Desktop\sms-fraudes-detections\classification-service\datasets\2.csv",
        models_dir=str(models_dir)
    )
    
    classifier.run_pipeline()