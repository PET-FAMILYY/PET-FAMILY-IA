from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
import uuid
from datetime import datetime, timezone

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
MODELO = "gemini-2.0-flash"

# armazenamento em memória das interações (por sessão)
# chave: petId → lista de InteracaoIAResponse
_historico: dict[int, list[dict]] = {}
_contador_id = 0


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
    """Endpoint /chat — usado pelo notebook acadêmico (Lab 1-3)."""
    mensagem: str
    pet: DadosPet
    historico: Optional[list] = []  # lista de {"role": "user"|"model", "text": "..."}

class RespostaAssistente(BaseModel):
    resposta: str
    urgencia: str   # "baixa", "media" ou "alta"
    recomenda_vet: bool

# contrato do mobile (mesmo formato do backend Java)
class InteracaoIARequest(BaseModel):
    pergunta: str
    petId: int
    categoria: Optional[str] = None
    # dados opcionais do pet — se não vierem, usamos valores genéricos
    petNome: Optional[str] = None
    petEspecie: Optional[str] = None
    petRaca: Optional[str] = None
    petIdade: Optional[float] = None
    petPeso: Optional[float] = None
    petObservacoes: Optional[str] = None

class InteracaoIAResponse(BaseModel):
    id: int
    pergunta: str
    resposta: str
    dataHora: str
    categoria: Optional[str]
    petId: int
    petNome: str


# ---- funções auxiliares ----

def montar_system_prompt_completo(
    nome: str,
    especie: str,
    raca: Optional[str],
    idade: Optional[float],
    peso: Optional[float],
    observacoes: Optional[str],
) -> str:
    raca_str = raca or "não informada"
    idade_str = f"{int(idade)} ano(s)" if idade else "não informada"
    peso_str = f"{peso} kg" if peso else "não informado"
    obs_str = observacoes or "nenhuma"

    return f"""
Você é o assistente veterinário virtual do app Pet Family, chamado PetDoc.

Seu papel é ajudar tutores de pets com dúvidas sobre saúde, vacinas, alimentação,
comportamento e bem-estar dos seus animais. Responda de forma clara, acolhedora
e acessível — o tutor não é veterinário.

Dados do pet do tutor:
- Nome: {nome}
- Espécie: {especie}
- Raça: {raca_str}
- Idade: {idade_str}
- Peso: {peso_str}
- Observações de saúde: {obs_str}

Regras importantes:
1. Sempre considere os dados do pet acima ao responder.
2. Para situações de emergência ou sintomas graves, oriente o tutor a procurar
   um veterinário imediatamente. Nunca substitua uma consulta presencial.
3. Não invente informações médicas. Se não souber, diga que não sabe.
4. Seja direto e objetivo. Evite respostas muito longas.
5. Chame o pet sempre pelo nome ({nome}).

Responda em texto corrido, de forma amigável e objetiva.
"""

def montar_system_prompt(pet: DadosPet) -> str:
    return montar_system_prompt_completo(
        nome=pet.nome,
        especie=pet.especie,
        raca=pet.raca,
        idade=None,
        peso=None,
        observacoes=pet.notas,
    )

def gerar_resposta_gemini(pergunta: str, system_prompt: str) -> str:
    resposta = cliente.models.generate_content(
        model=MODELO,
        contents=pergunta,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        )
    )
    return resposta.text.strip()


# ---- endpoints ----

@app.get("/")
def raiz():
    return {"status": "ok", "servico": "PetDoc API", "versao": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}


# ---- endpoint para o notebook acadêmico (Labs 1-3) ----

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


# ---- endpoints para o app mobile (contrato igual ao backend Java) ----

@app.post("/interacoes-ia", response_model=InteracaoIAResponse)
def criar_interacao_ia(req: InteracaoIARequest):
    global _contador_id

    pet_nome = req.petNome or f"Pet #{req.petId}"
    pet_especie = req.petEspecie or "animal de estimação"
    pet_raca = req.petRaca
    pet_idade = req.petIdade
    pet_peso = req.petPeso
    pet_obs = req.petObservacoes

    system_prompt = montar_system_prompt_completo(
        nome=pet_nome,
        especie=pet_especie,
        raca=pet_raca,
        idade=pet_idade,
        peso=pet_peso,
        observacoes=pet_obs,
    )

    try:
        resposta_texto = gerar_resposta_gemini(req.pergunta, system_prompt)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erro ao consultar IA: {str(e)}")

    _contador_id += 1
    data_hora = datetime.now(timezone.utc).isoformat()

    interacao = {
        "id": _contador_id,
        "pergunta": req.pergunta,
        "resposta": resposta_texto,
        "dataHora": data_hora,
        "categoria": req.categoria,
        "petId": req.petId,
        "petNome": pet_nome,
    }

    # armazena no histórico em memória
    if req.petId not in _historico:
        _historico[req.petId] = []
    _historico[req.petId].append(interacao)

    return InteracaoIAResponse(**interacao)


@app.get("/interacoes-ia/pet/{pet_id}", response_model=list[InteracaoIAResponse])
def listar_interacoes_do_pet(pet_id: int):
    return [InteracaoIAResponse(**i) for i in _historico.get(pet_id, [])]