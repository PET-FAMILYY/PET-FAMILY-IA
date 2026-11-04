# 🐾 Pet Family IA — Assistente Veterinário com IA Generativa

> Componente de Inteligência Artificial do projeto Pet Family — API FastAPI integrada com Gemini API (Google AI) para orientação veterinária preventiva personalizada, contextualizada com os dados reais do pet cadastrado no aplicativo mobile.

---

## Contexto do Projeto

O **Pet Family** é um ecossistema de cuidado contínuo para pets desenvolvido para o **Challenge FIAP 2026 — Clyvo Vet**. A plataforma conecta tutores, pets e clínicas veterinárias, promovendo o acompanhamento preventivo e a recorrência de consultas.

Este repositório concentra a proposta, arquitetura e o código do componente de **Inteligência Artificial Generativa** (PetDoc API) que alimenta o Assistente Pet Family — presente na tela de chat do aplicativo mobile.

---

## Problema de Negócio

Tutores de pets frequentemente não sabem interpretar sinais do cotidiano do animal — alimentação irregular, comportamentos atípicos, dúvidas sobre vacinas e vermifugação — sem orientação especializada. Isso resulta em:

- Consultas veterinárias apenas em emergências, reduzindo a recorrência nas clínicas
- Dados do pet cadastrados no app (raça, idade, peso, observações de saúde) sem uso real nas respostas
- Assistente de chat com respostas fixas baseadas em palavras-chave, sem capacidade de entender contexto ou perguntas inéditas

---

## Solução Proposta: IA Generativa com Contexto Dinâmico

Substituição do motor de respostas fixas (`AssistenteIASimulado` do backend Java) por chamadas reais à **Gemini API (Google AI)**, com um **system prompt dinâmico** que injeta:

- Perfil completo do pet (nome, espécie, raça, idade, peso, observações de saúde)
- Histórico recente da conversa (mantido em memória por `petId`)

---

## Como a IA Agrega Valor

| Cenário | Sem IA (simulado) | Com IA Generativa |
|---|---|---|
| "Meu gato pode comer abacate?" | Resposta genérica por palavra-chave | Resposta contextualizada pela espécie e raça cadastrada |
| "Ele tá comendo menos que o normal" | Redireciona ao veterinário | Analisa o perfil do pet e sugere observação ou consulta |
| "Vacina dele vence quando?" | Não tem essa informação | Responde com base nas observações de saúde cadastradas |
| Pergunta inédita | Resposta de fallback genérica | Raciocínio contextual real via LLM |

---

## Abordagem de IA: Por que IA Generativa / LLM?

### Alternativas consideradas

| Abordagem | Por que descartada |
|---|---|
| Sistema de regras (if/else) | Já existia, não escala, não entende contexto nem perguntas inéditas |
| Modelo preditivo treinado | Requer dataset próprio de saúde veterinária — inviável no prazo |
| Sistema de recomendação | Focado em itens/produtos, não em diálogo natural livre |
| NLP clássico (intent detection) | Limitado a intenções pré-definidas, sem raciocínio contextual |

### Por que Gemini (Google AI Studio)

- Abordagem ensinada na disciplina (Gemini API, prompt engineering)
- O modelo já possui conhecimento veterinário preventivo embutido — sem necessidade de fine-tuning
- Personalização via **prompt engineering**: perfil do pet injetado a cada requisição
- Gratuito no Google AI Studio para uso acadêmico
- SDK Python simples (`google-genai`), integrável diretamente na API FastAPI

---

## Arquitetura de Integração (Sprint 4)

**Fluxo:**

```
Tutor (app mobile — chat.tsx)
        ↓ POST /interacoes-ia com dados do pet
PetDoc API (FastAPI — pet-family-ia.onrender.com)
  ├── 1. Recebe pergunta + perfil completo do pet
  ├── 2. Monta system prompt dinâmico com contexto do pet
  ├── 3. Envia para Gemini API via google-genai SDK
  ├── 4. Armazena interação em memória (por petId)
  └── 5. Retorna resposta em linguagem natural
        ↓
chat.tsx exibe resposta na bolha do assistente
```

---

## Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/health` | Health check do serviço |
| `POST` | `/interacoes-ia` | Envia pergunta e recebe resposta do assistente (usado pelo mobile) |
| `GET` | `/interacoes-ia/pet/{pet_id}` | Lista histórico de interações de um pet |
| `POST` | `/chat` | Endpoint acadêmico usado no notebook (Labs 1–3) |

### Exemplo de requisição — `POST /interacoes-ia`

```json
{
  "pergunta": "Quais vacinas meu pet precisa?",
  "petId": 1,
  "petNome": "Bolinha",
  "petEspecie": "cachorro",
  "petRaca": "Golden Retriever",
  "petIdade": 3,
  "petPeso": 28.0,
  "petObservacoes": "Alergia a frango"
}
```

