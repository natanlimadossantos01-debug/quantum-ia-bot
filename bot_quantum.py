#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   ⚛️  Q U A N T U M   I A   D U A L      ║
║   🧠 M1 + M5 | Salas Independentes        ║
║   ⏱️ 5min entre sinais | ☁️ Cloud Ready    ║
║   📊 Super 5/3 + Last of Five no M5       ║
╚══════════════════════════════════════════════╝
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os, random
from datetime import datetime, timedelta, timezone
from collections import deque
from pathlib import Path

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

FUSO_BR = timezone(timedelta(hours=-3))

FILOSOFIA_SAMURAI = [
    "⚔️ A vitória começa na execução perfeita, não no resultado.",
    "🎯 O objetivo é o trade certo, não o dinheiro.",
    "🧘 Aceite a perda como parte do caminho do guerreiro.",
    "🐉 O mercado é um oponente vivo. Respeite-o.",
    "🕯️ Cada vela é uma batalha. Cada dia, uma guerra.",
    "⏳ Paciência é arma. Espere a confirmação.",
    "🌊 A tendência é sua amiga. Não a desafie.",
    "🛡️ O stop é o escudo do samurai. Use-o com honra.",
    "📚 O verdadeiro guerreiro estuda seus erros.",
    "🧠 Mente vazia, espírito pronto. Sem emoção.",
    "🔥 Paixão pelo processo, não pelo resultado.",
    "⛩️ Disciplina é o alicerce do trader samurai.",
    "⚡ O momento da execução é tudo. Hesitação é derrota.",
    "🏔️ A montanha do lucro se conquista com paciência.",
    "🌅 Cada amanhecer traz uma nova oportunidade de batalha."
]

def get_filosofia():
    return random.choice(FILOSOFIA_SAMURAI)

class C:
    G='\033[92m';Y='\033[93m';R='\033[91m';C='\033[96m';W='\033[97m';B='\033[1m';E='\033[0m';GOLD='\033[38;5;220m'

def clear(): os.system('clear 2>/dev/null || cls 2>/dev/null')

CONFIG_FILE="config_quantum_dual.json"

def carregar_config():
    token1 = os.environ.get('TELEGRAM_TOKEN_M1')
    chat1 = os.environ.get('TELEGRAM_CHAT_ID_M1')
    token2 = os.environ.get('TELEGRAM_TOKEN_M5')
    chat2 = os.environ.get('TELEGRAM_CHAT_ID_M5')
    email = os.environ.get('IQ_EMAIL')
    senha = os.environ.get('IQ_SENHA')
    
    if token1 and chat1 and token2 and chat2 and email and senha:
        print(f"{C.G}✅ Modo CLOUD dual detectado!{C.E}")
        return {
            "m1": {"token": token1, "chat": chat1},
            "m5": {"token": token2, "chat": chat2},
            "email": email, "senha": senha
        }
    
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE) as f: cfg = json.load(f)
        print(f"{C.G}✅ Config carregada!{C.E}")
        return cfg
    
    print(f"{C.Y}⚙️ Configure as salas:{C.E}")
    cfg = {
        "m1": {
            "token": input("Token M1: ").strip(),
            "chat": input("Chat ID M1: ").strip()
        },
        "m5": {
            "token": input("Token M5: ").strip(),
            "chat": input("Chat ID M5: ").strip()
        },
        "email": input("Email IQ: ").strip(),
        "senha": input("Senha IQ: ").strip()
    }
    with open(CONFIG_FILE, 'w') as f: json.dump(cfg, f, indent=2)
    return cfg

cfg = carregar_config()
EMAIL = cfg['email']
SENHA = cfg['senha']

from iqoptionapi.stable_api import IQ_Option

ATIVOS_OTC = {
    "EURUSD": "EURUSD-OTC",
    "GBPUSD": "GBPUSD-OTC",
    "EURGBP": "EURGBP-OTC",
    "EURJPY": "EURJPY-OTC"
}

# --------------------- CLASSES GERAIS ---------------------
class Telegram:
    def __init__(self, token, chat):
        self.url = f"https://api.telegram.org/bot{token}"
        self.chat = chat
    def send(self, txt):
        try:
            requests.post(f"{self.url}/sendMessage",
                         json={"chat_id": self.chat, "text": txt, "parse_mode": "Markdown"}, timeout=5)
        except: pass

