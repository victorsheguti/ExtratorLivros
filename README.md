# 📚 Extrator de Dados Híbrido de Livros (MVP 1.0 / a02)

Este projeto implementa uma **Arquitetura Híbrida** para extração de dados de livros, combinando fontes gratuitas e APIs de Inteligência Artificial (Gemini) para otimizar custos e garantir a precisão dos dados.

---

## ⚙️ 1. Arquitetura e Racional Híbrido (SoC)

A arquitetura adota a Separação de Responsabilidades (SoC) para minimizar o uso do LLM (alto custo) e maximizar a precisão dos dados canônicos.

| Fase | Objetivo | Fonte Principal | Racional |
| :--- | :--- | :--- | :--- |
| **Fase 1: Estática (Metadados)** | Extrair **Título, Autor, Editora** (Dados Canônicos). | Google Books API (GBA) | Custo Zero e alta precisão para dados estáveis. |
| **Fase 2: Dinâmica (Preços)** | Extrair **APENAS** `Preço Sem Desconto` e `Preço Com Desconto` (Dados Voláteis). | Gemini 2.5 Flash + Google Search Grounding | Uso estrito do LLM para a tarefa mais complexa (busca em tempo real). |

---

## 🔑 2. Configuração e Setup (CRÍTICO)

O arquivo principal é **`extrator_livros.py`**. A automação depende de três arquivos de suporte para rodar.

### 2.1. Arquivos Necessários

| Arquivo | Descrição | Exemplo/Detalhe |
| :--- | :--- | :--- |
| **`requirements.txt`** | Lista as dependências Python (`requests`, `python-dotenv`, `tabulate`). | Deve ser instalado via `pip install -r requirements.txt`. |
| **`.env`** | Armazena a chave de API de forma **segura** (Variável de Ambiente). | **Formato obrigatório:** `GEMINI_API_KEY="SUA_CHAVE_AQUI"`. |
| **`input_eans.csv`** | Lista os códigos de livros para processamento. | Deve conter a coluna `ISBN` (ou `EAN`) e um código por linha. |

### 2.2. Pré-requisitos e Instalação

1.  Instale Python 3 (se ainda não o fez).
2.  Instale as dependências listadas no `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
3.  Obtenha sua chave de API do Gemini em [Google AI Studio](https://ai.google.com/gemini-api/docs/api-key) (ou similar).
4.  Crie e configure a Chave de API no arquivo **`.env`**.

---

## ▶️ 3. Como Executar

Após a configuração, a execução do script é feita no terminal:

1.  Preencha os códigos EAN/ISBN no arquivo **`input_eans.csv`**.
2.  Execute o script principal:
    ```bash
    python extrator_livros.py
    ```
3.  O resultado será formatado e exibido diretamente no terminal.

---

## 📚 4. Documentação de Desenvolvimento

Para entender o racional e as regras de contribuição, consulte os arquivos de documentação detalhados:

* **[ARCHITECTURE.md](ARCHITECTURE.md)**: Detalha o fluxo das Fases 1 e 2, e as regras críticas de uso da Gemini API (modelo, prompts e *grounding*).
* **[DECISION_RECORD.md](DECISION_RECORD.md)**: Histórico das decisões tomadas (ADR), como a migração para a Arquitetura Híbrida (ADR 001) e o Contrato de Falhas (ADR 003).
* **[CONTRIBUTING.md](CONTRIBUTING.md)**: Guia rápido para novos colaboradores com foco nas regras de otimização de custos e estabilidade do pipeline.

---

## 🚀 5. Próximos Passos Críticos

O projeto está pronto para sua próxima grande fase: persistência de dados. O objetivo é implementar uma função de exportação para o Google Sheets usando a biblioteca `gspread`, configurando uma **Conta de Serviço (Service Account)** para autenticação segura.