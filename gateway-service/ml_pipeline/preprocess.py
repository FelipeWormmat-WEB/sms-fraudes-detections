import re
import string
from typing import List

class TextPreprocessor:
    """
    Classe para pré-processar textos de SMS para detecção de spam.
    Aplica técnicas de NLP para normalizar e limpar o texto.
    """
    
    def __init__(self):
        # Stopwords em português e inglês
        self.stopwords = set([
            # Português
            'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 
            'é', 'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais',
            'as', 'dos', 'como', 'mas', 'ao', 'ele', 'das', 'à', 'seu', 'sua',
            'ou', 'quando', 'muito', 'nos', 'já', 'eu', 'também', 'só', 'pelo',
            'pela', 'até', 'isso', 'ela', 'entre', 'depois', 'sem', 'mesmo',
            'aos', 'seus', 'quem', 'nas', 'me', 'esse', 'eles', 'você', 'essa',
            'num', 'nem', 'suas', 'meu', 'às', 'minha', 'numa', 'pelos', 'elas',
            # Inglês
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was',
            'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'of', 'and', 'or', 'but', 'in', 'with', 'to', 'from', 'by', 'for',
            'about', 'into', 'through', 'during', 'before', 'after', 'above',
        ])
        
    def clean_text(self, text: str) -> str:
        """
        Limpa e normaliza o texto.
        
        Args:
            text: Texto original
            
        Returns:
            Texto limpo e normalizado
        """
        if not isinstance(text, str):
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Substituir URLs por token
        text = re.sub(r'http[s]?://\S+|www\.\S+', ' URL ', text)
        
        # Substituir números de telefone por token
        text = re.sub(r'\b\d{4,}\b', ' PHONE ', text)
        
        # Substituir emails por token
        text = re.sub(r'\S+@\S+', ' EMAIL ', text)
        
        # Substituir valores monetários por token
        text = re.sub(r'[R$£€¥]\s?\d+[,.]?\d*', ' MONEY ', text)
        
        # Remover pontuação excessiva mas manter uma
        text = re.sub(r'([!?.]){2,}', r'\1', text)
        
        # Remover caracteres especiais (mantém letras, números e espaços)
        text = re.sub(r'[^a-záàâãéèêíïóôõöúçñ0-9\s]', ' ', text)
        
        # Remover números isolados
        text = re.sub(r'\b\d+\b', '', text)
        
        # Remover espaços múltiplos
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def remove_stopwords(self, text: str) -> str:
        """
        Remove stopwords do texto.
        
        Args:
            text: Texto já limpo
            
        Returns:
            Texto sem stopwords
        """
        words = text.split()
        # Mantém palavras com mais de 2 caracteres que não sejam stopwords
        filtered = [w for w in words if w not in self.stopwords and len(w) > 2]
        return ' '.join(filtered)
    
    def preprocess(self, text: str, remove_stops: bool = True) -> str:
        """
        Pipeline completo de pré-processamento.
        
        Args:
            text: Texto original
            remove_stops: Se deve remover stopwords
            
        Returns:
            Texto pré-processado
        """
        text = self.clean_text(text)
        if remove_stops:
            text = self.remove_stopwords(text)
        return text
    
    def preprocess_batch(self, texts: List[str], remove_stops: bool = True) -> List[str]:
        """
        Pré-processa uma lista de textos.
        
        Args:
            texts: Lista de textos
            remove_stops: Se deve remover stopwords
            
        Returns:
            Lista de textos pré-processados
        """
        return [self.preprocess(t, remove_stops) for t in texts]


# Função auxiliar para uso rápido
def preprocess_text(text: str) -> str:
    """Função de conveniência para pré-processar um texto único."""
    preprocessor = TextPreprocessor()
    return preprocessor.preprocess(text)