from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os

from google import genai
from google.genai import types

# inicializa o app
app = FastAPI(
    title="PetDoc API",
    description="Assistente veterinário virtual do app Pet Family",
    version="1.0.0"
)

# permite chamadas do app mobile (React Native / Expo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# inicializa o cliente Gemini com a chave do ambiente
cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODELO = "gemini-3.8-flash"


# ---- modelos de dados ----

class DadosPet(BaseModel):
    nome: str
    especie: str
    raca: str
    idade: str
    peso: str
    sexo: str
    notas: Optional[str] = ""

class MensagemRequest(BaseModel):
    mensagem: str
    pet: DadosPet
    historico: Optional[list] = []  # lista de {"role": "user"|"model", "text": "..."}

class RespostaAssistente(BaseModel):
    resposta: str
    urgencia: str   # "baixa", "media" ou "alta"
    recomenda_vet: bool


# ---- funções auxiliares ----

def montar_system_prompt(pet: DadosPet) -> str:
    return f"""
Você é o assistente veterinário virtual do app Pet Family, chamado PetDoc.

Seu papel é ajudar tutores de pets com dúvidas sobre saúde, vacinas, alimentação,
comportamento e bem-estar dos seus animais. Responda de forma clara, acolhedora
e acessível — o tutor não é veterinário.

Dados do pet do tutor:
- Nome: {pet.nome}
- Espécie: {pet.especie}
- Raça: {pet.raca}
- Idade: {pet.idade}
- Peso: {pet.peso}
- Sexo: {pet.sexo}
- Observações: {pet.notas}

Regras importantes:
1. Sempre considere os dados do pet acima ao responder.
2. Para situações de emergência ou sintomas graves, oriente o tutor a procurar
   um veterinário imediatamente. Nunca substitua uma consulta presencial.
3. Não invente informações médicas. Se não souber, diga que não sabe.
4. Seja direto e objetivo. Evite respostas muito longas.
5. Chame o pet sempre pelo nome ({pet.nome}).

FORMATO DE RESPOSTA OBRIGATÓRIO:
Responda SEMPRE com um JSON válido, sem nenhum texto fora do JSON:
{{
  "resposta": "texto da resposta para o tutor",
  "urgencia": "baixa" | "media" | "alta",
  "recomenda_vet": true | false
}}

Critérios de urgência:
- "baixa": dúvidas gerais, cuidados preventivos, comportamento normal
- "media": sintomas leves que merecem atenção nos próximos dias
- "alta": sintomas graves, emergências, risco de vida
"""


# ---- endpoints ----

@app.get("/")
def raiz():
    return {"status": "ok", "servico": "PetDoc API", "versao": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=RespostaAssistente)
def chat(req: MensagemRequest):
    system_prompt = montar_system_prompt(req.pet)

    # monta o histórico no formato que o SDK espera
    historico_sdk = []
    for msg in req.historico:
        historico_sdk.append(
            types.Content(
                role=msg["role"],
                parts=[types.Part(text=msg["text"])]
            )
        )

    try:
        # se há histórico, usa chat; senão, chamada simples
        if historico_sdk:
            chat_session = cliente.chats.create(
                model=MODELO,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json"
                ),
                history=historico_sdk
            )
            resposta = chat_session.send_message(req.mensagem)
        else:
            resposta = cliente.models.generate_content(
                model=MODELO,
                contents=req.mensagem,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json"
                )
            )

        dados = json.loads(resposta.text)
        return RespostaAssistente(**dados)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Resposta inválida do modelo")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
