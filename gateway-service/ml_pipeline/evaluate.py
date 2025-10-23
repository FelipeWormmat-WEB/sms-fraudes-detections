import json
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

class ModelEvaluator:
    """
    Classe para avaliar e visualizar métricas do modelo treinado.
    Gera gráficos e relatórios para apresentação do TCC.
    """
    
    def __init__(self, models_dir: str = "../models"):
        self.models_dir = Path(models_dir)
        self.metrics = self.load_metrics()
    
    def load_metrics(self):
        """Carrega as métricas salvas."""
        metrics_path = self.models_dir / "metrics.json"
        
        if not metrics_path.exists():
            print(f"❌ Arquivo de métricas não encontrado: {metrics_path}")
            return None
        
        with open(metrics_path, "r") as f:
            return json.load(f)
    
    def plot_confusion_matrix(self, save_path: str = None):
        """Gera gráfico da matriz de confusão."""
        if not self.metrics:
            print("❌ Métricas não carregadas")
            return
        
        cm = np.array(self.metrics['confusion_matrix'])
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm, 
            annot=True, 
            fmt='d', 
            cmap='Blues',
            xticklabels=['Ham', 'Spam'],
            yticklabels=['Ham', 'Spam'],
            cbar_kws={'label': 'Quantidade'}
        )
        plt.title('Matriz de Confusão - Detecção de Spam', fontsize=14, fontweight='bold')
        plt.ylabel('Classe Real', fontsize=12)
        plt.xlabel('Classe Prevista', fontsize=12)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ Matriz de confusão salva em: {save_path}")
        else:
            plt.savefig(self.models_dir / "confusion_matrix.png", dpi=300, bbox_inches='tight')
            print(f"✅ Matriz de confusão salva em: {self.models_dir / 'confusion_matrix.png'}")
        
        plt.close()
    
    def plot_metrics_comparison(self, save_path: str = None):
        """Gera gráfico de barras com as métricas."""
        if not self.metrics:
            print("❌ Métricas não carregadas")
            return
        
        metrics_values = [
            self.metrics['accuracy'],
            self.metrics['precision'],
            self.metrics['recall'],
            self.metrics['f1_score']
        ]
        
        metrics_names = ['Acurácia', 'Precisão', 'Recall', 'F1-Score']
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(metrics_names, metrics_values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        
        # Adicionar valores nas barras
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2., 
                height,
                f'{height:.2%}',
                ha='center', 
                va='bottom',
                fontsize=12,
                fontweight='bold'
            )
        
        plt.ylim(0, 1.1)
        plt.ylabel('Score', fontsize=12)
        plt.title(f'Métricas do Modelo - {self.metrics["model_type"]}', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ Gráfico de métricas salvo em: {save_path}")
        else:
            plt.savefig(self.models_dir / "metrics_comparison.png", dpi=300, bbox_inches='tight')
            print(f"✅ Gráfico de métricas salvo em: {self.models_dir / 'metrics_comparison.png'}")
        
        plt.close()
    
    def generate_report(self):
        """Gera relatório textual das métricas."""
        if not self.metrics:
            print("❌ Métricas não carregadas")
            return
        
        report = f"""
            {'='*80}
            RELATÓRIO DE AVALIAÇÃO DO MODELO
            {'='*80}

            Modelo: {self.metrics['model_type']}
            Data de Treinamento: {self.metrics['timestamp']}

            MÉTRICAS DE DESEMPENHO:
            {'─'*80}
            Acurácia:          {self.metrics['accuracy']:.4f} ({self.metrics['accuracy']*100:.2f}%)
            Precisão:          {self.metrics['precision']:.4f} ({self.metrics['precision']*100:.2f}%)
            Recall:            {self.metrics['recall']:.4f} ({self.metrics['recall']*100:.2f}%)
            F1-Score:          {self.metrics['f1_score']:.4f} ({self.metrics['f1_score']*100:.2f}%)

            VALIDAÇÃO CRUZADA (5-FOLD):
            {'─'*80}
            Média:             {self.metrics['cv_mean']:.4f} ({self.metrics['cv_mean']*100:.2f}%)
            Desvio Padrão:     {self.metrics['cv_std']:.4f}

            MATRIZ DE CONFUSÃO:
            {'─'*80}
                                Previsto
                            Ham      Spam
            Real    Ham     {self.metrics['confusion_matrix'][0][0]:<8} {self.metrics['confusion_matrix'][0][1]:<8}
                    Spam    {self.metrics['confusion_matrix'][1][0]:<8} {self.metrics['confusion_matrix'][1][1]:<8}

            ANÁLISE:
            {'─'*80}
            ✅ Verdadeiros Negativos (Ham → Ham):    {self.metrics['confusion_matrix'][0][0]}
            ⚠️  Falsos Positivos (Ham → Spam):       {self.metrics['confusion_matrix'][0][1]}
            ⚠️  Falsos Negativos (Spam → Ham):       {self.metrics['confusion_matrix'][1][0]}
            ✅ Verdadeiros Positivos (Spam → Spam):  {self.metrics['confusion_matrix'][1][1]}

            {'='*80}
            """
        
        report_path = self.models_dir / "model_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(report)
        print(f"✅ Relatório salvo em: {report_path}")
    
    def generate_all_visualizations(self):
        """Gera todas as visualizações."""
        print("\n📊 Gerando visualizações...")
        self.plot_confusion_matrix()
        self.plot_metrics_comparison()
        self.generate_report()
        print("\n✅ Todas as visualizações geradas com sucesso!")


if __name__ == "__main__":
    evaluator = ModelEvaluator()
    evaluator.generate_all_visualizations()