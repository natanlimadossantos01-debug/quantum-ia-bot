#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   ⚛️  Q U A N T U M   I A   M 1           ║
║   🔄 Gale 1 | 🧠 Cérebro Visual + Trader   ║
║   🕯️ Pavio | 📈 Tendência | 👁️ Visão      ║
║   🌊 Fluxo ALINHADO (NEUTRO BLOQUEADO)     ║
║   📊 Placar Diário Automático | ☁️ Cloud   ║
╚══════════════════════════════════════════════╝
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os
from datetime import datetime, timedelta
from collections import deque
from pathlib import Path

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

class C:
    G='\033[92m';Y='\033[93m';R='\033[91m';C='\033[96m';W='\033[97m';B='\033[1m';E='\033[0m';GOLD='\033[38;5;220m'

def clear(): os.system('clear 2>/dev/null || cls 2>/dev/null')

def banner():
    clear()
    print(f"{C.GOLD}{C.B}╔══════════════════════════════════════════════╗")
    print(f"║   ⚛️  Q U A N T U M   I A   M 1           ║")
    print(f"║   🔄 Gale 1 | 🧠 Cérebro Visual + Trader  ║")
    print(f"║   👁️ Visão | 🌊 Fluxo ALINHADO | ☁️ Cloud ║")
    print(f"╚══════════════════════════════════════════════╝{C.E}")

CONFIG_FILE = "config_quantum.json"

def carregar_config():
    """☁️ Cloud: variáveis de ambiente | 💻 Local: arquivo JSON"""
    
    # ═══════════════════════════════════════
    # ☁️ MODO CLOUD: Variáveis de Ambiente
    # ═══════════════════════════════════════
    cloud_token = os.environ.get('TELEGRAM_TOKEN')
    cloud_chat = os.environ.get('TELEGRAM_CHAT_ID')
    cloud_email = os.environ.get('IQ_EMAIL')
    cloud_senha = os.environ.get('IQ_SENHA')
    
    if cloud_token and cloud_chat and cloud_email and cloud_senha:
        banner()
        print(f"\n{C.G}✅ Modo CLOUD detectado!{C.E}")
        print(f"  ☁️ Usando variáveis de ambiente\n")
        return {
            "token": cloud_token,
            "chat": cloud_chat,
            "email": cloud_email,
            "senha": cloud_senha
        }
    
    # ═══════════════════════════════════════
    # 💻 MODO LOCAL: Arquivo JSON
    # ═══════════════════════════════════════
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        if 'token' not in cfg:
            Path(CONFIG_FILE).unlink()
            return carregar_config()
        banner()
        print(f"\n{C.G}✅ Config carregada do arquivo!{C.E}\n")
        return cfg
    
    # ═══════════════════════════════════════
    # 🆕 PRIMEIRA VEZ: Input manual
    # ═══════════════════════════════════════
    banner()
    try:
        cfg = {
            "token": input(f"{C.G}Token Telegram: {C.E}").strip(),
            "chat": input(f"{C.G}Chat ID: {C.E}").strip(),
            "email": input(f"\n{C.G}Email IQ: {C.E}").strip(),
            "senha": input(f"{C.G}Senha IQ: {C.E}").strip()
        }
    except (EOFError, KeyboardInterrupt):
        print(f"\n{C.R}❌ ERRO: Sem config e sem variáveis de ambiente!{C.E}")
        print(f"{C.Y}☁️ Configure as variáveis:{C.E}")
        print(f"  TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, IQ_EMAIL, IQ_SENHA")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)
    banner()
    print(f"\n{C.G}✅ Salvo!{C.E}\n")
    return cfg

cfg = carregar_config()
TOKEN = cfg['token']
CHAT = cfg['chat']
EMAIL = cfg['email']
SENHA = cfg['senha']

from iqoptionapi.stable_api import IQ_Option

