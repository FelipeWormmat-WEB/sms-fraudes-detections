import re
import numpy as np
from typing import Dict, List

class FeatureExtractor:
    """
    Extrai features adicionais do texto para melhorar a classificação.
    Features baseadas em padrões típicos de mensagens spam.
    """
    
    def __init__(self):
        # Palavras-chave de spam (PT + EN)
        self.spam_keywords = [
            # Inglês
            'free', 'win', 'winner', 'prize', 'claim', 'urgent', 'congratulations',
            'selected', 'call now', 'click here', 'limited time', 'act now',
            'cash', 'money', 'bonus', 'offer', 'txt', 'text', 'reply',
            'discount', 'guarantee', 'risk free', 'save', 'order now',
            # Português
            'gratis', 'gratuito', 'ganhe', 'ganhou', 'premio', 'premiado',
            'urgente', 'clique', 'clique aqui', 'parabens', 'selecionado',
            'oferta', 'desconto', 'dinheiro', 'bonus', 'ligue agora',
            'resgate', 'resgatar', 'confirme', 'confirmar', 'promoção',
        ]
        
        # Palavras-chave de ham (mensagens legítimas)
        self.ham_keywords = [
            # Inglês
            'thanks', 'thank you', 'sorry', 'please', 'love', 'friend',
            'family', 'meeting', 'tomorrow', 'today', 'see you',
            # Português
            'obrigado', 'obrigada', 'desculpa', 'por favor', 'amo', 'te amo',
            'amigo', 'amiga', 'familia', 'reuniao', 'amanha', 'hoje',
            'ate logo', 'tchau', 'beijo', 'abraco',
        ]
    
    def extract_features(self, text: str) -> Dict[str, float]:
        """
        Extrai múltiplas features do texto.
        
        Args:
            text: Texto original da mensagem
            
        Returns:
            Dicionário com features extraídas
        """
        features = {}
        text_lower = text.lower()
        
        # 1. Contagem de spam keywords
        features['spam_keyword_count'] = sum(
            1 for kw in self.spam_keywords if kw in text_lower
        )
        
        # 2. Contagem de ham keywords
        features['ham_keyword_count'] = sum(
            1 for kw in self.ham_keywords if kw in text_lower
        )
        
        # 3. Presença de URL
        features['has_url'] = 1.0 if re.search(r'http[s]?://|www\.', text_lower) else 0.0
        
        # 4. Presença de número de telefone
        features['has_phone'] = 1.0 if re.search(r'\b\d{4,}\b', text) else 0.0
        
        # 5. Presença de email
        features['has_email'] = 1.0 if re.search(r'\S+@\S+', text) else 0.0
        
        # 6. Presença de valor monetário
        features['has_money'] = 1.0 if re.search(r'[R$£€¥]\s?\d+', text) else 0.0
        
        # 7. Ratio de letras maiúsculas (SPAM tende a usar mais caps)
        if len(text) > 0:
            uppercase_count = sum(1 for c in text if c.isupper())
            features['uppercase_ratio'] = uppercase_count / len(text)
        else:
            features['uppercase_ratio'] = 0.0
        
        # 8. Contagem de pontuação excessiva (!!!, ???)
        features['excessive_punctuation'] = len(re.findall(r'[!?]{2,}', text))
        
        # 9. Contagem de caracteres especiais ($, £, €)
        features['special_chars'] = len(re.findall(r'[£$€¥]', text))
        
        # 10. Comprimento da mensagem
        features['message_length'] = len(text)
        
        # 11. Número de palavras
        features['word_count'] = len(text.split())
        
        # 12. Comprimento médio das palavras
        words = text.split()
        if words:
            features['avg_word_length'] = np.mean([len(w) for w in words])
        else:
            features['avg_word_length'] = 0.0
        
        # 13. Presença de palavras em CAPS LOCK
        features['has_caps_words'] = 1.0 if re.search(r'\b[A-Z]{3,}\b', text) else 0.0
        
        # 14. Densidade de dígitos
        digit_count = sum(1 for c in text if c.isdigit())
        features['digit_density'] = digit_count / len(text) if len(text) > 0 else 0.0
        
        return features
    
    def extract_features_batch(self, texts: List[str]) -> np.ndarray:
        """
        Extrai features de múltiplos textos.
        
        Args:
            texts: Lista de textos
            
        Returns:
            Array numpy com features (n_samples, n_features)
        """
        features_list = [self.extract_features(text) for text in texts]
        
        # Garantir que todas as features estão presentes
        feature_names = list(features_list[0].keys())
        
        # Converter para array numpy
        feature_matrix = np.array([
            [f[name] for name in feature_names] 
            for f in features_list
        ])
        
        return feature_matrix, feature_names


# Função auxiliar
def extract_text_features(text: str) -> Dict[str, float]:
    """Função de conveniência para extrair features de um texto único."""
    extractor = FeatureExtractor()
    return extractor.extract_features(text)