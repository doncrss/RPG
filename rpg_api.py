from fastapi import FastAPI, HTTPException, Body
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
        self.classe = 'Base'
        self.arma = 'punho'

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
        # Guerreiro: mais vida e defesa, dano consistente
        super().__init__(nome, 130, 24, 16)
        self.classe = 'Guerreiro'
        self.arma = 'espada'
    def ataque_especial(self, outro):
        # Golpe forte com variação pequena
        dano_base = int(self.ataque * 1.8)
        dano = max(0, dano_base - outro.defesa + random.randint(-2, 2))
        outro.vida -= dano
        return dano

class Mago(Personagem):
    def __init__(self, nome):
        # Mago: mais fraco que antes por balanceamento
        super().__init__(nome, 90, 26, 6)
        self.classe = 'Mago'
        self.arma = 'cajado'
        # magos podem ter mais poções quando são inimigos (ajustado ao reiniciar)

    def magia(self, outro):
        # magia simples: dano moderado com pouca variância
        dano_base = int(self.ataque * 1.1)
        dano = max(0, dano_base - outro.defesa + random.randint(-1, 3))
        outro.vida -= dano
        return dano

    def feitico(self, outro):
        # feitiço poderoso: alto dano com grande variância
        dano_base = int(self.ataque * 2.0)
        dano = max(0, dano_base - outro.defesa + random.randint(-8, 8))
        outro.vida -= dano
        return dano
    def ataque_especial(self, outro):
        # Bola de fogo com maior variância
        dano_base = int(self.ataque * 1.8)
        dano = max(0, dano_base - outro.defesa + random.randint(-6, 6))
        outro.vida -= dano
        return dano

class Arqueiro(Personagem):
    def __init__(self, nome):
        # Arqueiro: ataque à distância com mobilidade, equilíbrio entre ataque/defesa
        super().__init__(nome, 100, 26, 12)
        self.classe = 'Arqueiro'
        self.arma = 'arco'
    def ataque_especial(self, outro):
        dano_base = int(self.ataque * 1.9)
        dano = max(0, dano_base - outro.defesa + random.randint(-3, 3))
        outro.vida -= dano
        return dano

# --- Função para enviar personagens como dict ---
def personagem_para_dict(p):
    return {
        "nome": p.nome,
        "vida": p.vida,
        "vida_max": p.vida_max,
        "pocoes": p.pocoes,
        "classe": getattr(p, 'classe', 'Base'),
        "arma": getattr(p, 'arma', 'punho')
    }

# --- Estado da batalha ---
estado_batalha = {
    "jogador": None,
    "inimigo": None,
    "mensagens": [],
    "arcade_score": 0
}

# Classe selecionada pelo jogador (padrão)
selected_classe = 'Guerreiro'

# o estado será inicializado chamando `reiniciar_batalha()` após sua definição


def reiniciar_batalha():
    """Reinicia o estado da batalha para novos personagens e limpa mensagens."""
    # Cria jogador de acordo com a classe selecionada
    global selected_classe
    cls = selected_classe.lower() if selected_classe else 'guerreiro'
    if cls == 'mago':
        jogador = Mago("Herói")
    elif cls == 'arqueiro':
        jogador = Arqueiro("Herói")
    else:
        jogador = Guerreiro("Herói")

    inimigo = random.choice([Guerreiro("Orc"), Mago("Bruxo"), Arqueiro("Ladino")])
    # Se o inimigo for um Mago (Bruxo), ele começa com 2 poções
    if isinstance(inimigo, Mago):
        inimigo.pocoes = 2

    estado_batalha["jogador"] = jogador
    estado_batalha["inimigo"] = inimigo
    estado_batalha["mensagens"] = []


@app.post("/selecionar_classe/{classe}")
def selecionar_classe(classe: str):
    """Define a classe do jogador e reinicia a batalha."""
    global selected_classe
    cls = classe.strip().lower()
    if cls not in ['guerreiro','mago','arqueiro']:
        raise HTTPException(status_code=400, detail="Classe inválida. Use 'Guerreiro', 'Mago' ou 'Arqueiro'.")
    # normaliza o valor
    selected_classe = 'Guerreiro' if cls=='guerreiro' else ('Mago' if cls=='mago' else 'Arqueiro')
    reiniciar_batalha()
    return {
        "detail": f"Classe selecionada: {selected_classe}",
        "jogador": personagem_para_dict(estado_batalha["jogador"]),
        "inimigo": personagem_para_dict(estado_batalha["inimigo"]),
        "mensagens": estado_batalha["mensagens"],
        "arcade_score": estado_batalha.get("arcade_score", 0)
    }

# chama reiniciar uma vez para inicializar estado
reiniciar_batalha()

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
        "mensagens": estado_batalha["mensagens"],
        "arcade_score": estado_batalha.get("arcade_score", 0)
    }

