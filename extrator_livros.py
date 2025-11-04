import requests
import time
import json
import logging
import sys 
import os
from dotenv import load_dotenv # Para carregar variáveis de ambiente de .env
import csv
from tabulate import tabulate
from typing import Optional, Dict, Any, List

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variáveis Globais de Configuração
# A chave de API agora é carregada de .env
API_KEY = os.environ.get('GEMINI_API_KEY') 
GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"
MAX_RETRIES = 3

# URLs de APIs
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

# ----------------------------------------------------------------------
# FUNÇÃO UTILITÁRIA: FORMATAR MOEDA
# ----------------------------------------------------------------------

def format_currency(price_str: str) -> str:
    """
    Limpa e formata uma string de preço no padrão brasileiro "R$ XX,XX".
    Se a string não puder ser convertida, retorna a string original.
    """
    if not price_str or "N/A" in price_str:
        return price_str

    try:
        # Remove símbolos de moeda (R$, $) e espaços
        cleaned_str = price_str.replace('R$', '').replace('$', '').strip()
        
        # Tenta detectar o separador decimal (ponto para milhar, vírgula para decimal, ou vice-versa)
        if ',' in cleaned_str and '.' in cleaned_str:
            # Caso complexo: verifica qual é o separador decimal
            if cleaned_str.rfind(',') > cleaned_str.rfind('.'):
                # Vírgula é o decimal (padrão BR): 1.234,56
                cleaned_str = cleaned_str.replace('.', '').replace(',', '.')
            else:
                # Ponto é o decimal (padrão US): 1,234.56
                cleaned_str = cleaned_str.replace(',', '') # Remove vírgula de milhar
        elif ',' in cleaned_str:
            # Apenas vírgula, assume que é decimal (ex: 49,90)
            cleaned_str = cleaned_str.replace(',', '.')
        
        # Converte para float e formata como moeda BRL
        value = float(cleaned_str)
        # Formata para duas casas decimais com separador de milhar e vírgula decimal
        return f"R$ {value:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

    except ValueError:
        # Retorna a string original se a conversão falhar (ex: texto não numérico)
        logging.warning(f"Falha ao formatar o preço: '{price_str}'. Retornando valor original.")
        return price_str

# ----------------------------------------------------------------------
# FASE 1: EXTRAÇÃO DE METADADOS (APIs Públicas de Livros - Google Books API)
# ----------------------------------------------------------------------

def search_google_books_api(ean: str) -> Dict[str, str]:
    """
    Busca metadados de livros (Título, Autor, Editora) usando a Google Books API.
    
    CORREÇÃO DE TÍTULO: Inclui o subtítulo se ele existir no JSON da API.

    Args:
        ean: O Código EAN/ISBN do livro.

    Returns:
        Um dicionário contendo 'EAN/ISBN', 'titulo', 'autor' e 'editora'. 
        Retorna "Não Encontrado" para campos ausentes ou em caso de falha.
    """
    logging.info(f"Fase 1: Buscando metadados para EAN/ISBN: {ean}...")
    
    metadata = {
        "EAN/ISBN": ean,
        "titulo": "Não Encontrado",
        "autor": "Não Encontrado",
        "editora": "Não Encontrado"
    }
    
    try:
        url = f"{GOOGLE_BOOKS_API_URL}?q=isbn:{ean}"
        response = requests.get(url, timeout=10)
        
        # Garante que a requisição HTTP foi bem sucedida (código 200)
        response.raise_for_status() 
        data = response.json()

        if data.get('items'):
            item = data['items'][0]['volumeInfo']
            
            titulo_principal = item.get('title')
            subtitulo = item.get('subtitle')
            autores = item.get('authors', [])
            editora = item.get('publisher')

            # Lógica de concatenação de Título e Subtítulo
            if titulo_principal and subtitulo:
                titulo_completo = f"{titulo_principal} - {subtitulo}"
            elif titulo_principal:
                titulo_completo = titulo_principal
            else:
                titulo_completo = "Não Encontrado"


            metadata["titulo"] = titulo_completo
            metadata["autor"] = ", ".join(autores) if autores else "Não Encontrado"
            metadata["editora"] = editora if editora else "Não Encontrado"
            
            logging.info("Metadados encontrados com sucesso.")
            return metadata
        else:
            logging.warning("Nenhum livro encontrado na Google Books API.")
            return metadata # Retorna metadados vazios/padrão

    except requests.exceptions.RequestException as e:
        # Loga o erro, mas retorna o dicionário de metadados padrão para continuar o processo
        logging.error(f"Erro de requisição/HTTP na Fase 1 para {ean}: {e}")
        return metadata 
    except Exception as e:
        # Loga qualquer outro erro (parsing de JSON, etc.) e retorna o dicionário padrão
        logging.error(f"Erro inesperado na Fase 1 para {ean}: {e}")
        return metadata 

