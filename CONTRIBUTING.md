# 🤝 Guia de Contribuição: Extrator Híbrido de Dados (MVP 1.0)

Este documento estabelece as diretrizes e regras críticas para contribuir com o pipeline de extração de dados de livros, garantindo que a arquitetura híbrida seja mantida e que os custos de IA sejam otimizados.

## 1. 🏛️ Princípios Arquiteturais Chave

O pipeline adota o princípio de Separação de Responsabilidades (SoC) para otimizar custos e precisão.

| Fase | Responsabilidade **Exclusiva** | Ferramenta | Regra Crítica |
| :--- | :--- | :--- | :--- |
| **Fase 1 (Metadados)** | Extrair **Título, Autor, Editora** (Dados Canônicos). | Google Books API (GBA). | **NUNCA** usar a Gemini API para esta tarefa. |
| **Fase 2 (Preços)** | Extrair **APENAS** `precoSemDesconto` e `precoComDesconto` (Dados Voláteis). | Gemini 2.5 Flash + Google Search Grounding. | Executar somente se a Fase 1 retornar um EAN válido. |

## 2. 🤖 Regras Estritas da Gemini API (Fase 2)

A performance, o custo e a compatibilidade do sistema dependem da estrita aderência às seguintes configurações:

| Configuração | Requisito | Racional (ADR) |
| :--- | :--- | :--- |
| **Modelo** | Deve ser o **`gemini-2.5-flash-preview-05-20`**. | Otimização de custos e velocidade (ADR 002). |
| **Ferramenta** | O parâmetro `tools` deve **OBRIGATORIAMENTE** conter **`Google Search: {}`**. | Necessário para garantir a busca em tempo real (Grounding). |
| **Estrutura de Saída** | A saída é uma **STRING JSON**. **NÃO PODE** usar `responseMimeType: application/json`. | Incompatibilidade do JSON Estruturado com o Grounding (ADR 002). |
| **Limpeza de Saída** | O código **DEVE** incluir lógica para remover qualquer *markdown* (e.g., ```json) da resposta da IA antes do *parsing*. | Solução para a restrição de saída (ADR 002). |

## 3. 🛡️ Estabilidade e Resiliência (Robustez)

Todo o código de requisição (especialmente para a Fase 2, que é instável) deve seguir estas regras:

* **Retry:** Manter o mecanismo de **`retry` (3 vezes)** com **`exponential backoff`** para tratar erros temporários e *rate limits* (erro 429).
* **Timeout:** O *timeout* da requisição DEVE ser de, no mínimo, **35 segundos** para acomodar o tempo de execução do Search Grounding.
* **Segurança:** A `API_KEY` deve ser carregada **APENAS** de variáveis de ambiente (`.env file`).

## 4. 📝 Contrato de Falhas (Error Contract - ADR 003)

Para garantir a integridade dos dados na exportação e facilitar a análise de logs, o tratamento de falhas na Fase 2 é padronizado:

* **Falha Geral:** Se a Gemini falhar ou retornar um objeto JSON vazio, a função deve retornar um valor que se resolva para **`N/A (Fase 2 Falhou)`** no pipeline principal.
* **Log de Falha (Preços):** Mapear falhas de preço para os *placeholders* específicos no log:
    * `precoSemDesconto`: **`error_price`**.
    * `precoComDesconto`: **`error_wdiscount`**.

## 5. 🖥️ Setup do Ambiente

O arquivo principal é `extrator_livros.py`. Para rodar o projeto localmente, assegure-se de:

1.  Criar e configurar o arquivo `.env` com a API Key.
2.  Garantir que os EANs/ISBNs de entrada estejam no formato esperado pelo arquivo `input_eans.csv`.