@app.post("/acao/{acao}")
def realizar_acao(acao: str, payload: dict = Body(None)):
    jogador = estado_batalha["jogador"]
    inimigo = estado_batalha["inimigo"]
    mensagens = estado_batalha["mensagens"]

    opc = None
    if payload and isinstance(payload, dict):
        opc = payload.get('opcao')

    if not jogador.esta_vivo() or not inimigo.esta_vivo():
        raise HTTPException(status_code=400, detail="A batalha acabou! Reinicie a aplicação para jogar novamente.")

    # --- Turno do jogador ---
    if acao == "ataque":
        dano = jogador.atacar(inimigo)
        mensagens.append(f"Você atacou {inimigo.nome} causando {dano} de dano")
    elif acao == "especial":
        # usa ataque especial quando disponível
        if hasattr(jogador, 'ataque_especial'):
            dano = jogador.ataque_especial(inimigo)
            mensagens.append(f"Você usou ataque especial causando {dano} de dano")
        else:
            dano = jogador.atacar(inimigo)
            mensagens.append(f"Você atacou (especial fallback) {inimigo.nome} causando {dano} de dano")
    elif acao == "pocao":
        cura = jogador.usar_pocao()
        mensagens.append(f"Você usou uma poção e recuperou {cura} de vida" if cura>0 else "Você não tem poções!")
    elif acao == "magia":
        # magia com variantes enviadas via payload.opcao
        escolha = (opc or '').lower()
        if escolha in ['curar','heal']:
            cura = min(jogador.vida_max - jogador.vida, 25)
            jogador.vida += cura
            mensagens.append(f"Você usou {escolha} e recuperou {cura} de vida")
        elif hasattr(jogador, 'magia'):
            # variantes possíveis: 'raio' -> magia(), 'bola' -> ataque_especial(), 'feitico' -> feitico()
            if escolha in ['raio','raio_de_energia','raio_de_gelo','raio']:
                dano = jogador.magia(inimigo)
                mensagens.append(f"Você lançou {escolha} causando {dano} de dano")
            elif escolha in ['bola','bola_de_fogo','explosao'] and hasattr(jogador, 'ataque_especial'):
                dano = jogador.ataque_especial(inimigo)
                mensagens.append(f"Você lançou {escolha} causando {dano} de dano")
            elif escolha in ['feitico','poderoso','power'] and hasattr(jogador, 'feitico'):
                dano = jogador.feitico(inimigo)
                mensagens.append(f"Você conjurou {escolha} causando {dano} de dano")
            else:
                # fallback simples
                dano = jogador.magia(inimigo)
                mensagens.append(f"Você lançou magia causando {dano} de dano")
        else:
            dano = max(0, int(jogador.ataque*1.1) - inimigo.defesa)
            inimigo.vida -= dano
            mensagens.append(f"Você usou magia improvisada causando {dano} de dano")
    else:
        raise HTTPException(status_code=400, detail="Ação inválida. Use 'ataque', 'especial', 'pocao' ou 'magia'.")

    # --- Checa se inimigo morreu ---
    if not inimigo.esta_vivo():
        mensagens.append(f"🎉 Você venceu {inimigo.nome}!")
        # incrementa contador arcade quando vence inimigo
        estado_batalha['arcade_score'] = estado_batalha.get('arcade_score', 0) + 1
        # cria um novo inimigo mantendo o jogador atual (avança para próximo inimigo automaticamente)
        novo_inimigo = random.choice([Guerreiro("Orc"), Mago("Bruxo"), Arqueiro("Ladino")])
        if isinstance(novo_inimigo, Mago):
            novo_inimigo.pocoes = 2
        estado_batalha['inimigo'] = novo_inimigo
        mensagens.append(f"⚔️ Um novo inimigo apareceu: {novo_inimigo.nome} ({novo_inimigo.classe})")
        return {
            "jogador": personagem_para_dict(jogador),
            "inimigo": personagem_para_dict(novo_inimigo),
            "mensagens": mensagens,
            "arcade_score": estado_batalha.get('arcade_score', 0)
        }

    # --- Turno do inimigo ---
    # Magos inimigos têm um leque maior de ações
    if isinstance(inimigo, Mago):
        acao_inimigo = random.choice(["ataque", "magia", "pocao"])
    else:
        acao_inimigo = random.choice(["ataque","especial","pocao"])

    if acao_inimigo == "ataque":
        dano = inimigo.atacar(jogador)
        mensagens.append(f"{inimigo.nome} atacou você causando {dano} de dano")
    elif acao_inimigo == "especial":
        dano = inimigo.ataque_especial(jogador)
        mensagens.append(f"{inimigo.nome} usou ataque especial causando {dano} de dano")
    elif acao_inimigo == "magia":
        if hasattr(inimigo, 'magia'):
            dano = inimigo.magia(jogador)
            mensagens.append(f"{inimigo.nome} lançou magia causando {dano} de dano")
        else:
            dano = inimigo.atacar(jogador)
            mensagens.append(f"{inimigo.nome} atacou você causando {dano} de dano")
    # 'feitico' não é uma ação exposta; magia cobre variantes
    else:
        cura = inimigo.usar_pocao()
        mensagens.append(f"{inimigo.nome} usou poção recuperando {cura} de vida" if cura>0 else f"{inimigo.nome} tentou usar poção, mas não tinha!")

    if not jogador.esta_vivo():
        mensagens.append("💀 Você foi derrotado!")
        # reset arcade score quando o jogador perde
        estado_batalha['arcade_score'] = 0

    return {
        "jogador": personagem_para_dict(jogador),
        "inimigo": personagem_para_dict(inimigo),
        "mensagens": mensagens,
        "arcade_score": estado_batalha.get('arcade_score', 0)
    }



@app.post("/reiniciar")
def reiniciar():
    """Endpoint para reiniciar a batalha."""
    reiniciar_batalha()
    return {
        "detail": "Batalha reiniciada",
        "jogador": personagem_para_dict(estado_batalha["jogador"]),
        "inimigo": personagem_para_dict(estado_batalha["inimigo"]),
        "mensagens": estado_batalha["mensagens"],
        "arcade_score": estado_batalha.get("arcade_score", 0)
    }

