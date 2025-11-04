

# **Otimização Híbrida de Extração de Dados de Livros: Estratégias de Desacoplamento de LLMs via Integração de APIs Públicas**

## **I. Análise Crítica da Arquitetura Atual Baseada em LLM Grounding**

O projeto de extração de dados da Amazon, originalmente implementado em Google Apps Script (GAS) utilizando a API Gemini, demonstra uma funcionalidade crucial ao empregar o recurso de busca em tempo real (Search Grounding) para localizar produtos na Amazon pelo EAN/ISBN e extrair campos de título, autor, preços e editora.1 Embora essa abordagem cumpra o requisito de evitar *scraping* direto, uma análise detalhada da arquitetura revela ineficiências operacionais e financeiras significativas que podem comprometer a escalabilidade do projeto.

### **1.1. Revisão da Solução Google Apps Script (GAS) e Gemini**

A solução emprega o modelo Gemini 2.5 Flash, configurado com uma instrução de sistema (systemPrompt) extremamente rigorosa para atuar como um extrator de dados.2 A consulta do usuário (userQuery) é formulada para incluir o EAN/ISBN e a menção explícita à Amazon Brasil, solicitando os cinco campos de dados. O uso da ferramenta google\_search no *payload* da API é essencial para obter as informações dinâmicas da web.2

