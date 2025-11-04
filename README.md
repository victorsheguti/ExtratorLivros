📚 Extrator de Dados Híbrido de Livros (MVP 1.0)
Este projeto implementa uma Arquitetura Híbrida para extração de dados de livros, combinando fontes gratuitas e APIs de Inteligência Artificial para otimizar custos e garantir a precisão dos dados.

⚙️ Arquitetura Híbrida
Fase 1 (Metadados): Utiliza a Google Books API (Custo Zero) para extrair dados estáveis e canônicos (Título, Autor, Editora).

Fase 2 (Preços Dinâmicos): Utiliza o Gemini 2.5 Flash com Google Search Grounding para extrair APENAS preços em tempo real da Amazon Brasil e outros grandes varejistas.

📋 Campos Extraídos
Categoria

Campo

Fonte

Metadados

Título do Livro

Google Books API

Metadados

Autor(es)

Google Books API

Metadados

Editora

Google Books API

Preços

Preço Sem Desconto

Gemini + Search Grounding

Preços

Preço Com Desconto

Gemini + Search Grounding

🔑 Configuração (CRÍTICA)
Para que a Fase 2 (Extração de Preços) funcione, você deve configurar sua chave de API do Gemini.

Obtenha sua chave de API em Google AI Studio.

Abra o arquivo book_data_extractor.py.

Insira sua chave na variável global API_KEY:

API_KEY = "SUA_CHAVE_AQUI_GEMINI"

▶️ Como Executar
Instale Python 3 (se ainda não o fez).

Instale a dependência requests no seu terminal:

pip install requests

Execute o script:

python book_data_extractor.py

=======================

🚀 Atualização do Projeto: Refinamento do MVP (04/11/2025)

Esta seção detalha as melhorias implementadas para aumentar a segurança, usabilidade e profissionalismo do script.

1. Renomeação do Arquivo Principal

O arquivo principal foi renomeado para maior clareza:

Antigo: book_data_extractor.py

Novo: extrator_livros.py

2. Fonte de Dados Externa (CSV)

A lista de códigos EAN/ISBN foi movida de uma lista estática no código para um arquivo CSV externo, tornando a entrada de dados mais flexível.

Entrada de Dados: O script agora lê os códigos do arquivo input_eans.csv.

3. Configuração Segura (Variáveis de Ambiente)

A chave da API do Gemini agora é carregada de um arquivo de variáveis de ambiente, o que é uma prática essencial de segurança.

Chave da API: Deve ser configurada no arquivo .env sob a variável GEMINI_API_KEY.

Novas Dependências: As bibliotecas python-dotenv e tabulate foram adicionadas.

4. Saída Profissional

A saída no terminal foi melhorada usando a biblioteca tabulate para apresentar os resultados em uma tabela formatada, facilitando a leitura e visualização.

🛠️ Novo Processo de Execução

Instale Python 3 (se ainda não o fez).

Instale as dependências (requests, python-dotenv, tabulate):

pip install -r requirements.txt



Configure a Chave de API no arquivo .env (Ex: GEMINI_API_KEY="SUA_CHAVE_AQUI").

Preencha os códigos EAN/ISBN no arquivo input_eans.csv.

Execute o script principal:

python extrator_livros.py

# Atualização 20251104

📚 Extrator de Dados Híbrido de Livros (Versão a02)
Este projeto implementa uma Arquitetura Híbrida para extração de dados de livros, combinando fontes gratuitas e APIs de Inteligência Artificial para otimizar custos e garantir a precisão dos dados.

⚙️ Arquitetura Híbrida e Fluxo de Trabalho
O projeto segue o princípio de Separação de Responsabilidades (SoC) para minimizar o uso do recurso de inteligência artificial (que tem custo):

* **Fase 1 (Metadados - Custo Zero):** Utiliza a **Google Books API (GBA)** para extrair dados estáveis e canônicos (**Título, Subtítulo, Autor(es), Editora**).
* **Fase 2 (Preços Dinâmicos - Alto Custo):** Utiliza o **Gemini 2.5 Flash** com **Google Search Grounding** para extrair APENAS preços em tempo real (`precoSemDesconto` e `precoComDesconto`) de fontes de e-commerce.

📋 Campos Extraídos

| Categoria | Campo | Fonte |
| :--- | :--- | :--- |
| Metadados | Título Completo (Título + Subtítulo) | Google Books API |
| Metadados | Autor(es) | Google Books API |
| Metadados | Editora | Google Books API |
| Preços | Preço Sem Desconto | Gemini + Search Grounding |
| Preços | Preço Com Desconto | Gemini + Search Grounding |

🔑 Configuração (CRÍTICA)
O arquivo principal foi renomeado para **extrator\_livros.py** e a automação depende de três arquivos de suporte para rodar:

1.  **requirements.txt**: Lista as dependências (`requests`, `python-dotenv`, `tabulate`).
2.  **.env**: Armazena a chave de API de forma segura. O formato obrigatório é: `GEMINI_API_KEY=SUA_CHAVE_AQUI`.
3.  **input\_eans.csv**: Lista os códigos de livros para processamento (um EAN/ISBN por linha, sem cabeçalho).

🛠️ Novo Processo de Execução

1.  Instale Python 3 (se ainda não o fez).
2.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure a Chave de API no arquivo **.env** (Ex: `GEMINI_API_KEY="SUA_CHAVE_AQUI"`).
4.  Preencha os códigos EAN/ISBN no arquivo **input\_eans.csv**.
5.  Execute o script principal:
    ```bash
    python extrator_livros.py
    ```

### 🚀 Próximo Passo Crítico: Exportação para Google Sheets
A próxima fase do projeto (persisência de dados) será implementar a exportação dos resultados para uma Planilha Google. Isso exigirá a configuração de uma **Conta de Serviço (Service Account)** e a biblioteca **`gspread`** no `extrator_livros.py` para garantir a autenticação e escrita dos dados.