# 🐾 Pet Family IA — Assistente Veterinário com IA Generativa

> Componente de Inteligência Artificial do projeto Pet Family — integração com Gemini API para orientação veterinária preventiva personalizada, contextualizada com dados reais do pet e do comedouro IoT.

---

## Contexto do Projeto

O **Pet Family** é um ecossistema de cuidado contínuo para pets desenvolvido para o **Challenge FIAP 2026 — Clyvo Vet**. A plataforma conecta tutores, pets e clínicas veterinárias, promovendo o acompanhamento preventivo e a recorrência de consultas.

Este repositório concentra a proposta, arquitetura e documentação do componente de **Inteligência Artificial Generativa** que alimenta o Assistente Pet Family — presente na tela de chat do aplicativo mobile.

---

## Problema de Negócio

Tutores de pets frequentemente não sabem interpretar sinais do cotidiano do animal — hábitos alimentares irregulares, temperatura ambiente inadequada, comportamentos atípicos — sem orientação especializada. Isso resulta em:

- Consultas veterinárias apenas em emergências, reduzindo a recorrência nas clínicas
- Dados coletados pelo comedouro IoT (temperatura, umidade, nível de ração, frequência de alimentação) subutilizados — existem, mas não geram valor ao tutor
- Assistente de chat com respostas fixas baseadas em palavras-chave, sem capacidade de entender contexto ou perguntas inéditas

---

## Solução Proposta: IA Generativa com Contexto Dinâmico

Substituição do motor de respostas fixas (`if/else` por palavras-chave) por chamadas reais à **Gemini API (Google AI)**, com um **system prompt dinâmico** que injeta:

- Perfil completo do pet (nome, espécie, raça, idade, peso, notas de saúde)
- Dados em tempo real do comedouro IoT (temperatura, umidade, nível de ração, horário da última alimentação, contagem de refeições do dia)
- Histórico recente da conversa (últimas 10 mensagens para continuidade de contexto)

---

## Como a IA Agrega Valor

| Cenário | Sem IA (atual) | Com IA Generativa |
|---|---|---|
| "Meu gato comeu hoje?" | Não sabe responder | Consulta dados do IoT e responde com horário e quantidade |
| "A temperatura tá boa para o Rex?" | Resposta genérica | Usa os °C do DHT22 e o perfil da raça para orientar |
| "Ele tá comendo menos que o normal" | Redireciona ao veterinário | Analisa histórico de alimentações e sugere observação ou consulta |
| "Vacina dele vence quando?" | Não tem essa informação | Responde com base nas notas de saúde cadastradas no perfil |
| Pergunta inédita | Resposta de fallback genérica | Raciocínio contextual real via LLM |

---

## Abordagem de IA: Por que IA Generativa / LLM?

### Alternativas consideradas

| Abordagem | Por que descartada |
|---|---|
| Sistema de regras (if/else) | Já existe, não escala, não entende contexto nem perguntas inéditas |
| Modelo preditivo treinado | Requer dataset próprio de saúde veterinária — inviável no prazo |
| Sistema de recomendação | Focado em itens/produtos, não em diálogo natural livre |
| NLP clássico (intent detection) | Limitado a intenções pré-definidas, sem raciocínio contextual |

### Por que Gemini 1.5 Flash

- É a abordagem ensinada na disciplina (Gemini API, prompt engineering)
- O modelo já possui conhecimento veterinário preventivo embutido — não requer fine-tuning
- Personalização via **prompt engineering**: contexto do pet e do IoT injetado a cada requisição
- Gratuito no Google AI Studio para uso acadêmico
- API REST simples, integrável diretamente no app mobile

---

## Dados Utilizados pela IA

[Ver diagrama interativo](https://pet-familyy.github.io/PET-FAMILY-IA/docs/architecture-diagram.html)

### Perfil do Pet (AsyncStorage — App Mobile)

| Campo | Tipo | Uso pela IA |
|---|---|---|
| `name` | string | Personalização das respostas |
| `species` | `dog` \| `cat` | Adapta recomendações por espécie |
| `breed` | string | Considera predisposições da raça |
| `age` | number | Ajusta frequências de vacina, check-up e vermifugação |
| `weight` | number | Orientações de dosagem e nutrição |
| `healthNotes` | string | Contexto de condições preexistentes |

### Comedouro IoT (ESP32 REST API — `GET /api/status`)

| Campo | Tipo | Uso pela IA |
|---|---|---|
| `temperature` | float | Alerta se fora da faixa ideal para a espécie/raça |
| `humidity` | float | Contexto ambiental para saúde respiratória |
| `foodLevel` | int (0–100%) | Informa nível de ração e sugere reabastecimento |
| `lastFeedTime` | string | Informa horário da última refeição |
| `feedCount` | int | Monitora frequência de alimentação do dia |
| `nextFeedIn` | int (ms) | Informa quando será a próxima alimentação automática |

---

## Arquitetura de Integração

**Fluxo resumido:**

```
Tutor (App Mobile — chat.tsx)
        ↓ mensagem do usuário
geminiService.ts
  ├── 1. Busca perfil do pet → AsyncStorage
  ├── 2. Busca dados do IoT  → GET /api/status (ESP32)
  ├── 3. Monta system prompt dinâmico com contexto completo
  ├── 4. Envia histórico + mensagem → Gemini API
  └── 5. Retorna resposta em linguagem natural
        ↓
chat.tsx exibe resposta na bolha "ai"
```

---

## Estrutura do Repositório

```
PET-FAMILY-IA/
├── README.md
└── docs/
    └── architecture-diagram.html
```

---

## Link Vídeo Pitch

[Clique aqui para assistir ao vídeo](https://youtu.be/yRoGgqYLlVg)

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
> Prof. Arnaldo · Turma 2TDSPG · Entrega Sprint 3: **12/09/2026**