class Placar:
    def __init__(self):
        self.w = 0; self.l = 0; self.g1 = 0
        self.s = deque(maxlen=20); self.ops = []
    def win(self, g=0):
        if g == 0: self.w += 1; self.s.append('🟢'); return "✅ WIN"
        else: self.g1 += 1; self.s.append('🟡'); return "✅ WIN GALE 1"
    def loss(self): self.l += 1; self.s.append('🔴'); return "❌ LOSS"
    def registrar(self, ativo, direcao, conf, resultado, is_gale=False):
        agora = datetime.now(FUSO_BR); hora = agora.strftime('%H:%M')
        sufixo = "¹" if is_gale else ""; emoji = "✅️" if "WIN" in resultado else "🔴"
        self.ops.append(f"M1 {ativo}-OTC {direcao} {hora} {emoji}{sufixo}")
    def zerar(self):
        self.w = 0; self.l = 0; self.g1 = 0
        self.s.clear(); self.ops.clear()

class IQAPI:
    def __init__(self, email, senha, ativos):
        self.email = email; self.senha = senha; self.ativos = ativos
        self.api = None
        self.velas = {nome: deque(maxlen=100) for nome in ativos}
        self.ok = False
    def conectar(self):
        for t in range(5):
            try:
                if self.api:
                    try: self.api.close()
                    except: pass
                    time.sleep(2)
                self.api = IQ_Option(self.email, self.senha)
                ok, _ = self.api.connect()
                if ok: self.ok = True; return True
                time.sleep(5*(t+1))
            except: time.sleep(5*(t+1))
        self.ok = False; return False
    def obter_velas(self, ativo_id, timeframe, qtd=80):
        for retry in range(3):
            if not self.ok and not self.conectar(): return 0
            try:
                c = self.api.get_candles(ativo_id, timeframe, qtd, time.time())
                if c and len(c) > 0:
                    nome = [k for k, v in self.ativos.items() if v == ativo_id][0]
                    self.velas[nome].clear()
                    for x in c[-qtd:]:
                        if isinstance(x, dict):
                            try:
                                self.velas[nome].append({
                                    'time': datetime.fromtimestamp(x.get('from', 0), FUSO_BR),
                                    'open': float(x['open']), 'high': float(x['max']),
                                    'low': float(x['min']), 'close': float(x['close']),
                                    'volume': int(x.get('volume', 0))
                                })
                            except: pass
                    return len(c)
            except:
                self.ok = False
                if retry < 2: time.sleep(3); continue
        return 0
    def atualizar(self, timeframe):
        if not self.ok: self.conectar()
        for nome, ativo_id in self.ativos.items():
            try: self.obter_velas(ativo_id, timeframe)
            except: pass

# ---------- ESTRATÉGIAS M1 (ORIGINAIS) ----------
class FundoTopo:
    def analisar(self, v):
        try:
            if len(v) < 15: return None, 0
            precos = [x['close'] for x in v]
            max_10 = max(precos[-10:]); min_10 = min(precos[-10:]); atual = precos[-1]
            if min_10 > 0 and (atual - min_10) / min_10 < 0.0003: return 'CALL', 82
            if atual > 0 and (max_10 - atual) / atual < 0.0003: return 'PUT', 82
            return None, 0
        except: return None, 0

class Estrategia520:
    def analisar(self, v):
        try:
            if len(v) < 25: return None, 0
            precos = [x['close'] for x in v]
            mm5 = np.mean(precos[-5:])
            media20 = np.mean(precos[-20:]); std20 = np.std(precos[-20:])
            bs = media20 + 2*std20; bi = media20 - 2*std20; atual = precos[-1]
            if atual > mm5 and atual <= bi*1.002: return 'CALL', 78
            if atual < mm5 and atual >= bs*0.998: return 'PUT', 78
            return None, 0
        except: return None, 0

class Rejeicao:
    def analisar(self, v):
        try:
            if len(v) < 3: return None, 0
            vela = v[-1]; corpo = abs(vela['close'] - vela['open'])
            if corpo == 0: return None, 0
            pavio_sup = vela['high'] - max(vela['close'], vela['open'])
            pavio_inf = min(vela['close'], vela['open']) - vela['low']
            if pavio_inf > corpo * 3: return 'CALL', 85
            if pavio_sup > corpo * 3: return 'PUT', 85
            return None, 0
        except: return None, 0

class MHI1_Adaptada:
    def analisar(self, v):
        try:
            if len(v) < 8: return None, 0
            velas_ant = v[-6:-3]
            ups = sum(1 for x in velas_ant if x['close'] > x['open'])
            downs = 3 - ups
            if 0 < ups < downs: return 'CALL', 72
            if 0 < downs < ups: return 'PUT', 72
            return None, 0
        except: return None, 0