# ----------------------------------------------------------------------
# FASE 2: EXTRAÇÃO DE PREÇOS (Gemini API Otimizada)
# ----------------------------------------------------------------------

def call_gemini_api_otimizada(ean: str, api_key: str) -> Dict[str, str]:
    """
    Envia requisição para a Gemini API com Search Grounding para extrair APENAS preços (Fase 2).

    Args:
        ean: O Código EAN/ISBN do produto.
        api_key: A chave da API do Gemini carregada do .env.

    Returns:
        Um objeto JSON contendo APENAS os preços (garantido como strings), ou um dicionário vazio ({}) em caso de falha.
    """
    if not api_key:
        return {} # Retorna dicionário vazio em caso de chave ausente

    # URL da API do Gemini
    api_url = f"{GEMINI_BASE_URL}/{GEMINI_MODEL}:generateContent?key={api_key}"
    logging.info(f"Fase 2: Buscando preços para EAN/ISBN: {ean}...")

    # NOVO SYSTEM PROMPT: Focado em preço e com instrução para tentar outros varejistas
    system_prompt = "Você é um extrator de APENAS PREÇOS de e-commerce, especialista em localizar e extrair informações dinâmicas com base no EAN/ISBN. Use o Google Search para buscar PRIMEIRO na Amazon Brasil, e se o preço não for encontrado, procure em outros grandes varejistas brasileiros (como Submarino, Livraria Cultura, etc.). SUA TAREFA É ESTRITAMENTE EXTRAIR PREÇOS. NÃO RETORNE TÍTULO, AUTOR OU EDITORAS. CAMPOS OBRIGATÓRIOS (APENAS): 'precoSemDesconto' e 'precoComDesconto'. Se o 'precoComDesconto' não for encontrado, use o valor de 'precoSemDesconto'. Se NENHUM preço for encontrado na fonte, retorne O OBJETO JSON VAZIO: {}. Retorne APENAS o objeto JSON, sem nenhum texto introdutório ou código markdown (e.g., sem ```json)."

    # NOVA USER QUERY: Simplificada para guiar a busca apenas para preços
    user_query = f"BUSCA DE PREÇOS (Amazon.com.br): EAN/ISBN {ean}. Extrair estritamente apenas o preço sem e com desconto."

    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        # Ferramenta de Google Search Grounding ativada
        "tools": [{"google_search": {}}], 
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }

    headers = {'Content-Type': 'application/json'}

    for attempt in range(MAX_RETRIES):
        try:
            # Implementação do NOVO timeout de 35 segundos (aumento da resiliência)
            response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=35)
            response_code = response.status_code

            if response_code == 200:
                json_response = response.json()
                candidate = json_response.get('candidates', [None])[0]

                if candidate and candidate.get('content', {}).get('parts', [None])[0]:
                    json_text = candidate['content']['parts'][0]['text']

                    # Limpeza CRUCIAL: remove markdown code fences (```json, ```) e espaços extras
                    cleaned_json_text = json_text.replace("```json", "").replace("```", "").strip()
                    
                    try:
                        result_object = json.loads(cleaned_json_text)
                        
                        # A IA deve retornar {} se o preço não for encontrado
                        if not result_object:
                            logging.warning("Busca de preço falhou: IA retornou objeto JSON vazio ({}).")
                            return {}

                        # CORREÇÃO DE TIPO: Garante que todos os valores de preço sejam strings
                        for key, value in result_object.items():
                            if isinstance(value, (int, float)):
                                result_object[key] = str(value)

                        # Adiciona o campo precoComDesconto se estiver faltando (conforme o prompt)
                        if 'precoComDesconto' not in result_object and 'precoSemDesconto' in result_object:
                             result_object['precoComDesconto'] = result_object['precoSemDesconto']

                        logging.info("Preços extraídos com sucesso.")
                        return result_object
                    except json.JSONDecodeError:
                        logging.error("ERRO DE PARSE: O retorno da IA não era JSON limpo.")
                        logging.error(f"Texto recebido: {json_text}")
                        return {} # Retorna dicionário vazio em caso de erro de JSON
                else:
                    logging.error("Erro: Resposta JSON da IA vazia ou mal formatada.")
                    return {} # Retorna dicionário vazio em caso de resposta vazia

            elif response_code == 429:
                delay = 2 ** attempt
                # Implementação de Exponential Backoff
                logging.warning(f"Atingido Rate Limit (429). Tentando novamente em {delay}s... (Tentativa {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
                continue
            else:
                logging.error(f"Erro na API. Código: {response_code}, Mensagem: {response.text}")
                return {} # Retorna dicionário vazio em caso de erro HTTP

        except requests.exceptions.RequestException as e:
            logging.error(f"Exceção durante a chamada da API: {e}")
            return {} # Retorna dicionário vazio em caso de erro de conexão
        except Exception as e:
            logging.error(f"Erro inesperado: {e}")
            return {} # Retorna dicionário vazio em caso de erro genérico

    logging.error("Falha após todas as tentativas na Fase 2.")
    return {}

# ----------------------------------------------------------------------
# FUNÇÃO DE ORQUESTRAÇÃO COMPLETA (HÍBRIDA)
# ----------------------------------------------------------------------

def extract_book_data_full(ean: str) -> Dict[str, Any]:
    """
    Orquestra a extração de dados estáticos (Fase 1) e dinâmicos (Fase 2) e combina os resultados.
    """
    global API_KEY

    # 1. Fase 1: Extração de Metadados (Gratuita)
    metadata = search_google_books_api(ean)

    # 2. Fase 2: Extração de Preços (Gemini - Custo)
    prices = call_gemini_api_otimizada(ean, API_KEY)
    
    price_data = prices
    
    # Obtém preços com fallback.
    preco_sem_desc = price_data.get("precoSemDesconto", "N/A (Fase 2 Falhou)")
    preco_com_desc = price_data.get("precoComDesconto", "N/A (Fase 2 Falhou)")

    # Aplica a formatação de moeda se os dados foram encontrados
    formatted_preco_sem_desc = format_currency(preco_sem_desc)
    formatted_preco_com_desc = format_currency(preco_com_desc)

    # Combina e formata os resultados
    result = {
        "EAN/ISBN": ean,
        "titulo": metadata.get("titulo", "N/A"),
        "autor": metadata.get("autor", "N/A"),
        "editora": metadata.get("editora", "N/A"),
        "precoSemDesconto": formatted_preco_sem_desc,
        "precoComDesconto": formatted_preco_com_desc
    }
    
    return result

# ----------------------------------------------------------------------
# FUNÇÕES DE ENTRADA DE DADOS
# ----------------------------------------------------------------------

def load_eans_from_csv(filepath: str) -> List[str]:
    """
    Carrega a lista de EANs/ISBNs de um arquivo CSV, ignorando cabeçalhos e valores vazios.
    """
    eans = []
    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            # Tenta pular o cabeçalho se o primeiro item parecer um texto e não um número
            try:
                first_row = next(reader)
                if not first_row or not first_row[0].isdigit():
                    # Ignora o cabeçalho
                    pass
                else:
                    # Se parecer números, volta a linha para ser processada
                    eans.extend([e.strip() for e in first_row if e.strip()])
            except StopIteration:
                # Arquivo vazio
                return []

            # Processa as linhas restantes
            for row in reader:
                # Assume que o EAN/ISBN está na primeira coluna
                if row and row[0].strip():
                    eans.append(row[0].strip())
        
        logging.info(f"Encontrados {len(eans)} EANs/ISBNs no arquivo {filepath}.")
        return eans

    except FileNotFoundError:
        logging.error(f"Erro: Arquivo de entrada '{filepath}' não encontrado.")
        return []
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo CSV: {e}")
        return []

# ----------------------------------------------------------------------
# FUNÇÃO DE PROCESSAMENTO EM LOTE (BATCH) - ATUALIZADA
# ----------------------------------------------------------------------

def process_ean_list_to_spreadsheet(ean_list: List[str]) -> List[List[str]]:
    """
    Processa uma lista de EANs e retorna os 6 campos em formato de planilha (lista de listas).
    """
    results_table: List[List[str]] = [
        ["EAN/ISBN", "Título do Livro", "Autor(es)", "Editora", "Preço S/ Desc.", "Preço C/ Desc."] # NOVO CABEÇALHO
    ]

    # Verifica se a chave está configurada para exibir o aviso de delay
    has_api_key = bool(API_KEY)
    if has_api_key:
        # Aumentamos o delay para 5 segundos para maior resiliência contra Rate Limit (429)
        print("AVISO: Tempo de espera de 5 segundos entre cada chamada devido à Fase 2 (Gemini + Search Grounding).")

    for ean in ean_list:
        data = extract_book_data_full(ean)
        
        row = [
            data["EAN/ISBN"],
            data["titulo"],
            data["autor"],
            data["editora"],
            data["precoSemDesconto"],
            data["precoComDesconto"]
        ]
        results_table.append(row)
        
        # Atraso só é necessário se a Fase 2 (API do Gemini) for realmente chamada
        if has_api_key:
            time.sleep(5) 

    return results_table


# ----------------------------------------------------------------------
# EXEMPLO DE USO
# ----------------------------------------------------------------------

if __name__ == "__main__":
    
    # ------------------------------------------------------------------
    # VERIFICAÇÃO CRÍTICA: ENCERRAMENTO SE API_KEY ESTIVER VAZIA
    # ------------------------------------------------------------------
    if not API_KEY:
        print("\n\n####################################################################")
        print("AVISO CRÍTICO: CHAVE API DO GEMINI NÃO CONFIGURADA.")
        print("A Fase 2 (Extração de Preços) não pode ser executada sem a chave.")
        print("Verifique se o arquivo .env existe e se a variável GEMINI_API_KEY está preenchida.")
        print("####################################################################\n")
        # Encerra o script com código de erro 1 (falha)
        sys.exit(1)
    
    # 1. Carrega a lista de EANs do arquivo CSV
    INPUT_FILEPATH = "input_eans.csv"
    TEST_EANS = load_eans_from_csv(INPUT_FILEPATH)

    if not TEST_EANS:
        logging.error("Nenhum EAN/ISBN válido para processar. Encerrando.")
        sys.exit(1)

    logging.info(f"--- INICIANDO EXTRAÇÃO HÍBRIDA (FASE 1 + FASE 2) PARA {len(TEST_EANS)} CÓDIGOS ---")
    
    # 2. Processa os dados
    spreadsheet_data = process_ean_list_to_spreadsheet(TEST_EANS)

    # 3. Formata e imprime o resultado
    print("\n" + "="*110)
    print("RESULTADO FINAL COMBINADO (ARQUITETURA HÍBRIDA):")
    
    # Usa a biblioteca tabulate para imprimir a tabela de forma profissional
    headers = spreadsheet_data[0]
    data_rows = spreadsheet_data[1:]
    print(tabulate(data_rows, headers=headers, tablefmt="fancy_grid", numalign="right"))
    
    print("="*110)
    
