# 📐 Arquitetura do Extrator Híbrido de Dados (MVP 1.0 / a02)

Este documento detalha o racional por trás da **Arquitetura Híbrida** para extração de dados de livros, utilizando o princípio de Separação de Responsabilidades (SoC), e registra os prompts oficiais da Fase 2 para garantir a rastreabilidade e a manutenção do código.

## 1. Contexto Histórico e Status Atual

### 1.1. Motivação do Projeto
O projeto foi migrado de uma arquitetura de monolito de IA (que usava a Gemini API para todos os 5 campos) para a Arquitetura Híbrida. A mudança teve como objetivo principal **reduzir custos** e **aumentar a precisão** dos dados canônicos (Título, Autor).

### 1.2. Status de Estabilidade
O código Python (`extrator_livros.py`) representa a versão mais estável, incorporando `retry`, `exponential backoff` e tratamento robusto de erros. A única dependência inerentemente instável é a extração de preços da Amazon (Fase 2), devido à natureza dinâmica do e-commerce.

### 1.3. Atualizações Críticas (04/11/2025)
* **Arquivo Principal:** Renomeado para `extrator_livros.py`.
* **Segurança:** A configuração da `API_KEY` foi movida para **variáveis de ambiente (`.env`)**.
* **Operação:** O script agora aceita códigos EAN/ISBN de um arquivo de entrada (`input_eans.csv`).
* **Saída:** A saída no terminal é formatada usando a biblioteca `tabulate`.

## 2. Racional da Arquitetura Híbrida (SoC)

O pipeline adota a Separação de Responsabilidades (SoC) para otimizar custos e maximizar a precisão, dividindo a extração em duas fases.

| Fase | Objetivo | Fonte/Ferramenta | Racional / Justificativa |
| :--- | :--- | :--- | :--- |
| **Fase 1: Estática (Metadados)** | Extrair **Título, Subtítulo, Autor(es), Editora** (Dados Canônicos). | Google Books API (GBA) | Custo Zero (Gratuita) e alta precisão para dados que raramente mudam. |
| **Fase 2: Dinâmica (Preços)** | Extrair **APENAS** `precoSemDesconto` e `precoComDesconto` (Dados Voláteis). | Gemini 2.5 Flash + Google Search Grounding | Utiliza o LLM (Alto Custo) estritamente para a tarefa mais complexa: extração de dados voláteis de e-commerce em tempo real. |

---

## 3. 🤖 Prompts Oficiais de Geração (Fase 2 - Gemini)

Os prompts guiam o modelo a atuar estritamente como um extrator de preços, garantindo que o alto custo da API seja utilizado apenas para a tarefa de alto valor.

**Modelo Utilizado:** `gemini-2.5-flash-preview-05-20` (Otimizado para extração e baixa latência).

### 3.1. System Prompt (Instrução para a IA)

Define a persona, o foco exclusivo e as regras de fallback.

> Você é um extrator de APENAS PREÇOS de e-commerce, especialista em localizar e extrair informações dinâmicas com base no EAN/ISBN. Use o Google Search para buscar PRIMEIRO na Amazon Brasil, e se o preço não for encontrado, procure em outros grandes varejistas brasileiros (como Submarino, Livraria Cultura, etc.). SUA TAREFA É ESTRITAMENTE EXTRAIR PREÇOS. NÃO RETORNE TÍTULO, AUTOR OU EDITORAS. CAMPOS OBRIGATÓRIOS (APENAS): 'precoSemDesconto' e 'precoComDesconto'. Se o 'precoComDesconto' não for encontrado, use o valor de 'precoSemDesconto'. Se NENHUM preço for encontrado na fonte, retorne O OBJETO JSON VAZIO: {}. Retorne APENAS o objeto JSON, sem nenhum texto introdutório ou código markdown (e.g., sem ```json).

### 3.2. User Query (Consulta de Execução)

A instrução direta que acompanha o EAN no payload.

> BUSCA DE PREÇOS: EAN/ISBN [EAN\_AQUI]. Extrair estritamente apenas o preço sem e com desconto.

---

## 4. 🚀 Regras Críticas para Continuidade (Contrato de Manutenção)

Este prompt consolida todas as regras críticas para a nova IA ou desenvolvedor que for dar continuidade ao projeto.

### 4.1. Arquitetura e Fluxo

| Regra | Detalhe |
| :--- | :--- |
| **Separação de Responsabilidades** | **NUNCA** use o Gemini para extrair Título, Autor ou Editora. Essa tarefa pertence **EXCLUSIVAMENTE à Fase 1** (Google Books API). |
| **Pré-condição da Fase 2** | A Fase 2 (Preços) deve ser executada apenas se a Fase 1 retornar um EAN válido. |

### 4.2. Configuração e Estrutura de Saída da Gemini API

| Configuração | Regra Crítica |
| :--- | :--- |
| **Modelo** | Deve ser o `gemini-2.5-flash-preview-05-20`. |
| **Grounding (Busca)** | O parâmetro `tools` deve **OBRIGATORIAMENTE** conter `Google Search: {}`. |
| **Estrutura de Saída** | O Gemini **NÃO PODE** usar `responseMimeType: application/json` (JSON Estruturado) pois é incompatível com o Grounding. A saída será uma **STRING JSON**. |
| **Limpeza de JSON** | O código DEVE incluir lógica para remover qualquer *markdown* (e.g., ```json) da resposta da IA antes do `JSON.parse()/json.loads()`. |

### 4.3. Tratamento de Falhas (Contrato de Dados)

O pipeline principal deve tratar as falhas da Fase 2 conforme o contrato abaixo, para facilitar a análise de logs e a exportação.

| Cenário de Falha | Valor de Retorno (Placeholder) |
| :--- | :--- |
| **Geral (JSON Vazio/Falha)** | A função deve retornar um valor que se resolva para **`N/A (Fase 2 Falhou)`** no pipeline principal. |
| **Log: `precoSemDesconto`** | `error_price`. |
| **Log: `precoComDesconto`** | `error_wdiscount`. |

### 4.4. Estabilidade e Resiliência

| Mecanismo | Configuração Mínima |
| :--- | :--- |
| **Retry** | O código deve manter o mecanismo de **`retry` (3 vezes)** com **`exponential backoff`** para tratar erros temporários e *rate limits* (erro 429). |
| **Timeout** | O *timeout* da requisição DEVE ser de, no mínimo, **35 segundos** para acomodar o tempo de execução do *Search Grounding*. |