class Rompimento:
    def analisar(self, v):
        try:
            if len(v) < 5: return None, 0
            precos = [x['close'] for x in v]; highs = [x['high'] for x in v]; lows = [x['low'] for x in v]
            max_3 = max(highs[-4:-1]); min_3 = min(lows[-4:-1])
            if precos[-1] > max_3: return 'CALL', 75
            if precos[-1] < min_3: return 'PUT', 75
            return None, 0
        except: return None, 0

# ---------- ESTRATÉGIAS M5 (SUPER 5, SUPER 3, LAST OF FIVE) ----------
class Super5:
    """SUPER 5 - M5 (Maioria/Minoria)"""
    def __init__(self, modo='minoria'):
        self.modo = modo
        self.tamanho_quadrante = 6
        self.velas_analise = 3
        
    def analisar(self, v):
        try:
            if len(v) < self.tamanho_quadrante * 2:
                return None, 0
            ultimas_velas = list(v[-self.tamanho_quadrante*2:])
            quadrante_anterior = ultimas_velas[-self.tamanho_quadrante:]
            velas_analise = quadrante_anterior[-self.velas_analise:]
            calls = sum(1 for x in velas_analise if x['close'] > x['open'])
            puts = self.velas_analise - calls
            if self.modo == 'minoria':
                alvo = 'CALL' if calls < puts else 'PUT'
            else:
                alvo = 'CALL' if calls > puts else 'PUT'
            diff = abs(calls - puts)
            conf = 50 + diff * 10
            conf = min(conf, 85)
            return alvo, conf
        except:
            return None, 0

class Super3:
    """SUPER 3 - M5 (Maioria/Minoria)"""
    def __init__(self, modo='minoria'):
        self.modo = modo
        self.tamanho_quadrante = 3
        
    def analisar(self, v):
        try:
            if len(v) < self.tamanho_quadrante * 2:
                return None, 0
            ultimas_velas = list(v[-self.tamanho_quadrante*2:])
            quadrante_anterior = ultimas_velas[-self.tamanho_quadrante:]
            calls = sum(1 for x in quadrante_anterior if x['close'] > x['open'])
            puts = self.tamanho_quadrante - calls
            if self.modo == 'minoria':
                alvo = 'CALL' if calls < puts else 'PUT'
            else:
                alvo = 'CALL' if calls > puts else 'PUT'
            diff = abs(calls - puts)
            conf = 50 + diff * 15
            conf = min(conf, 85)
            return alvo, conf
        except:
            return None, 0

class LastOfFive:
    """LAST OF FIVE - M5 (Maioria/Minoria)"""
    def __init__(self, modo='minoria'):
        self.modo = modo
        self.tamanho_quadrante = 6
        self.velas_analise = 5
        
    def analisar(self, v):
        try:
            if len(v) < self.tamanho_quadrante * 2:
                return None, 0
            ultimas_velas = list(v[-self.tamanho_quadrante*2:])
            quadrante_anterior = ultimas_velas[-self.tamanho_quadrante:]
            velas_analise = quadrante_anterior[-self.velas_analise:]
            calls = sum(1 for x in velas_analise if x['close'] > x['open'])
            puts = self.velas_analise - calls
            if self.modo == 'minoria':
                alvo = 'CALL' if calls < puts else 'PUT'
            else:
                alvo = 'CALL' if calls > puts else 'PUT'
            diff = abs(calls - puts)
            conf = 50 + diff * 8
            conf = min(conf, 85)
            return alvo, conf
        except:
            return None, 0

# Listas de estratégias
ESTRATEGIAS_M1 = [
    ('🔥 Fundo/Topo', FundoTopo()),
    ('🔬 5-2-0', Estrategia520()),
    ('🕯️ Rejeição', Rejeicao()),
    ('📊 MHI 1', MHI1_Adaptada()),
    ('💥 Rompimento', Rompimento()),
]

ESTRATEGIAS_M5 = [
    ('📊 Super 5 Minoria', Super5(modo='minoria')),
    ('📊 Super 5 Maioria', Super5(modo='maioria')),
    ('📊 Super 3 Minoria', Super3(modo='minoria')),
    ('📊 Super 3 Maioria', Super3(modo='maioria')),
    ('📊 Last of Five Minoria', LastOfFive(modo='minoria')),
    ('📊 Last of Five Maioria', LastOfFive(modo='maioria')),
]