### Exemplo de resposta

```json
{
  "id": 1,
  "pergunta": "Quais vacinas meu pet precisa?",
  "resposta": "Oi! Para o Bolinha, um Golden Retriever de 3 anos, as vacinas essenciais são...",
  "dataHora": "2026-11-02T21:00:00+00:00",
  "categoria": null,
  "petId": 1,
  "petNome": "Bolinha"
}
```

---

## Dados Utilizados pela IA

### Perfil do Pet (enviado pelo app mobile)

| Campo | Tipo | Uso pela IA |
|---|---|---|
| `petNome` | string | Personalização das respostas (chama o pet pelo nome) |
| `petEspecie` | string | Adapta recomendações por espécie |
| `petRaca` | string | Considera predisposições da raça |
| `petIdade` | float | Ajusta frequências de vacina, check-up e vermifugação |
| `petPeso` | float | Orientações de dosagem e nutrição |
| `petObservacoes` | string | Contexto de condições preexistentes |

---

## Stack Técnica

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.11 | Linguagem principal |
| FastAPI | 0.143.0 | Framework da API REST |
| google-genai | 2.29.0 | SDK oficial do Gemini API |
| Uvicorn | 0.54.0 | Servidor ASGI |
| Render | — | Deploy em nuvem (plano gratuito) |

---

## Deploy

A API está deployada no Render:

**Base URL:** `https://pet-family-ia.onrender.com`

> O plano gratuito do Render hiberna após inatividade. O primeiro acesso pode demorar até 2 minutos (cold start).

### Variáveis de ambiente necessárias

| Variável | Descrição |
|---|---|
| `GEMINI_API_KEY` | Chave da Gemini API (Google AI Studio) |

### Como rodar localmente

```bash
# clonar o repositório
git clone https://github.com/PET-FAMILYY/PET-FAMILY-IA.git
cd PET-FAMILY-IA/pet-family-ia

# criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# instalar dependências
pip install -r requirements.txt

# configurar variável de ambiente
cp .env.example .env
# editar .env e adicionar sua GEMINI_API_KEY

# rodar a API
uvicorn app.main:app --reload --port 8000
```

---

## Estrutura do Repositório

```
PET-FAMILY-IA/
├── README.md
├── assistente_pet_family.ipynb    ← notebook acadêmico (Labs 1–3)
├── docs/
│   └── architecture-diagram.html  ← diagrama interativo da arquitetura
└── pet-family-ia/
    ├── app/
    │   └── main.py                ← código da API FastAPI + integração Gemini
    ├── requirements.txt
    ├── Dockerfile
    ├── render.yaml
    └── .env.example
```

---

## Evolução entre Sprints

### Sprint 3 — Proposta e Arquitetura
- Definição da abordagem de IA Generativa com Gemini
- Documentação do problema de negócio e solução proposta
- Arquitetura de integração planejada (mobile → IA → Gemini)
- Diagrama interativo da arquitetura

### Sprint 4 — Implementação e Integração
- **API FastAPI implementada** com endpoints `/interacoes-ia` e `/chat`
- **System prompt dinâmico** com injeção de dados reais do pet
- **Histórico em memória** por `petId` para continuidade de contexto
- **Deploy no Render** com variáveis de ambiente seguras
- **Integração com o app mobile** — `chat.tsx` + `interacoesIaApi.ts` chamando a API com retry automático (3 tentativas com backoff para lidar com cold start e sobrecarga do Gemini)
- **Notebook acadêmico** (`assistente_pet_family.ipynb`) demonstrando Labs 1–3 com o endpoint `/chat`
- Testes validados em cenários reais de uso via Postman e Expo Go

---

## Vídeos

| Sprint | Link |
|---|---|
| Sprint 3 — Pitch e Proposta | [Assistir no YouTube](https://youtu.be/yRoGgqYLlVg) |
| Sprint 4 — Demonstração da IA implementada | [Assistir no YouTube](https://youtu.be/SFHiU1p0MBQ) |

---

## Integrantes

| Nome | RM | Turma |
|---|---|---|
| Felipe Kirschner Modesto | RM 561810 | 2TDSPG |
| João Victor Luiz de Oliveira Resende | RM 565139 | 2TDSPG |
| Pedro Henrique Vaz Ferreira | RM 566551 | 2TDSPG |
| Vitor Dias dos Santos | RM 565422 | 2TDSPG |

---

> **FIAP 2026** · Challenge Clyvo Vet · 2º Semestre  
> Disciplina: Disruptive Architectures: IoT, IoB & Generative IA  
> Prof. Arnaldo · Turma 2TDSPG  
> Sprint 3: 12/09/2026 · Sprint 4: 04/11/2026
