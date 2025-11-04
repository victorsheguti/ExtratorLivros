📐 Arquitetura do Extrator Híbrido de Dados (MVP 1.0)
Este documento detalha o racional por trás da Arquitetura Híbrida e registra os prompts utilizados na Fase 2 para garantir a rastreabilidade e a manutenção do código.

0. Contexto Histórico do Projeto e Objetivos
Este projeto foi migrado de uma arquitetura de monolito de IA (onde a Gemini API era usada para extrair todos os 5 campos) para uma Arquitetura Híbrida.

Motivação: Reduzir custos e aumentar a precisão dos dados canônicos (Título, Autor).

Status Atual: O código Python (book_data_extractor.py) representa a versão mais estável, incorporando retry, exponential backoff e tratamento robusto de TypeError e falhas de conexão. A única dependência que ainda é instável é a extração de preços da Amazon (Fase 2), inerente à natureza dinâmica do e-commerce.

1. Racional da Arquitetura Híbrida
O projeto adota uma arquitetura de Separação de Responsabilidades (SoC) para otimizar custos e maximizar a precisão.

Fase

Objetivo

Fonte/Ferramenta

Racional / Justificativa

Fase 1: Estática

Extrair Título, Autor, Editora (Dados Canônicos).

Google Books API (GBA)

Custo Zero (Gratuito), alta disponibilidade e precisão para dados que raramente mudam.

Fase 2: Dinâmica

Extrair APENAS precoSemDesconto e precoComDesconto (Dados Voláteis).

Gemini 2.5 Flash + Google Search Grounding

Utiliza o LLM (alto custo) estritamente para a tarefa mais difícil: extração de dados dinâmicos e voláteis de e-commerce em tempo real.

2. Prompts de Geração (Fase 2 - Gemini)
Os prompts são escritos para guiar o Gemini a atuar como um extrator de preços focado, garantindo que o custo da API seja usado apenas para a tarefa de alto valor.

Modelo Utilizado: gemini-2.5-flash-preview-05-20 (Otimizado para extração e baixa latência).

System Prompt (Instrução para a IA)
Define a persona, o foco exclusivo e as regras de fallback.

Você é um extrator de APENAS PREÇOS de e-commerce, especialista em localizar e extrair informações dinâmicas com base no EAN/ISBN. Use o Google Search para buscar PRIMEIRO na Amazon Brasil, e se o preço não for encontrado, procure em outros grandes varejistas brasileiros (como Submarino, Livraria Cultura, etc.). SUA TAREFA É ESTRITAMENTE EXTRAIR PREÇOS. NÃO RETORNE TÍTULO, AUTOR OU EDITORAS. CAMPOS OBRIGATÓRIOS (APENAS): 'precoSemDesconto' e 'precoComDesconto'. Se o 'precoComDesconto' não for encontrado, use o valor de 'precoSemDesconto'. Se NENHUM preço for encontrado na fonte, retorne O OBJETO JSON VAZIO: {}. Retorne APENAS o objeto JSON, sem nenhum texto introdutório ou código markdown (e.g., sem ```json).

User Query (Consulta de Execução)
A instrução direta que acompanha o EAN.

BUSCA DE PREÇOS: EAN/ISBN [EAN_AQUI]. Extrair estritamente apenas o preço sem e com desconto.

🚀 Prompt de Continuidade para Novo Desenvolvedor
Este prompt consolida todas as regras críticas para a nova IA ou desenvolvedor que for dar continuidade ao projeto.

**CONTEÚDO CRÍTICO PARA CONTINUIDADE DO PROJETO DE EXTRAÇÃO HÍBRIDA (MVP 1.0)**

**Objetivo:** Manter e evoluir o pipeline de extração de dados de livros (5 campos) utilizando a Arquitetura Híbrida.

**1. Arquitetura e Fluxo:**
* O pipeline é dividido em **Fase 1 (Metadados)** via Google Books API (Gratuita) e **Fase 2 (Preços)** via Gemini + Google Search Grounding (Alto Custo).
* **NUNCA** use o Gemini para extrair Título, Autor ou Editora. Essa tarefa pertence EXCLUSIVAMENTE à Fase 1.
* A Fase 2 (Preços) deve ser executada apenas se a Fase 1 retornar um EAN válido.

**2. Regras Críticas da Fase 2 (Gemini API):**
* **Modelo:** Deve ser o `gemini-2.5-flash-preview-05-20` para otimização de custos/velocidade.
* **Ferramenta:** O parâmetro `tools` deve OBRIGATORIAMENTE conter `Google Search: {}` para garantir a busca em tempo real (Grounding).
* **Estrutura de Saída:** O Gemini **NÃO PODE** usar `responseMimeType: application/json` (JSON Estruturado) pois é incompatível com o Grounding. A saída será uma **STRING JSON**.
* **Limpeza de JSON:** O código (Python/GAS) DEVE incluir lógica para remover qualquer *markdown* (e.g., ```json) da resposta da IA antes do `JSON.parse()/json.loads()`.
* **Tratamento de Falhas (Contrato):** Se o Gemini falhar ou retornar um objeto JSON vazio, a função deve retornar um valor que se resolva para `N/A (Fase 2 Falhou)` no pipeline principal.