# --------------------- BOT CONFIGURÁVEL ---------------------
class QuantumBot:
    def __init__(self, nome, timeframe, estrategias, token, chat, intervalo=300):
        self.nome = nome
        self.timeframe = timeframe          # em segundos (60 para M1, 300 para M5)
        self.estrategias = estrategias
        self.tg = Telegram(token, chat)
        self.placar = Placar()
        self.iq = None
        self.catalogador = CatalogadorInteligente()
        self.filtro_tendencia = FiltroTendencia()
        self.sinais_bloqueados_pavio = 0
        self.sinais_bloqueados_tendencia = 0
        self.op = False
        self.ult = 0
        self.sinais_enviados = 0
        self.intervalo = intervalo
        self.professor = TraderProfessor()

    def _pavio_ok(self, velas, direcao):
        if len(velas) < 2: return True
        va, vb = velas[-1], velas[-2]
        corpo_va = abs(va['close'] - va['open'])
        if corpo_va == 0: return False
        if direcao == 'CALL':
            if va['high'] - max(va['close'], va['open']) > corpo_va * 0.4: return False
        else:
            if min(va['close'], va['open']) - va['low'] > corpo_va * 0.4: return False
        corpo_vb = abs(vb['close'] - vb['open'])
        if corpo_vb > 0:
            if direcao == 'CALL':
                if vb['high'] - max(vb['close'], vb['open']) > corpo_vb * 0.5: return False
            else:
                if min(vb['close'], vb['open']) - vb['low'] > corpo_vb * 0.5: return False
        range_total = va['high'] - va['low']
        if range_total > 0 and corpo_va < range_total * 0.3: return False
        return True

    def _tendencia_ok(self, velas, direcao, par):
        tendencia, forca = self.filtro_tendencia.analisar_tendencia(velas)
        alinhado = self.filtro_tendencia.sinal_alinhado(direcao, tendencia, forca)
        if not alinhado:
            print(f"  🚫 {self.nome} Bloqueado: {direcao} {par} | {tendencia} ({forca:.0f}%)")
        return alinhado

    def obter_sinal(self):
        for nome_par, velas in self.iq.velas.items():
            if len(velas) < 30: continue
            tendencia, forca = self.filtro_tendencia.analisar_tendencia(velas)
            for nome_est, est in self.estrategias:
                try:
                    d, c = est.analisar(velas)
                    if d and c >= 65 and self._pavio_ok(velas, d) and self.filtro_tendencia.sinal_alinhado(d, tendencia, forca):
                        return {'ativo': nome_par, 'direcao': d, 'confianca': c, 'estrategia': nome_est, 'tendencia': tendencia}
                except: pass
        return None

    async def run(self, iq_api):
        self.iq = iq_api
        print(f"\n  ⚛️ {self.nome} iniciando (TF={self.timeframe}s)...")
        while True:
            try:
                agora = datetime.now(FUSO_BR)
                if agora.second in (0, 30):
                    self.iq.atualizar(self.timeframe)
                    self.professor.atualizar_dados(self.iq.velas)
                if not self.op:
                    sinal = self.obter_sinal()
                    if sinal and time.time() - self.ult > self.intervalo:
                        self.op = True
                        self.sinais_enviados += 1
                        minutos_offset = self.timeframe // 60
                        next_minute = ((agora.minute // minutos_offset) + 1) * minutos_offset
                        entrada = agora.replace(minute=next_minute % 60, second=0, microsecond=0)
                        if entrada <= agora:
                            entrada += timedelta(minutes=minutos_offset)
                        he = entrada.strftime('%H:%M')
                        print(f"\n⚛️ {self.nome} #{self.sinais_enviados} {sinal['ativo']}-OTC {sinal['direcao']} | {sinal['confianca']:.0f}% | 🧠 {sinal['estrategia']} | ⏰ {he}")
                        self.tg.send(self._fmt_sinal(sinal, he))
                        self.ult = time.time()
                        asyncio.create_task(self._corrigir(sinal))
                if agora.second in (0, 30):
                    w, l, g1 = self.placar.w, self.placar.l, self.placar.g1
                    total_profit = w + g1
                    total_trades = total_profit + l
                    tx = round((total_profit / total_trades) * 100, 1) if total_trades > 0 else 0
                    print(f"{C.GOLD}│{C.E} {self.nome} ⏰ {agora.strftime('%H:%M:%S')} | 📨{self.sinais_enviados} | 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}%")
                await asyncio.sleep(3)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"  {C.R}❌ {self.nome} erro: {str(e)[:40]}{C.E}")
                self.iq.ok = False
                await asyncio.sleep(5)

    def _fmt_sinal(self, s, hora):
        e = "🟢" if s['direcao'] == 'CALL' else "🔴"
        return f"""⚛️ SINAL {self.nome} ⚛️

⏰ Horário: {hora}
💰 Ativo: {s['ativo']}-OTC
📈 Direção: {s['direcao']} {e}
⌛️ Expiração: {self.timeframe//60} min
📊 Confiança: {s['confianca']:.0f}%
🧠 Estratégia: {s['estrategia']}
📐 Tendência: {s.get('tendencia', 'NEUTRA')}

⚠️ Entrar somente no horário marcado.
🔄 1 recuperação (Gale 1)!"""

    async def _corrigir(self, sinal):
        at = sinal['ativo']; d = sinal['direcao']; conf = sinal.get('confianca', 0)
        try:
            agora = datetime.now(FUSO_BR)
            minutos_offset = self.timeframe // 60
            next_candle = agora.replace(second=0, microsecond=0)
            while next_candle.minute % minutos_offset != 0:
                next_candle += timedelta(minutes=1)
            if next_candle <= agora:
                next_candle += timedelta(minutes=minutos_offset)
            espera = (next_candle - agora).total_seconds()
            await asyncio.sleep(espera + 10)
            self.iq.atualizar(self.timeframe)
            v = self.iq.velas[at]
            if len(v) < 2: self.op = False; return
            pc = v[-1]['open']
            print(f"  ⚛️ {self.nome} {at}-OTC {d} | OPEN:{pc:.5f}")
            await asyncio.sleep(self.timeframe * 0.8)
            self.iq.atualizar(self.timeframe)
            v = self.iq.velas[at]
            if len(v) > 0 and ((d == 'CALL' and v[-1]['high'] > pc) or (d == 'PUT' and v[-1]['low'] < pc)):
                r = self.placar.win(0)
                print(f"  ✅ {r}")
                self.tg.send(f"{r}\n{at}-OTC {d} | Placar: 🟢{self.placar.w}W 🟡{self.placar.g1}G1 🔴{self.placar.l}L")
                self.placar.registrar(at, d, conf, "WIN")
                self.op = False; return
            print(f"  🔄 GALE 1")
            await asyncio.sleep(self.timeframe * 0.8)
            self.iq.atualizar(self.timeframe)
            v = self.iq.velas[at]
            if len(v) > 0:
                pg = v[-1]['open']
                print(f"  GALE | OPEN:{pg:.5f}")
                await asyncio.sleep(self.timeframe * 0.8)
                self.iq.atualizar(self.timeframe)
                v = self.iq.velas[at]
                if len(v) > 0 and ((d == 'CALL' and v[-1]['high'] > pg) or (d == 'PUT' and v[-1]['low'] < pg)):
                    r = self.placar.win(1)
                    print(f"  ✅ {r}")
                    self.tg.send(f"{r}\n{at}-OTC {d} | Placar: 🟢{self.placar.w}W 🟡{self.placar.g1}G1 🔴{self.placar.l}L")
                    self.placar.registrar(at, d, conf, "WIN GALE 1", is_gale=True)
                    self.op = False; return
            r = self.placar.loss()
            print(f"  🔴 {r}")
            self.tg.send(f"{r}\n{at}-OTC {d} | Placar: 🟢{self.placar.w}W 🟡{self.placar.g1}G1 🔴{self.placar.l}L")
            self.placar.registrar(at, d, conf, "LOSS")
            self.op = False
        except Exception as e:
            print(f"  ❌ {e}"); self.op = False

async def main():
    clear()
    print(f"{C.GOLD}{C.B}╔══════════════════════════════╗")
    print(f"║  ⚛️ QUANTUM IA DUAL       ║")
    print(f"║  M1 + M5 | Salas Separadas ║")
    print(f"╚══════════════════════════════╝{C.E}")
    
    iq = IQAPI(EMAIL, SENHA, ATIVOS_OTC)
    if not iq.conectar():
        print(f"{C.R}❌ Falha conexão IQ!{C.E}")
        return
    
    bot_m1 = QuantumBot(
        nome="M1", timeframe=60, estrategias=ESTRATEGIAS_M1,
        token=cfg['m1']['token'], chat=cfg['m1']['chat'], intervalo=300
    )
    bot_m5 = QuantumBot(
        nome="M5", timeframe=300, estrategias=ESTRATEGIAS_M5,
        token=cfg['m5']['token'], chat=cfg['m5']['chat'], intervalo=600
    )
    
    await asyncio.gather(
        bot_m1.run(iq),
        bot_m5.run(iq)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.G}👋 Quantum IA Dual encerrado.{C.E}")