ATIVOS_OTC = {"EURUSD": "EURUSD-OTC", "GBPUSD": "GBPUSD-OTC", "EURGBP": "EURGBP-OTC"}

# ═══════════════════════════════════════════
# PLACAR
# ═══════════════════════════════════════════
class Placar:
    def __init__(self): self.w = 0; self.l = 0; self.g1 = 0; self.s = deque(maxlen=20)
    def win(self, g=0):
        self.w += 1
        if g == 0: self.s.append('🟢'); return "✅ WIN"
        else: self.g1 += 1; self.s.append('🟡'); return "✅ WIN GALE 1"
    def loss(self): self.l += 1; self.s.append('🔴'); return "❌ LOSS"
    def zerar(self): self.w = 0; self.l = 0; self.g1 = 0; self.s.clear()

# ═══════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════
class Telegram:
    def __init__(self, t, c): self.u = f"https://api.telegram.org/bot{t}"; self.c = c
    def send(self, txt):
        try: requests.post(f"{self.u}/sendMessage", json={"chat_id": self.c, "text": txt, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# ═══════════════════════════════════════════
# 5 ESTRATÉGIAS (SIMPLIFICADAS E ROBUSTAS)
# ═══════════════════════════════════════════
class Mortalha:
    def sma(self, d, p):
        try:
            if len(d) >= p: return sum(d[-p:]) / p
            return sum(d) / len(d) if d else 0
        except: return 0
    def wma(self, d, p):
        try:
            if len(d) < p: return sum(d) / len(d) if d else 0
            w = np.arange(1, p+1); return np.sum(np.array(d[-p:]) * w) / np.sum(w)
        except: return 0
    def analisar(self, v):
        try:
            if len(v) < 30: return None, 0
            c = np.array([x['close'] for x in v]); b1 = np.zeros(len(c))
            for i in range(len(c)):
                if i >= 33: b1[i] = self.sma(c[:i+1], 1) - self.sma(c[:i+1], 34)
            b2 = np.zeros(len(b1))
            for i in range(len(b1)):
                if i >= 3: b2[i] = self.wma(b1[:i+1], 4)
            if b1[-1] > b2[-1] and b1[-2] <= b2[-2]: return 'CALL', min(45 + abs(b1[-1]-b2[-1]) * 10000, 90)
            if b1[-1] < b2[-1] and b1[-2] >= b2[-2]: return 'PUT', min(45 + abs(b1[-1]-b2[-1]) * 10000, 90)
            return None, 0
        except: return None, 0

class Formiga:
    def ema(self, p, pe):
        try:
            if len(p) < pe: return sum(p) / len(p) if p else 0
            return np.mean(p[-pe:])
        except: return 0
    def analisar(self, v):
        try:
            if len(v) < 12: return None, 0
            precos = np.array([x['close'] for x in v])
            ema5 = self.ema(precos, 5); ema10 = self.ema(precos, 10)
            dif = ((ema5 - ema10) / ema10) * 100 if ema10 > 0 else 0
            sc = 0; sp = 0
            if dif > 0.02: sc += 3
            elif dif > 0.005: sc += 1
            elif dif < -0.02: sp += 3
            elif dif < -0.005: sp += 1
            if sc >= 2 and sc > sp: return 'CALL', min(50 + sc * 4, 85)
            if sp >= 2 and sp > sc: return 'PUT', min(50 + sp * 4, 85)
            return None, 0
        except: return None, 0

class Fortaleza:
    def rsi(self, p, pe=7):
        try:
            if len(p) < pe+1: return 50
            d = np.diff(list(p[-pe-1:])); g = np.where(d > 0, d, 0); l = np.where(d < 0, -d, 0)
            mg = np.mean(g) if len(g) > 0 else 0; mp = np.mean(l) if len(l) > 0 else 0
            if mp == 0: return 100
            return 100 - (100 / (1 + mg/mp))
        except: return 50
    def analisar(self, v):
        try:
            if len(v) < 18: return None, 0
            precos = np.array([x['close'] for x in v])
            rsi_val = self.rsi(precos)
            m = np.mean(precos[-10:]) if len(precos) >= 10 else np.mean(precos)
            s = np.std(precos[-10:]) if len(precos) >= 10 else 0
            bs = m + 2*s; bi = m - 2*s
            sc = 0; sp = 0
            if rsi_val < 30: sc += 3
            elif rsi_val < 40: sc += 2
            if rsi_val > 70: sp += 3
            elif rsi_val > 60: sp += 2
            if precos[-1] <= bi * 1.0004: sc += 3
            if precos[-1] >= bs * 0.9996: sp += 3
            if sc >= 4 and sc > sp: return 'CALL', min(60 + sc * 3, 90)
            if sp >= 4 and sp > sc: return 'PUT', min(60 + sp * 3, 90)
            return None, 0
        except: return None, 0

class RaioNegro:
    def analisar(self, v):
        try:
            if len(v) < 12: return None, 0
            precos = np.array([x['close'] for x in v])
            ema5 = np.mean(precos[-5:]) if len(precos) >= 5 else precos[-1]
            ema13 = np.mean(precos[-13:]) if len(precos) >= 13 else ema5
            macd = ema5 - ema13; sinal = macd * 0.5
            mom = precos[-1] - precos[-3] if len(precos) >= 3 else 0
            sc = 0; sp = 0
            if macd > sinal and macd > 0: sc += 3
            elif macd > sinal: sc += 1
            elif macd < sinal and macd < 0: sp += 3
            elif macd < sinal: sp += 1
            if mom > 0.00003: sc += 3
            elif mom > 0: sc += 1
            elif mom < -0.00003: sp += 3
            elif mom < 0: sp += 1
            if sc >= 2 and sc > sp: return 'CALL', min(48 + sc * 4, 85)
            if sp >= 2 and sp > sc: return 'PUT', min(48 + sp * 4, 85)
            return None, 0
        except: return None, 0

class Tsunami:
    def analisar(self, v):
        try:
            if len(v) < 12: return None, 0
            precos = np.array([x['close'] for x in v])
            altas = sum(1 for i in range(-min(5, len(v)-1), 0) if precos[i] > precos[i-1])
            sc = 0; sp = 0
            if altas >= 3: sc += 3
            elif altas <= 2: sp += 3
            if sc >= 2 and sc > sp: return 'CALL', min(50 + sc * 3, 85)
            if sp >= 2 and sp > sc: return 'PUT', min(50 + sp * 3, 85)
            return None, 0
        except: return None, 0

# ═══════════════════════════════════════════
# QUANTUM IA
# ═══════════════════════════════════════════
class QuantumIA:
    def __init__(self):
        self.mortalha = Mortalha()
        self.formiga = Formiga()
        self.fortaleza = Fortaleza()
        self.raio_negro = RaioNegro()
        self.tsunami = Tsunami()
        self.min_estrategias = 2

    def analisar_completo(self, v):
        try:
            if len(v) < 30: return None, 0, 0
            resultados = []
            votos = {'CALL': 0, 'PUT': 0}
            confiancas = {'CALL': [], 'PUT': []}
            estrategias = [
                ('mortalha', self.mortalha), ('formiga', self.formiga),
                ('fortaleza', self.fortaleza), ('raio_negro', self.raio_negro),
                ('tsunami', self.tsunami)
            ]
            for nome, est in estrategias:
                try:
                    d, c = est.analisar(v)
                    if d:
                        resultados.append((nome, d, c))
                        votos[d] += 1
                        confiancas[d].append(c)
                except: pass
            total = len(resultados)
            if total < self.min_estrategias: return None, 0, total
            if votos['CALL'] >= self.min_estrategias and votos['CALL'] > votos['PUT']:
                conf = np.mean(confiancas['CALL'])
                return 'CALL', min(conf + (total-2)*3, 95), total
            if votos['PUT'] >= self.min_estrategias and votos['PUT'] > votos['CALL']:
                conf = np.mean(confiancas['PUT'])
                return 'PUT', min(conf + (total-2)*3, 95), total
            return None, 0, total
        except: return None, 0, 0

    def melhor_par(self, velas_dict, bloqueados, stats_pares):
        try:
            melhor = None; melhor_score = 0
            for nome, velas in velas_dict.items():
                if nome in bloqueados: continue
                if nome in stats_pares and stats_pares[nome]['total'] >= 5:
                    if stats_pares[nome]['taxa'] < 50: continue
                if len(velas) >= 30:
                    d, cf, num = self.analisar_completo(velas)
                    if d:
                        score = cf + (num * 5)
                        if nome in stats_pares and stats_pares[nome]['total'] >= 5:
                            score += stats_pares[nome]['taxa'] * 0.2
                        if score > melhor_score:
                            melhor_score = score
                            melhor = {'ativo': nome, 'direcao': d, 'confianca': cf, 'estrategias': num}
            return melhor
        except: return None

# ═══════════════════════════════════════════
# 🧠 CÉREBRO VISUAL + 🌊 FLUXO
# ═══════════════════════════════════════════
class CerebroVisual:
    def __init__(self):
        self.historico = deque(maxlen=50)
        self.score_minimo = 55
        self.max_pavio_ratio = 0.6
        self.stats_pares = {nome: {'wins': 0, 'losses': 0, 'total': 0, 'taxa': 0} for nome in ATIVOS_OTC}
        self.tendencias = {nome: "NEUTRA" for nome in ATIVOS_OTC}
        self.fluxo_atual = {nome: 'NEUTRO' for nome in ATIVOS_OTC}
        self.forca_fluxo = {nome: 0 for nome in ATIVOS_OTC}
        self.bloqueios_fluxo = 0
        self.bonus_fluxo = 0
        self.bloqueios_neutro = 0

    def atualizar_stats(self, ativo, resultado):
        if ativo in self.stats_pares:
            self.stats_pares[ativo]['total'] += 1
            if resultado == 'win': self.stats_pares[ativo]['wins'] += 1
            else: self.stats_pares[ativo]['losses'] += 1
            t = self.stats_pares[ativo]['total']
            w = self.stats_pares[ativo]['wins']
            self.stats_pares[ativo]['taxa'] = round((w/t)*100, 1) if t > 0 else 0

    def detectar_fluxo(self, velas):
        if len(velas) < 15: return 'NEUTRO', 0
        precos = [v['close'] for v in velas]
        mc = np.mean(precos[-5:]) if len(precos) >= 5 else precos[-1]
        ml = np.mean(precos[-15:]) if len(precos) >= 15 else mc
        dif = ((mc - ml) / ml) * 100 if ml > 0 else 0
        altas = sum(1 for i in range(-min(10, len(precos)-1), 0) if precos[i] > precos[i-1])
        baixas = 10 - altas if len(precos) >= 11 else 5 - altas
        forca = max(altas, baixas) / 10 if len(precos) >= 11 else 0.5
        if dif > 0.03 and altas >= 6: return 'CALL', forca
        if dif < -0.03 and baixas >= 6: return 'PUT', forca
        return 'NEUTRO', forca

    def atualizar_fluxos(self, velas_dict):
        for nome, velas in velas_dict.items():
            if len(velas) >= 15:
                self.fluxo_atual[nome], self.forca_fluxo[nome] = self.detectar_fluxo(velas)

    def atualizar_tendencias(self, velas_dict):
        for nome, velas in velas_dict.items():
            if len(velas) >= 21:
                closes = np.array([v['close'] for v in velas])
                ema9 = np.mean(closes[-9:]) if len(closes) >= 9 else np.mean(closes)
                ema21 = np.mean(closes[-21:]) if len(closes) >= 21 else ema9
                if ema9 > ema21 * 1.0002: self.tendencias[nome] = "ALTA 📈"
                elif ema9 < ema21 * 0.9998: self.tendencias[nome] = "BAIXA 📉"
                else: self.tendencias[nome] = "NEUTRA ➡️"

    def avaliar(self, sinal, velas):
        direcao = sinal.get('direcao')
        ativo = sinal.get('ativo', '')

        # Pavio
        try:
            if len(velas) >= 1:
                v = velas[-1]
                corpo = abs(v['close'] - v['open'])
                if corpo > 0:
                    if direcao == 'CALL':
                        ratio = (v['high'] - max(v['close'], v['open'])) / corpo
                        if ratio > self.max_pavio_ratio: return False, 0, ["🕯️ Pavio superior grande"]
                    else:
                        ratio = (min(v['close'], v['open']) - v['low']) / corpo
                        if ratio > self.max_pavio_ratio: return False, 0, ["🕯️ Pavio inferior grande"]
        except: pass

        # 🌊 FLUXO
        fluxo = self.fluxo_atual.get(ativo, 'NEUTRO')
        forca = self.forca_fluxo.get(ativo, 0)

        if fluxo == 'NEUTRO':
            self.bloqueios_neutro += 1
            return False, 0, ["🌊 BLOQUEADO: Fluxo NEUTRO"]

        if direcao != fluxo and forca >= 0.65:
            self.bloqueios_fluxo += 1
            return False, 0, [f"🌊 BLOQUEADO: Contra fluxo {fluxo}"]

        # Score
        score = 0
        motivos = []
        conf = sinal.get('confianca', 0)
        score += (conf / 100) * 35
        est = sinal.get('estrategias', 0)
        score += (est / 5) * 25
        if est >= 3: motivos.append(f"{est}/5 estratégias")
        hora = datetime.now().hour
        if 6 <= hora <= 23: score += 15
        if len(self.historico) > 0 and np.mean(self.historico) > 70: score += 10

        if direcao == fluxo:
            bonus = int(forca * 15)
            score += bonus
            motivos.append(f"🌊 Fluxo {fluxo} +{bonus}")
            self.bonus_fluxo += 1
        else:
            penalty = int(forca * 10)
            score -= penalty
            motivos.append(f"⚠️ Contra fluxo -{penalty}")

        motivos.append(f"Score: {score:.0f}/{self.score_minimo}")
        aprovado = score >= self.score_minimo
        return aprovado, score, motivos

    def registrar(self, resultado):
        self.historico.append(1 if resultado == 'win' else 0)

# ═══════════════════════════════════════════
# IQ API
# ═══════════════════════════════════════════
class IQAPI:
    def __init__(self, e, s, a):
        self.e = e; self.s = s; self.a = a; self.api = None
        self.velas = {nome: deque(maxlen=100) for nome in a}
        self.ok = False; self.erros = 0

    def conectar(self):
        for t in range(5):
            try:
                if self.api:
                    try: self.api.close()
                    except: pass
                    time.sleep(2)
                self.api = IQ_Option(self.e, self.s)
                ok, _ = self.api.connect()
                if ok:
                    self.ok = True; self.erros = 0
                    print(f"  {C.G}✅ Conectado!{C.E}")
                    return True
                print(f"  {C.Y}⚠️ Tentativa {t+1}/5{C.E}")
                time.sleep(5 * (t+1))
            except: time.sleep(5 * (t+1))
        self.ok = False; return False

    def obter(self, ativo_id, qtd=80):
        for retry in range(3):
            if not self.ok and not self.conectar(): return 0
            try:
                c = self.api.get_candles(ativo_id, 60, qtd, time.time())
                if c and len(c) > 0:
                    nome = [k for k, v in self.a.items() if v == ativo_id][0]
                    self.velas[nome].clear()
                    for x in c[-qtd:]:
                        if isinstance(x, dict):
                            try:
                                self.velas[nome].append({
                                    'time': datetime.fromtimestamp(x.get('from', 0)),
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

    def atualizar(self):
        if not self.ok: self.conectar()
        for n, i in self.a.items():
            try: self.obter(i)
            except: pass

# ═══════════════════════════════════════════
# BOT
# ═══════════════════════════════════════════
class Bot:
    def __init__(self):
        self.tg = Telegram(TOKEN, CHAT)
        self.m = QuantumIA()
        self.p = Placar()
        self.iq = IQAPI(EMAIL, SENHA, ATIVOS_OTC)
        self.cerebro = CerebroVisual()
        self.op = False; self.g = 0; self.ult = 0; self.sinais = 0
        self.ultimo_sinal_ativo = {}
        self.intervalo_minimo = 180
        self.sinais_recusados = 0
        self.ultimo_dia = datetime.now().day
        self.placar_enviado = False

    def pode_enviar(self, ativo):
        agora = time.time()
        if ativo in self.ultimo_sinal_ativo:
            if agora - self.ultimo_sinal_ativo[ativo] < self.intervalo_minimo: return False
        return True

    def registrar_envio(self, ativo):
        self.ultimo_sinal_ativo[ativo] = time.time()

    def _barra(self, pct):
        p = int(pct / 10)
        return '█' * p + '░' * (10 - p)

    def fechar_dia(self):
        agora = datetime.now()
        data = agora.strftime('%d/%m/%Y')
        dias = {'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
                'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
        dia = dias.get(agora.strftime('%A'), '')
        w = self.p.w; g1 = self.p.g1; l = self.p.l
        total = max(w + l, 1); tx = round((w / total) * 100, 1)
        lucro = round(w * 1.6 + g1 * 0.4 - l * 5, 2)

        msg = f"""📊 *PLACAR DIÁRIO FINALIZADO*

🗓️ *{data} ({dia})*
⏰ {agora.strftime('%H:%M')}

┌──────────────────────────┐
│ ⚛️ QUANTUM IA           │
│ 🟢 Wins: {w}              │
│ 🟡 Gale 1: {g1}            │
│ 🔴 Losses: {l}            │
│ 📨 Sinais: {w+g1+l}       │
│ 🎯 Assertividade: {tx}%   │
│ [{self._barra(tx)}]      │
│ 💰 Lucro: +R${lucro}      │
│ 🛡️ Recusados: {self.sinais_recusados} │
│ 🚫 Neutro: {self.cerebro.bloqueios_neutro} │
└──────────────────────────┘

🔄 *Placar zerado!*"""
        self.tg.send(msg)
        print(f"\n{C.GOLD}╔══════════════════════════════╗{C.E}")
        print(f"{C.GOLD}║ 📊 PLACAR DIÁRIO FINALIZADO ║{C.E}")
        print(f"{C.GOLD}║ 🗓️ {data} ({dia})     ║{C.E}")
        print(f"{C.GOLD}║ 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}% 💰+R${lucro} ║{C.E}")
        print(f"{C.GOLD}╚══════════════════════════════╝{C.E}\n")
        self.p.zerar()
        self.sinais = 0; self.sinais_recusados = 0
        self.cerebro.historico.clear()
        self.cerebro.bloqueios_fluxo = 0; self.cerebro.bonus_fluxo = 0
        self.cerebro.bloqueios_neutro = 0
        print(f"  {C.G}🔄 Placar ZERADO! Novo dia!{C.E}\n")

    def fmt_sinal(self, s):
        he = (datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)).strftime('%H:%M')
        e = "🟢" if s['direcao'] == 'CALL' else "🔴"
        est = s.get('estrategias', 0)
        fluxo = self.cerebro.fluxo_atual.get(s['ativo'], 'NEUTRO')
        alinhado = "✅ ALINHADO" if fluxo == s['direcao'] else "⚠️ CONTRA"
        return f"""⚛️ SINAL QUANTUM IA ⚛️

⏰ Horário: {he}
💰 Ativo: {s['ativo']}-OTC
📈 Direção: {s['direcao']} {e}
⌛️ Expiração: M1
📊 Confiança: {s['confianca']:.0f}%
🧠 Estratégias: {est}/5
🛡️ Score IA: {s.get('score_ia',0):.0f}/100
🌊 Fluxo: {fluxo} {alinhado}

⚠️ Entrar somente no horário marcado.
🔄 1 recuperação (Gale 1)!"""

    def fmt_corr(self, r, s):
        return f"""{r}
📊 {s['ativo']}-OTC | {s['direcao']} {'🟢' if s['direcao']=='CALL' else '🔴'}
📊 Placar: 🟢{self.p.w}W 🟡{self.p.g1}G1 🔴{self.p.l}L"""

    def bateu(self, d, p, v): return v['high'] > p if d == 'CALL' else v['low'] < p

    async def esperar(self, seg=60):
        try:
            agora = datetime.now()
            alvo = agora.replace(second=0, microsecond=0) + timedelta(minutes=1)
            alvo += timedelta(seconds=seg)
            e = max(0, (alvo - agora).total_seconds())
            if e > 0: await asyncio.sleep(e)
            self.iq.atualizar()
        except: pass

    async def corrigir(self, sinal):
        at = sinal['ativo']; d = sinal['direcao']
        try:
            await self.esperar(8); v = self.iq.velas[at]
            if len(v) < 2: self.op = False; return
            pc = v[-1]['open']; hora = v[-1]['time'].strftime('%H:%M')
            print(f"\n  ⚛️ {at}-OTC {d} | OPEN:{pc:.5f} | Vela:{hora}")
            await self.esperar(5); v = self.iq.velas[at]
            if len(v) > 0 and self.bateu(d, pc, v[-1]):
                r = self.p.win(0); print(f"  ✅ {r}"); self.tg.send(self.fmt_corr(r, sinal))
                self.cerebro.registrar('win'); self.cerebro.atualizar_stats(at, 'win'); self.op = False; return
            print(f"  ❌ Principal")
            self.g = 1; v = self.iq.velas[at]; pg = v[-1]['open'] if len(v) > 0 else pc
            print(f"  🔄 GALE 1 | OPEN:{pg:.5f}"); await self.esperar(5); v = self.iq.velas[at]
            if len(v) > 0 and self.bateu(d, pg, v[-1]):
                r = self.p.win(1); print(f"  ✅ {r}"); self.tg.send(self.fmt_corr(r, sinal))
                self.cerebro.registrar('win'); self.cerebro.atualizar_stats(at, 'win'); self.op = False; return
            print(f"  ❌ GALE 1"); r = self.p.loss(); print(f"  🔴 {r}"); self.tg.send(self.fmt_corr(r, sinal))
            self.cerebro.registrar('loss'); self.cerebro.atualizar_stats(at, 'loss'); self.op = False
        except Exception as e: print(f"  ❌ {e}"); self.op = False

    async def run(self):
        banner()
        print(f"\n  ⚛️ Iniciando Quantum IA Cloud...\n")
        if not self.iq.conectar(): print(f"  ❌ Falha conexão!"); return
        self.iq.atualizar()
        self.cerebro.atualizar_fluxos(self.iq.velas)
        self.ultimo_dia = datetime.now().day
        print(f"\n  ✅ QUANTUM IA CLOUD | 🧠👁️🌊 | 🚫 NEUTRO BLOQUEADO | 📊 Placar Auto\n")
        self.tg.send(f"⚛️ *QUANTUM IA CLOUD*\n📊 3 pares OTC\n🌊 Fluxo ALINHADO\n🚫 NEUTRO BLOQUEADO\n⏰ {datetime.now().strftime('%H:%M:%S')}")

        while True:
            try:
                agora = datetime.now()

                # 📊 PLACAR DIÁRIO
                if agora.hour == 23 and agora.minute == 59 and not self.placar_enviado:
                    self.fechar_dia()
                    self.placar_enviado = True
                if agora.day != self.ultimo_dia:
                    self.ultimo_dia = agora.day
                    self.placar_enviado = False

                if agora.second in [0, 30]:
                    try:
                        self.iq.atualizar()
                        self.cerebro.atualizar_tendencias(self.iq.velas)
                        self.cerebro.atualizar_fluxos(self.iq.velas)
                    except: self.iq.ok = False

                if not self.op:
                    try:
                        bloqueados = [a for a in ATIVOS_OTC if not self.pode_enviar(a)]
                        sinal = self.m.melhor_par(self.iq.velas, bloqueados, self.cerebro.stats_pares)
                        if sinal and time.time() - self.ult > 25:
                            aprovado, score, motivos = self.cerebro.avaliar(sinal, self.iq.velas[sinal['ativo']])
                            if aprovado:
                                self.op = True; self.sinais += 1
                                self.registrar_envio(sinal['ativo'])
                                sinal['score_ia'] = score
                                he = (agora.replace(second=0, microsecond=0) + timedelta(minutes=1)).strftime('%H:%M')
                                print(f"\n⚛️ #{self.sinais} {sinal['ativo']}-OTC {sinal['direcao']} | {sinal['confianca']:.0f}% | 🧠{sinal.get('estrategias',0)}/5 | 🛡️{score:.0f}/100 | ⏰ {he}")
                                self.tg.send(self.fmt_sinal(sinal)); self.ult = time.time()
                                asyncio.create_task(self.corrigir(sinal))
                            else: self.sinais_recusados += 1
                    except: pass

                if agora.second in [0, 30]:
                    try:
                        w, l, g1 = self.p.w, self.p.l, self.p.g1
                        t = max(w + l, 1); tx = round((w / t) * 100, 1)
                        lucro = round(w * 1.6 + g1 * 0.4 - l * 5, 2)
                        print(f"{C.GOLD}┌──────────────────────────────────────────────────────────┐{C.E}")
                        print(f"{C.GOLD}│{C.E} ⏰ {agora.strftime('%H:%M:%S')} | 📨{self.sinais} | 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}% | 💰+R${lucro}")
                        print(f"{C.GOLD}│{C.E} 🌊 {' | '.join([f'{n}:{self.cerebro.fluxo_atual[n]}' for n in ATIVOS_OTC])}")
                        print(f"{C.GOLD}│{C.E} 🚫 Neutro: {self.cerebro.bloqueios_neutro} | ✅ Alinhado: {self.cerebro.bonus_fluxo} | 🛡️ Recusados: {self.sinais_recusados}")
                        print(f"{C.GOLD}└──────────────────────────────────────────────────────────┘{C.E}")
                    except: pass

                await asyncio.sleep(3)

            except KeyboardInterrupt:
                clear()
                w, l, g1 = self.p.w, self.p.l, self.p.g1
                t = max(w + l, 1); tx = round((w / t) * 100, 1)
                lucro = round(w * 1.6 + g1 * 0.4 - l * 5, 2)
                print(f"\n👋 🟢{w}W 🟡{g1}G1 🔴{l}L | 🎯{tx}% | 💰+R${lucro} | 📨{self.sinais}\n")
                self.tg.send(f"⚠️ *Desligado*\n🟢{w}W 🟡{g1}G1 🔴{l}L\n🎯{tx}%\n💰+R${lucro}")
                if self.iq.api:
                    try: self.iq.api.close()
                    except: pass
                break
            except Exception as e:
                print(f"  {C.R}❌ {str(e)[:40]}{C.E}")
                self.iq.ok = False
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(Bot().run())
