from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random
from fastapi.responses import RedirectResponse
app = FastAPI()

# Permitir chamadas do Live Server (ou qualquer frontend local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:5501", "http://localhost:5501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Personagens ---
class Personagem:
    def __init__(self, nome, vida, ataque, defesa):
        self.nome = nome
        self.vida = vida
        self.vida_max = vida
        self.ataque = ataque
        self.defesa = defesa
        self.pocoes = 1

    def atacar(self, outro):
        dano = max(0, self.ataque - outro.defesa)
        outro.vida -= dano
        return dano

    def esta_vivo(self):
        return self.vida > 0

    def usar_pocao(self):
        if self.pocoes > 0:
            cura = min(self.vida_max - self.vida, 30)
            self.vida += cura
            self.pocoes -= 1
            return cura
        return 0

class Guerreiro(Personagem):
    def __init__(self, nome):
        super().__init__(nome, 120, 25, 15)
    def ataque_especial(self, outro):
        dano = max(0, self.ataque*2 - outro.defesa)
        outro.vida -= dano
        return dano

class Mago(Personagem):
    def __init__(self, nome):
        super().__init__(nome, 80, 35, 5)
    def ataque_especial(self, outro):
        dano = max(0, int(self.ataque*2.5) - outro.defesa)
        outro.vida -= dano
        return dano

class Arqueiro(Personagem):
    def __init__(self, nome):
        super().__init__(nome, 90, 30, 10)
    def ataque_especial(self, outro):
        dano = max(0, self.ataque*2 - outro.defesa)
        outro.vida -= dano
        return dano

# --- Função para enviar personagens como dict ---
def personagem_para_dict(p):
    return {
        "nome": p.nome,
        "vida": p.vida,
        "vida_max": p.vida_max,
        "pocoes": p.pocoes
    }

# --- Estado da batalha ---
estado_batalha = {
    "jogador": Guerreiro("Herói"),
    "inimigo": random.choice([Guerreiro("Orc"), Mago("Bruxo"), Arqueiro("Ladino")]),
    "mensagens": []
}


def reiniciar_batalha():
    """Reinicia o estado da batalha para novos personagens e limpa mensagens."""
    estado_batalha["jogador"] = Guerreiro("Herói")
    estado_batalha["inimigo"] = random.choice([Guerreiro("Orc"), Mago("Bruxo"), Arqueiro("Ladino")])
    estado_batalha["mensagens"] = []

# --- Rotas ---

@app.get("/", include_in_schema=True)
def raiz():
    '''
    SAASDSADASDSDASDAS
    '''
    return RedirectResponse(url='/docs')
@app.get("/batalha")
def mostrar_batalha():
    return {
        "jogador": personagem_para_dict(estado_batalha["jogador"]),
        "inimigo": personagem_para_dict(estado_batalha["inimigo"]),
        "mensagens": estado_batalha["mensagens"]
    }

@app.post("/acao/{acao}")
def realizar_acao(acao: str):
    jogador = estado_batalha["jogador"]
    inimigo = estado_batalha["inimigo"]
    mensagens = estado_batalha["mensagens"]

    if not jogador.esta_vivo() or not inimigo.esta_vivo():
        raise HTTPException(status_code=400, detail="A batalha acabou! Reinicie a aplicação para jogar novamente.")

    # --- Turno do jogador ---
    if acao == "ataque":
        dano = jogador.atacar(inimigo)
        mensagens.append(f"Você atacou {inimigo.nome} causando {dano} de dano")
    elif acao == "especial":
        dano = jogador.ataque_especial(inimigo)
        mensagens.append(f"Você usou ataque especial causando {dano} de dano")
    elif acao == "pocao":
        cura = jogador.usar_pocao()
        mensagens.append(f"Você usou uma poção e recuperou {cura} de vida" if cura>0 else "Você não tem poções!")
    else:
        raise HTTPException(status_code=400, detail="Ação inválida. Use 'ataque', 'especial' ou 'pocao'.")

    # --- Checa se inimigo morreu ---
    if not inimigo.esta_vivo():
        mensagens.append(f"🎉 Você venceu {inimigo.nome}!")
        return {
            "jogador": personagem_para_dict(jogador),
            "inimigo": personagem_para_dict(inimigo),
            "mensagens": mensagens
        }

    # --- Turno do inimigo ---
    acao_inimigo = random.choice(["ataque","especial","pocao"])
    if acao_inimigo == "ataque":
        dano = inimigo.atacar(jogador)
        mensagens.append(f"{inimigo.nome} atacou você causando {dano} de dano")
    elif acao_inimigo == "especial":
        dano = inimigo.ataque_especial(jogador)
        mensagens.append(f"{inimigo.nome} usou ataque especial causando {dano} de dano")
    else:
        cura = inimigo.usar_pocao()
        mensagens.append(f"{inimigo.nome} usou poção recuperando {cura} de vida" if cura>0 else f"{inimigo.nome} tentou usar poção, mas não tinha!")

    if not jogador.esta_vivo():
        mensagens.append("💀 Você foi derrotado!")

    return {
        "jogador": personagem_para_dict(jogador),
        "inimigo": personagem_para_dict(inimigo),
        "mensagens": mensagens
    }


@app.post("/reiniciar")
def reiniciar():
    """Endpoint para reiniciar a batalha."""
    reiniciar_batalha()
    return {
        "detail": "Batalha reiniciada",
        "jogador": personagem_para_dict(estado_batalha["jogador"]),
        "inimigo": personagem_para_dict(estado_batalha["inimigo"]),
        "mensagens": estado_batalha["mensagens"]
    }