**3. Prompts e Payload:**
* **System Prompt:** Aplicar o prompt fornecido neste documento (foco exclusivo em preço e fallback para outros varejistas).
* **Payload:** O campo `contents` DEVE incluir o `userQuery` e os `tools` (search grounding).

**4. Estabilidade e Resiliência:**
* O código deve manter o mecanismo de `retry` (3 vezes) com `exponential backoff` para tratar erros temporários e *rate limits* (erro 429).
* O *timeout* da requisição DEVE ser de, no mínimo, 35 segundos para acomodar o tempo de execução do Search Grounding.

📐 Arquitetura do Extrator Híbrido de Dados (a02)
Este documento detalha o racional por trás da Arquitetura Híbrida e registra os prompts utilizados na Fase 2 para garantir a rastreabilidade e a manutenção do código.

Contexto Histórico do Projeto e Objetivos
Este projeto foi migrado de uma arquitetura de monolito de IA (onde a Gemini API era usada para extrair todos os 5 campos) para uma Arquitetura Híbrida.
Motivação: Reduzir custos e aumentar a precisão dos dados canônicos (Título, Autor).
Status Atual: O código Python (**extrator_livros.py**) representa a versão mais estável, incorporando retry, exponential backoff e tratamento robusto de TypeError e falhas de conexão. A única dependência que ainda é instável é a extração de preços da Amazon (Fase 2), inerente à natureza dinâmica do e-commerce.

ATUALIZAÇÃO CRÍTICA (04/11/2025):
O arquivo principal foi renomeado para **extrator_livros.py**. 
A configuração da API_KEY foi movida para **variáveis de ambiente (.env)** por questões de segurança.
O script agora aceita códigos EAN/ISBN de um arquivo de entrada **input_eans.csv**, e a saída no terminal é formatada usando a biblioteca **tabulate**.

Racional da Arquitetura Híbrida
O projeto adota uma arquitetura de Separação de Responsabilidades (SoC) para otimizar custos e maximizar a precisão.

| Fase | Objetivo | Fonte/Ferramenta | Racional / Justificativa |
| :--- | :--- | :--- | :--- |
| **Fase 1: Estática** | Extrair **Título, Subtítulo, Autor(es), Editora** (Dados Canônicos). *(Corrigido para concatenar Título e Subtítulo)* | Google Books API (GBA) | Custo Zero (Gratuito), alta disponibilidade e precisão para dados que raramente mudam. |
| **Fase 2: Dinâmica** | Extrair APENAS precoSemDesconto e precoComDesconto (Dados Voláteis). | Gemini 2.5 Flash + Google Search Grounding | Utiliza o LLM (alto custo) estritamente para a tarefa mais difícil: extração de dados dinâmicos e voláteis de e-commerce em tempo real. |

