import os
import logging
import ocrmypdf
import PyPDF2
from paddleocr import PaddleOCR
import re

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_processing.log'),
        logging.StreamHandler()
    ]
)

class PDFProcessor:
    def __init__(self):
        # Configurações otimizadas para português brasileiro
        self.ocr_config = {
            'use_angle_cls': True,
            'lang': 'pt',
            'detect_orientation': True,  # Detecta orientação do texto
            'enable_mkldnn': True,       # Aceleração de hardware
            'use_gpu': False             # Altere para True se tiver GPU compatível
        }
        self.ocr_engine = PaddleOCR(**self.ocr_config)
        
        # Expressão regular para limpeza de texto
        self.clean_regex = re.compile(r'[^\w\sà-úÀ-Úâ-ûÂ-Ûã-õÃ-Õá-éÁ-Éí-óÍ-Óô-úÔ-ÚçÇ.,;:!?()-]')

    def is_searchable(self, pdf_path):
        """Verifica se o PDF contém texto pesquisável de forma confiável"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Verificação combinada de fontes e conteúdo
                if any('/Font' in page.get('/Resources', {}) for page in reader.pages[:3]):
                    return True
                
                # Verificação de conteúdo textual
                text = ''.join([page.extract_text() or '' for page in reader.pages[:3]])
                return len(text.strip()) > 100  # Limite seguro
                
        except Exception as e:
            logging.error(f"Erro na verificação de texto pesquisável: {e}")
            return False

    def _clean_text(self, text):
        """Limpeza avançada do texto OCR"""
        try:
            # Normalização de caracteres
            text = self.clean_regex.sub('', text)
            
            # Correção de espaçamento em pontuações
            text = re.sub(r'\s+([.,;:!?)])', r'\1', text)
            text = re.sub(r'([(])\s+', r'\1', text)
            
            # Unificação de espaços e hifens
            text = re.sub(r'[\-\u2010-\u2015]', '-', text)
            text = ' '.join(text.split())
            
            return text.strip()
        
        except Exception as e:
            logging.error(f"Erro na limpeza de texto: {e}")
            return text

    def process_pdf(self, input_path):
        """
        Processa o PDF com OCR e extração otimizada
        Retorna o texto limpo e estruturado
        """
        try:
            if not os.path.isfile(input_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

            output_path = os.path.splitext(input_path)[0] + "_ocr.pdf"
            
            # Configurações otimizadas para documentos brasileiros
            ocrmypdf_config = {
                'language': 'por+eng',     # Prioriza português mas considera inglês
                'deskew': True,
                'rotate_pages': True,
                'clean': True,
                'optimize': 3,
                'output_type': 'pdfa',
                'progress_bar': False,
                'oversample': 300           # Melhora resolução para documentos escaneados
            }

            if not self.is_searchable(input_path):
                logging.info("Aplicando OCR com otimizações...")
                ocrmypdf.ocr(input_path, output_path, **ocrmypdf_config)
            else:
                output_path = input_path
                logging.info("Documento já pesquisável, pulando OCR")

            # Extração de texto com PaddleOCR
            logging.info("Extraindo e processando texto...")
            result = self.ocr_engine.ocr(output_path, cls=True)
            
            # Processamento do resultado
            full_text = []
            for page in result:
                page_text = []
                for line in page:
                    text = line[1][0]
                    confidence = line[1][1]
                    if confidence > 0.6:  # Filtro de qualidade
                        page_text.append(self._clean_text(text))
                full_text.append(' '.join(page_text))
            
            return '\n\n'.join(full_text)

        except Exception as e:
            logging.critical(f"Falha crítica no processamento: {e}")
            return ''

if __name__ == "__main__":
    processor = PDFProcessor()
    
    pdf_path = "edital_A06_2024.pdf"
    if not os.path.exists(pdf_path):
        logging.error("Arquivo de entrada não encontrado!")
        exit(1)
        
    try:
        texto = processor.process_pdf(pdf_path)
        output_file = "texto_processado.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(texto)
            
        logging.info(f"Processamento concluído. Resultado salvo em: {output_file}")
        logging.info(f"Total de caracteres extraídos: {len(texto)}")
        
    except KeyboardInterrupt:
        logging.warning("Processo interrompido pelo usuário!")