O principal desafio técnico identificado na arquitetura original foi a incompatibilidade entre o uso da ferramenta de busca e a solicitação nativa de retorno JSON estruturado via configurações da API, que resultava em um erro de código 400\.1 Para contornar essa restrição, o projeto precisou impor o formato JSON através da instrução de prompt e adicionar uma lógica de limpeza de texto no lado do cliente (GAS). Essa lógica é responsável por remover marcadores de código Markdown, como \`\`\`\`json\`\`\`, antes que o texto da resposta possa ser analisado pelo JSON.parse().2

### **1.2. Pontos de Fricção: Conflito de Formato Estruturado vs. Search Grounding**

A dependência da limpeza de código no lado do cliente (jsonText.replace(/\`\`\`json\\s\*/, '').replace(/\\s\*\`\`\`/, '').trim()) introduz uma fragilidade arquitetural notável.2 O sucesso da extração e da análise JSON (parsing) está condicionado à exata aderência do LLM à instrução de prompt, garantindo que ele não inclua texto introdutório, explicativo ou que use um formato de marcação ligeiramente diferente. Se o modelo se desviar, mesmo minimamente, ou se a plataforma Gemini alterar a formatação padrão da cerca de código Markdown, o JSON.parse() no script GAS falhará sem aviso prévio. Essa vulnerabilidade representa um débito técnico de alto risco para a manutenibilidade do sistema.

### **1.3. A Carga Operacional e Financeira do Search Grounding para Metadados**

O uso do LLM Grounding para extrair metadados estáticos (Título, Autor e Editora) é uma alocação ineficiente de recursos de inteligência artificial. Estes campos são informações canônicas e curadas, disponíveis em catálogos bibliográficos de forma gratuita e padronizada.

O custo do Grounding com Google Search é significativo: após a utilização da cota gratuita de 1.500 requisições por dia (RPD), as chamadas subsequentes são tarifadas a $35 por 1.000 requisições.3 Utilizar este recurso pago e limitado para obter dados estáveis, que não requerem inferência complexa ou busca em tempo real, impede a escalabilidade financeira do projeto. Cenários de uso em planilhas empresariais que demandam milhares de buscas diárias rapidamente fariam do custo do Grounding o principal gargalo operacional e financeiro.

A conclusão é que a arquitetura atual viola o princípio fundamental da Separação de Responsabilidades (SoC), pois um único, caro e complexo mecanismo é encarregado de extrair tanto dados estáticos quanto dados dinâmicos. A otimização reside no desacoplamento dessas tarefas.

## **II. O Paradigma da Separação de Responsabilidades (SoC) na Extração de Dados**

A adoção de um modelo híbrido que integra APIs públicas de livros permite que o projeto minimize o custo do LLM Grounding, aumente a precisão dos metadados e melhore a robustez geral da extração.

### **2.1. Definição do Modelo Híbrido: Metadados Estáticos vs. Dados Dinâmicos**

O novo modelo opera em duas fases distintas, cada uma otimizada para o tipo de dado que busca:

1. **Metadados Estáticos (Título, Autor, Editora):** Serão obtidos exclusivamente através de APIs públicas de livros, como a Google Books API (GBA). Essas APIs fornecem alta confiabilidade, retorno em formato JSON estritamente padronizado e um custo operacional nulo (cota gratuita).6  
2. **Dados Dinâmicos (Preços):** O recurso de LLM Search Grounding será reservado unicamente para extrair os preços (precoSemDesconto, precoComDesconto) da página da Amazon. A complexidade do LLM é justificada aqui, pois se trata de informação proprietária, volátil e dependente da busca em tempo real.

### **2.2. O Papel Estratégico das APIs Públicas de Livros**

APIs como a Google Books API 7 são fontes de autoridade bibliográfica. Elas fornecem metadados canônicos e estruturados para um determinado EAN/ISBN, eliminando a ambiguidade e o risco de erros contextuais associados à inferência de LLMs a partir de texto não estruturado de páginas de produto. Enquanto um LLM pode ocasionalmente cometer erros ao interpretar co-autores ou formatações de títulos complexas, a API de livros garante que o Título, Autor e Editora sejam retirados de um catálogo curado. O uso da API para metadados aumenta significativamente a qualidade canônica dos dados estáticos, que são fundamentais para a identificação do produto.

### **2.3. Resiliência e Manutenibilidade Aumentadas**

Ao isolar as responsabilidades, o sistema se torna inerentemente mais resiliente. A GBA serve como uma camada de pré-validação do ISBN/EAN. Se a busca inicial na GBA falhar, o sistema pode determinar imediatamente que o código é inválido ou não está catalogado, abortando a execução antes de incorrer no custo e na latência de uma chamada de LLM Grounding.4

Além disso, a manutenção é simplificada. Se o layout da página de preços da Amazon mudar, apenas o prompt do LLM (Fase 2\) precisa ser ajustado. Se a fonte bibliográfica (GBA) mudar a formatação de seus dados, apenas o parser da Fase 1 é afetado. O risco de falha é desacoplado, o que aumenta a longevidade e a estabilidade da função BUSCAR\_DADOS\_AMAZON.

## **III. Avaliação e Comparativo de APIs Públicas de Livros para EAN/ISBN**

Para implementar o modelo híbrido, é imperativo selecionar a API de metadados mais adequada. O foco recai sobre a Google Books API (GBA) e a Open Library API (OLA).

### **3.1. Google Books API (GBA): Vantagens e Limitações**

A GBA é a opção mais indicada devido à sua integração natural com o ecossistema Google (GAS/Gemini) e suas características de escalabilidade:

* **Capacidade de Busca:** A GBA suporta nativamente a busca por ISBN ou EAN utilizando o parâmetro de consulta q=isbn:... 8, o que permite localizar edições específicas com alta precisão.  
* **Cota de Uso:** A GBA oferece cotas gratuitas extremamente generosas para chamadas de leitura (read-only calls), limitadas a 240 requisições por minuto, o que equivale a centenas de milhares de chamadas por dia, com a possibilidade de solicitar aumento de cota.6 Esta cota é ordens de grandeza maior do que o *free tier* do LLM Grounding.  
* **Viabilidade Técnica:** A integração via UrlFetchApp no GAS é simples e requer apenas uma chave API para acessar dados públicos.11  
* **Limitação:** A GBA não é uma fonte de dados comerciais e, portanto, não fornece os preços dinâmicos de varejistas, o que confirma a necessidade de manter o LLM para a extração de preços.

### **3.2. Open Library API (OLA): Uma Alternativa de Código Aberto**

A Open Library é uma fonte valiosa de metadados abertos.12 No entanto, sua estrutura é mais complexa.

* **Estrutura de Dados:** A OLA diferencia entre Works (informação genérica do livro) e Editions (informação específica do ISBN/Editora).12 A extração rigorosa de dados como a Editora, que varia por edição, exige a manipulação dos endpoints de Editions ou a utilização da API específica por ISBN.12  
* **Gestão de Limites:** A OLA adverte que aplicações de uso frequente devem incluir um *header* User-Agent com informações de contato, indicando que a gestão de limites de taxa é menos automatizada e mais propensa a bloqueios se não for seguida essa diretriz.13

Dada a simplicidade de uso, a alta velocidade de retorno (baixa latência) e a cota extremamente alta, a **Google Books API é a solução primária** para a Fase 1 da extração. A Tabela 1 sumariza a análise comparativa:

Comparativo de Custo e Funcionalidade das APIs Públicas de Livros

| API | Busca por EAN/ISBN | Retorno de Dados (Formato) | Cota Gratuita (RPS/RPM) | Viabilidade GAS/Facilidade |
| :---- | :---- | :---- | :---- | :---- |
| **Google Books API** | Sim (q=isbn:...) | Sim (JSON) | Altíssimo (240 requisições/min) | Muito Alta (Integração direta com API Key) |
| **Open Library API** | Sim (via Editions) | Sim (JSON/YAML) | Moderada (Requer User-Agent e gestão de Editions) | Moderada |

## **IV. Proposta da Nova Arquitetura Híbrida Otimizada**

A arquitetura otimizada implementa um fluxo de trabalho em três fases dentro da função principal BUSCAR\_DADOS\_AMAZON\_HIBRIDA(ean).

### **4.1. Fluxo Detalhado da Função Híbrida**

O fluxo garante que o LLM Grounding só seja acionado após a validação do ISBN pela GBA, maximizando a eficiência e minimizando custos:

1. **Fase 1: Consulta de Metadados (API Google Books):**  
   * O EAN é submetido à GBA. Se a GBA retornar Título, Autor e Editora em JSON limpo e estruturado, esses dados são armazenados como resultado parcial.  
   * Se a GBA falhar em encontrar o EAN (o que indica que o código é inválido ou o livro não está catalogado em fontes bibliográficas canônicas), a função aborta e retorna uma mensagem de "EAN Inválido/Não Catalogado", economizando o custo da requisição LLM.  
2. **Fase 2: Consulta de Preços (LLM Grounding Otimizado):**  
   * A nova função otimizada, callGeminiApiOtimizada(ean), é acionada. O LLM agora recebe uma instrução de prompt dramaticamente reduzida, focada estritamente na extração de precoSemDesconto e precoComDesconto da Amazon.  
   * A premissa é que, como a GBA já validou o EAN, o LLM não precisa mais se preocupar com validação de EAN ou extração de metadados complexos.  
3. **Fase 3: Consolidação e Formatação:**  
   * Os metadados canônicos da GBA são combinados com os preços extraídos pelo LLM.  
   * O resultado final é formatado (preços em R$ X,XX) e retornado como um array de cinco elementos para a planilha.2

### **4.2. Redefinição do Prompt Gemini para Extração Otimizada**

A otimização mais valiosa reside na simplificação do systemPrompt e do userQuery para a chamada do LLM, conforme detalhado na Tabela 2\.

A redução da complexidade da tarefa do LLM (de extrair 5 campos e validar o EAN, para extrair apenas 2 campos de preço) tem uma implicação direta na qualidade do dado dinâmico. O modelo tem agora maior "foco cognitivo" para identificar e extrair corretamente padrões numéricos e de desconto na página da Amazon, que são os dados mais sensíveis ao negócio e mais variáveis em sua apresentação.

Comparativo de Prompt Gemini (Antes vs. Depois)

| Componente | Arquitetura Anterior 2 | Arquitetura Híbrida Proposta (Otimizada) | Justificativa |
| :---- | :---- | :---- | :---- |
| **userQuery** | EAN/ISBN: ${ean} livro Amazon Brasil \- preço, autor e editora | EAN/ISBN: ${ean} Amazon Brasil. Extraia estritamente apenas o preço sem e com desconto. | Foco exclusivo nos dados dinâmicos. |
| **systemPrompt** | Extrator rigoroso de 5 campos, com validação de EAN e retorno de {} em caso de falha. | Extrator de preços da Amazon. **Suponha que o EAN/ISBN é válido**. Extraia **apenas** 'precoSemDesconto' e 'precoComDesconto'. Se um preço não existir, use o outro. Retorne APENAS o objeto JSON. | Redução da carga de trabalho do LLM e aumento da precisão nos preços. |

### **4.3. Estratégias de Fallback e Tratamento de Erros no Modelo Híbrido**

O novo modelo melhora as estratégias de *fallback*. Se a Fase 1 for bem-sucedida, mas a Fase 2 (LLM Grounding) falhar—seja por um erro de limite de taxa 429, falha de conexão, ou incapacidade do LLM de encontrar preços—o sistema ainda pode retornar os Metadados Válidos (Título, Autor, Editora) obtidos pela GBA. Os campos de preço seriam preenchidos com placeholders como "Preço Não Encontrado". Isso contrasta com a arquitetura anterior, onde qualquer falha do LLM resultava em uma falha total e o retorno de "Busca falhou" para todos os cinco campos.2 A capacidade de retornar dados canônicos parciais aumenta significativamente a utilidade do sistema.

## **V. Análise de Impacto: Custo, Desempenho e Confiabilidade**

A transição para a arquitetura híbrida proporciona benefícios quantificáveis em custo e robustez.

### **5.1. Projeção de Redução de Custo Operacional (Baseline Gemini vs. Híbrido)**

O custo do Grounding (pós-free tier) permanece em $35 por 1.000 requisições.5 O ganho financeiro não está na redução do preço unitário, mas na eliminação massiva de chamadas desnecessárias ou inválidas que consomem esse recurso caro.

A Google Books API absorve quase toda a necessidade de extração de metadados, utilizando sua cota gratuita de 240 RPS.6 O LLM é reservado apenas para o dado proprietário. A GBA atua como um filtro rigoroso: apenas EANs válidos e catalogados que passaram pela Fase 1 (custo zero) prosseguem para a Fase 2 (custo potencial de $35/1k). Isso garante que o custo de Grounding nunca seja incorrido para códigos inválidos.

Comparativo de Custo e Risco por Tipo de Extração (1.000 Requisições)

| Mecanismo | Dados Extraídos | Custo Estimado (Após Free Tier) | Estabilidade do Retorno | Latência Típica |
| :---- | :---- | :---- | :---- | :---- |
| **Gemini Grounding (Baseline)** | 5 Campos (Metadados \+ Preço) | \~$35.00 / 1.000 requests | Média (Alta dependência de Prompt/Limpeza JSON) | Alta (LLM \+ Web Search) |
| **Google Books API (Fase 1\)** | 3 Metadados Estáveis | $0.00 (Free Tier de 240 RPS) | Muito Alta (JSON Estruturado Padrão) | Baixa (API de metadados simples) |
| **Modelo Híbrido (Proposto)** | 5 Campos (Metadados via GBA, Preços via LLM) | \~$35.00 / 1.000 requests | Alta (Separação de Responsabilidades e Prompts Simplificados) | Moderada (Latência dominada pelo LLM Grounding) |

### **5.2. Aumento da Velocidade de Resposta (Latência)**

Embora a latência geral seja ainda dominada pela chamada de LLM Grounding (que envolve tempo de processamento do modelo e da busca web), a latência da Fase 1 (GBA) é extremamente baixa, característica das APIs de metadados simples. A GBA permite uma resposta rápida de falha para EANs inválidos, melhorando a experiência do usuário, que não precisa esperar pela expiração de um timeout caro do LLM. Em ambientes escaláveis (fora do GAS), a natureza rápida da GBA permitiria até mesmo uma paralelização mais eficaz da execução.

### **5.3. Confiabilidade e Robustez: Otimização da Cadeia de Valor**

O valor agregado final reside na robustez inerente à separação de tarefas. Os metadados críticos são agora extraídos de uma fonte de autoridade bibliográfica, não de inferência textual. Essa abordagem eleva a segurança de dados e a precisão canônica do Título e Autor.

A simplificação do *payload* de saída da Gemini (apenas 2 campos) torna o tratamento de erros e a limpeza do JSON no GAS muito mais previsíveis. O LLM tem menos margem para introduzir texto extra ou formatação incorreta. Caso a restrição de erro 400 persista, exigindo a manutenção da lógica de limpeza de JSON via regex, o formato de retorno simplificado aumentará significativamente a confiabilidade desse processo de limpeza. O acoplamento de riscos foi efetivamente desfeito, resultando em um sistema mais fácil de manter e mais resistente a mudanças futuras nas fontes de dados.

## **VI. Conclusões e Recomendações**

A integração de APIs públicas de livros, especificamente a Google Books API, agrega valor fundamental ao projeto de extração de dados da Amazon, transformando a arquitetura monolítica baseada em LLM em um modelo híbrido eficiente e economicamente escalável.

A principal conclusão é que o LLM Grounding, um recurso caro e de alta latência, deve ser reservado exclusivamente para a extração de dados proprietários e dinâmicos (preços). A utilização da GBA, com sua cota robusta de 240 requisições por minuto, garante que a extração de metadados estáticos (Título, Autor, Editora) seja gratuita, canônica e altamente confiável.

As recomendações para o próximo passo de desenvolvimento são:

1. **Implementação da Função GBA:** Criar a nova função BUSCAR\_METADADOS\_GBA(ean) no Google Apps Script para consumir a Google Books API via EAN/ISBN, retornando um objeto JSON estruturado contendo Título, Autor e Editora.  
2. **Otimização do LLM:** Clonar a função callGeminiApi para criar callGeminiApiOtimizada, ajustando o systemPrompt e o userQuery para focar estritamente na extração de precoSemDesconto e precoComDesconto.  
3. **Refatoração da Função Principal:** Alterar BUSCAR\_DADOS\_AMAZON(ean) para implementar o fluxo de trabalho sequencial de três fases (GBA, LLM, Consolidação), garantindo que as lógicas de *retry* e *exponential backoff* permaneçam na chamada do LLM.2

Este novo design não só melhora a robustez operacional do código existente, mitigando a fragilidade da limpeza de JSON 2, mas também garante a viabilidade financeira do projeto em volumes de alta demanda.

#### **Referências citadas**

1. continuou com problemas  
2. GoogleAppsScript.gs  
3. Gemini Developer API Pricing, acessado em outubro 14, 2025, [https://ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing)  
4. Grounding with Google Search | Gemini API, acessado em outubro 14, 2025, [https://ai.google.dev/gemini-api/docs/google-search](https://ai.google.dev/gemini-api/docs/google-search)  
5. The True Cost of Google Gemini A Guide to API Pricing and Integration \- MetaCTO, acessado em outubro 14, 2025, [https://www.metacto.com/blogs/the-true-cost-of-google-gemini-a-guide-to-api-pricing-and-integration](https://www.metacto.com/blogs/the-true-cost-of-google-gemini-a-guide-to-api-pricing-and-integration)  
6. Quotas and limits | API Keys API Documentation \- Google Cloud, acessado em outubro 14, 2025, [https://cloud.google.com/api-keys/docs/quotas](https://cloud.google.com/api-keys/docs/quotas)  
7. Books APIs \- Google for Developers, acessado em outubro 14, 2025, [https://developers.google.com/books](https://developers.google.com/books)  
8. Trying to use ISBNs to pull book info and getting conflicting API returns : r/GoogleAppsScript, acessado em outubro 14, 2025, [https://www.reddit.com/r/GoogleAppsScript/comments/11m2inr/trying\_to\_use\_isbns\_to\_pull\_book\_info\_and\_getting/](https://www.reddit.com/r/GoogleAppsScript/comments/11m2inr/trying_to_use_isbns_to_pull_book_info_and_getting/)  
9. Google Books API find exact author \- Stack Overflow, acessado em outubro 14, 2025, [https://stackoverflow.com/questions/66392498/google-books-api-find-exact-author](https://stackoverflow.com/questions/66392498/google-books-api-find-exact-author)  
10. Google Books API rate limiting information? \- Stack Overflow, acessado em outubro 14, 2025, [https://stackoverflow.com/questions/35302157/google-books-api-rate-limiting-information](https://stackoverflow.com/questions/35302157/google-books-api-rate-limiting-information)  
11. Using the API | Google Books APIs, acessado em outubro 14, 2025, [https://developers.google.com/books/docs/v1/using](https://developers.google.com/books/docs/v1/using)  
12. Developer Center / APIs / Books API \- Open Library, acessado em outubro 14, 2025, [https://openlibrary.org/dev/docs/api/books](https://openlibrary.org/dev/docs/api/books)  
13. APIs | Open Library, acessado em outubro 14, 2025, [https://openlibrary.org/developers/api](https://openlibrary.org/developers/api)

# Atualização 20251104

# **Otimização Híbrida de Extração de Dados de Livros: Estratégias de Desacoplamento de LLMs via Integração de APIs Públicas**

... (Conteúdo das Seções I a V mantido)

## **VI. Conclusões e Recomendações**

A integração de APIs públicas de livros, especificamente a Google Books API, agrega valor fundamental ao projeto de extração de dados da Amazon, transformando a arquitetura monolítica baseada em LLM em um modelo híbrido eficiente e economicamente escalável.

A principal conclusão é que o LLM Grounding, um recurso caro e de alta latência, deve ser reservado exclusivamente para a extração de dados proprietários e dinâmicos (preços). A utilização da GBA, com sua cota robusta de **240 requisições por minuto**, garante que a extração de metadados estáticos (**Título, Subtítulo, Autor(es), Editora**) seja gratuita, canônica e altamente confiável.

As recomendações para o próximo passo de desenvolvimento são:

1. **Implementação da Função GBA:** Criar a nova função `BUSCAR_METADADOS_GBA(ean)` no Google Apps Script para consumir a Google Books API via EAN/ISBN, retornando um objeto JSON estruturado contendo **Título, Subtítulo, Autor(es) e Editora**.
2. **Otimização do LLM:** Clonar a função `callGeminiApi` para criar `callGeminiApiOtimizada`, ajustando o `systemPrompt` e o `userQuery` para focar estritamente na extração de `precoSemDesconto` e `precoComDesconto`.
3. **Refatoração da Função Principal:** Alterar `BUSCAR_DADOS_AMAZON(ean)` para implementar o fluxo de trabalho sequencial de três fases (GBA, LLM, Consolidação), garantindo que as lógicas de *retry* e *exponential backoff* permaneçam na chamada do LLM.

### **Próximo Passo Crítico: Exportação para Google Sheets**

O projeto está pronto para a sua próxima grande fase: persistência de dados. Os requisitos críticos para a continuidade do desenvolvimento são:
* **Objetivo:** Implementar uma função de exportação para o Google Sheets usando a biblioteca **`gspread`** (ou similar) no arquivo `extrator_livros.py`.
* **Credenciais e Autenticação:** É necessário configurar uma **Conta de Serviço (Service Account)** no Google Cloud e obter o arquivo de credenciais (`.json`). O código deve carregar essas credenciais e garantir que a planilha de destino tenha permissão de leitura/escrita para o e-mail da Service Account.
* **Lógica de Exportação:** Definir o ID da Planilha e o Nome da Aba alvo e decidir se a função de exportação deve sobrescrever os dados ou adicionar novas linhas.

Este novo design não só melhora a robustez operacional do código existente, mitigando a fragilidade da limpeza de JSON, mas também garante a viabilidade financeira do projeto em volumes de alta demanda.

#### **Referências citadas**
... (Referências citadas mantidas)