Prompts de Geração (Fase 2 - Gemini)
Os prompts são escritos para guiar o Gemini a atuar como um extrator de preços focado, garantindo que o custo da API seja usado apenas para a tarefa de alto valor.
Modelo Utilizado: gemini-2.5-flash-preview-05-20 (Otimizado para extração e baixa latência).

System Prompt (Instrução para a IA)
Define a persona, o foco exclusivo e as regras de fallback.
Você é um extrator de APENAS PREÇOS de e-commerce, especialista em localizar e extrair informações dinâmicas com base no EAN/ISBN. Use o Google Search para buscar PRIMEIRO na Amazon Brasil, e se o preço não for encontrado, procure em outros grandes varejistas brasileiros (como Submarino, Livraria Cultura, etc.). SUA TAREFA É ESTRITAMENTE EXTRAIR PREÇOS. NÃO RETORNE TÍTULO, AUTOR OU EDITORAS. CAMPOS OBRIGATÓRIOS (APENAS): 'precoSemDesconto' e 'precoComDesconto'. Se o 'precoComDesconto' não for encontrado, use o valor de 'precoSemDesconto'. Se NENHUM preço for encontrado na fonte, retorne O OBJETO JSON VAZIO: {}. Retorne APENAS o objeto JSON, sem nenhum texto introdutório ou código markdown (e.g., sem ```json).

User Query (Consulta de Execução)
A instrução direta que acompanha o EAN.
BUSCA DE PREÇOS: EAN/ISBN [EAN_AQUI]. Extrair estritamente apenas o preço sem e com desconto.

🚀 Prompt de Continuidade para Novo Desenvolvedor
Este prompt consolida todas as regras críticas para a nova IA ou desenvolvedor que for dar continuidade ao projeto.

CONTEÚDO CRÍTICO PARA CONTINUIDADE DO PROJETO DE EXTRAÇÃO HÍBRIDA (a02)
Objetivo: Manter e evoluir o pipeline de extração de dados de livros (5 campos) utilizando a Arquitetura Híbrida.

1. Arquitetura e Fluxo:
O pipeline é dividido em Fase 1 (Metadados) via Google Books API (Gratuita) e Fase 2 (Preços) via Gemini + Google Search Grounding (Alto Custo).
NUNCA use o Gemini para extrair Título, Autor ou Editora. Essa tarefa pertence EXCLUSIVAMENTE à Fase 1.
A Fase 2 (Preços) deve ser executada apenas se a Fase 1 retornar um EAN válido.

2. Regras Críticas da Fase 2 (Gemini API):
Modelo: Deve ser o gemini-2.5-flash-preview-05-20 para otimização de custos/velocidade.
Ferramenta: O parâmetro tools deve OBRIGATORIAMENTE conter Google Search: {} para garantir a busca em tempo real (Grounding).
Estrutura de Saída: O Gemini NÃO PODE usar responseMimeType: application/json (JSON Estruturado) pois é incompatível com o Grounding. A saída será uma STRING JSON.
Limpeza de JSON: O código (Python/GAS) DEVE incluir lógica para remover qualquer markdown (e.g., ```json) da resposta da IA antes do JSON.parse()/json.loads().
Tratamento de Falhas (Contrato): Se o Gemini falhar ou retornar um objeto JSON vazio, a função deve retornar um valor que se resolva para N/A (Fase 2 Falhou) no pipeline principal.

3. Prompts e Payload:
System Prompt: Aplicar o prompt fornecido neste documento (foco exclusivo em preço e fallback para outros varejistas).
Payload: O campo contents DEVE incluir o userQuery e os tools (search grounding).

4. Estabilidade e Resiliência:
O código deve manter o mecanismo de retry (3 vezes) com exponential backoff para tratar erros temporários e rate limits (erro 429).
O timeout da requisição DEVE ser de, no mínimo, 35 segundos para acomodar o tempo de execução do Search Grounding.