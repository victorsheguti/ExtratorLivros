# 📋 Registro de Decisões de Arquitetura (ADR - MVP 1.0)

Este documento registra as principais decisões de arquitetura (ADR - Architecture Decision Record) tomadas durante a migração e o desenvolvimento do Extrator Híbrido de Dados (MVP 1.0).

## 1. ADR 001: Migração para Arquitetura Híbrida

| Detalhe | Valor |
| :--- | :--- |
| **Data de Aprovação** | 01/09/2025 |
| **Status** | Aprovado |

### Contexto
O modelo anterior (Monolito IA) gerava custos muito altos na Gemini API para extrair todos os 5 campos. Além disso, a precisão para dados canônicos (Título/Autor) era baixa.

### Decisão
Implementar a Arquitetura Híbrida, separando a extração de metadados canônicos (Fase 1) da extração de preços dinâmicos (Fase 2).

### Consequências
* **Positivas:**
    * Redução estimada de **70% nos custos** da API de IA (Gemini).
    * Precisão de dados canônicos garantida pela Google Books API (GBA).
* **Negativas:**
    * Maior complexidade de código devido à orquestração de dois fluxos distintos (Fase 1 GBA, Fase 2 Gemini).
    * Necessidade de mecanismos robustos de `retry` e `timeout` para a Fase 2 (LLM).

---

## 2. ADR 002: Escolha da Gemini API + Search Grounding para Preços (Fase 2)

| Detalhe | Valor |
| :--- | :--- |
| **Data de Aprovação** | 10/09/2025 |
| **Status** | Aprovado |

### Contexto
A extração de preços de e-commerce é uma tarefa de alta volatilidade, inviabilizando o web scraping tradicional e exigindo o raciocínio e busca em tempo real de um LLM.

### Decisão
Utilizar o modelo `gemini-2.5-flash-preview-05-20` com o recurso **`Google Search Grounding: {}`** para a Fase 2, focada em preços.

### Consequências
* **Positivas:**
    * Capacidade de buscar em tempo real e em múltiplas fontes (Amazon, Submarino, etc.).
    * Aumento de **20% na taxa de sucesso** da extração de preços em relação ao modelo anterior (sem grounding).
* **Negativas:**
    * Latência de requisição maior (necessidade de **timeout mínimo de 35 segundos**).
    * O *Search Grounding* é incompatível com a saída estruturada (`responseMimeType: application/json`), exigindo que o código faça a **limpeza de markdown** (`strip('```json')`) da saída que é uma **STRING JSON**.

---

## 3. ADR 003: Implementação do Contrato de Falhas (Error Contract)

| Detalhe | Valor |
| :--- | :--- |
| **Data de Aprovação** | 20/09/2025 |
| **Status** | Aprovado |

### Contexto
Garantir a integridade dos dados na exportação para o banco de dados final, mapeando todas as falhas da Fase 2 para *placeholders* específicos.

### Decisão
Se a Fase 2 falhar ou retornar um objeto JSON vazio, retornar os *placeholders* **`error_price`** (para `precoSemDesconto`) e **`error_wdiscount`** (para `precoComDesconto`) no pipeline principal.

### Consequências
* **Positivas:**
    * Facilidade na análise de logs e relatórios de falha.
    * Garante que a estrutura final de dados (SQL/JSON) tenha campos preenchidos, evitando *crashes* downstream.
* **Negativas:**
    * O código cliente precisa de lógica adicional para tratar e reverter os *placeholders* caso seja necessária a exibição de `N/A` para o usuário final.

---

## 4. ADR 004: Mover Configuração de Segurança (API Key)

| Detalhe | Valor |
| :--- | :--- |
| **Data de Aprovação** | 04/11/2025 |
| **Status** | Aprovado |

### Contexto
A chave da API do Gemini estava codificada no script principal, representando um risco de segurança e dificultando a rotação de chaves.

### Decisão
Mover a chave da API para **variáveis de ambiente (`.env file`)** e carregar usando a biblioteca `dotenv`.

### Consequências
* **Positivas:**
    * Aumento da segurança (não expõe a chave no código).
    * Melhor prática de desenvolvimento e conformidade com padrões de segurança.
* **Negativas:**
    * Requer que o ambiente de execução tenha o arquivo `.env` configurado e que o pacote `dotenv` esteja instalado.