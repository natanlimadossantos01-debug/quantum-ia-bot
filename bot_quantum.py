#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   ⚛️  Q U A N T U M   I A   M 1           ║
║   🔄 Gale 1 | 🧠 Cérebro Visual + Trader  ║
║   👁️ Visão Gráfica | 📈 LTA/LTB           ║
║   ⚡ MODO TURBO: +Sinais +Assertividade    ║
║   ☁️ Railway Ready | 🇧🇷 Brasília         ║
╚══════════════════════════════════════════════╝
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os
from datetime import datetime, timedelta
from collections import deque
from pathlib import Path

# ═══════════════════════════════════════════
# 🇧🇷 HORÁRIO DE BRASÍLIA
# ═══════════════════════════════════════════
os.environ['TZ'] = 'America/Sao_Paulo'
time.tzset()

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

class C:
    G='\033[92m';Y='\033[93m';R='\033[91m';C='\033[96m';W='\033[97m';B='\033[1m';E='\033[0m';GOLD='\033[38;5;220m'

def clear(): os.system('clear 2>/dev/null || cls 2>/dev/null')

def banner():
    clear()
    print(f"{C.GOLD}{C.B}╔══════════════════════════════════════════════╗")
    print(f"║   ⚛️  Q U A N T U M   I A   M 1           ║")
    print(f"║   🔄 Gale 1 | 🧠 Cérebro Visual + Trader  ║")
    print(f"║   ⚡ MODO TURBO | 🇧🇷 Brasília           ║")
    print(f"╚══════════════════════════════════════════════╝{C.E}")

# ═══════════════════════════════════════════
# ✅ CONFIGURAÇÃO PARA NUVEM
# ═══════════════════════════════════════════
def carregar_config():
    return {
        "token": os.environ['TELEGRAM_TOKEN'],
        "chat": os.environ['CHAT_ID'],
        "email": os.environ['IQ_EMAIL'],
        "senha": os.environ['IQ_PASSWORD']
    }

cfg = carregar_config()
TOKEN = cfg['token']
CHAT = cfg['chat']
EMAIL = cfg['email']
SENHA = cfg['senha']

from iqoptionapi.stable_api import IQ_Option

ATIVOS_OTC = {"EURUSD":"EURUSD-OTC", "GBPUSD":"GBPUSD-OTC", "EURGBP":"EURGBP-OTC"}

class Placar:
    def __init__(self):
        self.w = 0
        self.l = 0
        self.g1 = 0
        self.s = deque(maxlen=20)
    
    def win(self, g=0):
        self.w += 1
        if g == 0:
            self.s.append('🟢')
            return "✅ WIN"
        else:
            self.g1 += 1
            self.s.append('🟡')
            return "✅ WIN GALE 1"
    
    def loss(self):
        self.l += 1
        self.s.append('🔴')
        return "❌ LOSS"

class Telegram:
    def __init__(self, t, c):
        self.u = f"https://api.telegram.org/bot{t}"
        self.c = c
    
    def send(self, txt):
        try:
            requests.post(f"{self.u}/sendMessage", json={"chat_id": self.c, "text": txt, "parse_mode": "Markdown"}, timeout=3)
        except:
            pass

# ═══════════════════════════════════════════
# 5 ESTRATÉGIAS ROBUSTAS
# ═══════════════════════════════════════════
class Mortalha:
    def sma(self, d, p):
        try:
            if len(d) >= p: return sum(d[-p:])/p
            return sum(d)/len(d) if d else 0
        except: return 0
    
    def wma(self, d, p):
        try:
            if len(d) < p: return sum(d)/len(d) if d else 0
            w = np.arange(1, p+1)
            return np.sum(np.array(d[-p:]) * w) / np.sum(w)
        except: return 0
    
    def analisar(self, v):
        try:
            if len(v) < 30: return None, 0
            c = np.array([x['close'] for x in v])
            b1 = np.zeros(len(c))
            for i in range(len(c)):
                if i >= 33: b1[i] = self.sma(c[:i+1], 1) - self.sma(c[:i+1], 34)
            b2 = np.zeros(len(b1))
            for i in range(len(b1)):
                if i >= 3: b2[i] = self.wma(b1[:i+1], 4)
            if b1[-1] > b2[-1] and b1[-2] <= b2[-2]:
                return 'CALL', min(45 + abs(b1[-1]-b2[-1])*10000, 90)
            if b1[-1] < b2[-1] and b1[-2] >= b2[-2]:
                return 'PUT', min(45 + abs(b1[-1]-b2[-1])*10000, 90)
            return None, 0
        except: return None, 0

class Formiga:
    def calcular_ema(self, p, pe):
        try:
            if len(p) < pe: return sum(p)/len(p) if p else 0
            return np.mean(p[-pe:])
        except: return 0
    
    def analisar(self, v):
        try:
            if len(v) < 12: return None, 0
            precos = np.array([x['close'] for x in v])
            highs = np.array([x['high'] for x in v])
            lows = np.array([x['low'] for x in v])
            ema5 = self.calcular_ema(precos, 5)
            ema10 = self.calcular_ema(precos, 10)
            dif = ((ema5-ema10)/ema10)*100 if ema10 > 0 else 0
            tp = [(h+l+c)/3 for h,l,c in zip(highs, lows, precos)]
            mtp = np.mean(tp[-7:]) if len(tp) >= 7 else np.mean(tp)
            desv = np.mean([abs(t-mtp) for t in tp[-7:]]) if len(tp) >= 7 else 1
            cci = (tp[-1]-mtp)/(0.015*desv) if desv > 0 else 0
            obv = sum(v[i]['volume'] if precos[i] > precos[i-1] else -v[i]['volume'] for i in range(-min(5, len(v)-1), 0))
            sc = sp = 0
            if dif > 0.02: sc += 3
            elif dif > 0.005: sc += 1
            elif dif < -0.02: sp += 3
            elif dif < -0.005: sp += 1
            if cci < -100: sc += 3
            elif cci < -60: sc += 2
            elif cci > 100: sp += 3
            elif cci > 60: sp += 2
            if obv > 200: sc += 2
            elif obv > 50: sc += 1
            elif obv < -200: sp += 2
            elif obv < -50: sp += 1
            if sc >= 3 and sc > sp: return 'CALL', min(50+sc*4, 88)
            if sp >= 3 and sp > sc: return 'PUT', min(50+sp*4, 88)
            return None, 0
        except: return None, 0

class Fortaleza:
    def rsi(self, p, pe=7):
        try:
            if len(p) < pe+1: return 50
            d = np.diff(list(p[-pe-1:]))
            g = np.where(d>0, d, 0)
            l = np.where(d<0, -d, 0)
            mg = np.mean(g) if len(g) > 0 else 0
            mp = np.mean(l) if len(l) > 0 else 0
            if mp == 0: return 100
            return 100 - (100/(1+mg/mp))
        except: return 50
    
    def analisar(self, v):
        try:
            if len(v) < 18: return None, 0
            precos = np.array([x['close'] for x in v])
            rsi_val = self.rsi(precos)
            m = np.mean(precos[-10:]) if len(precos) >= 10 else np.mean(precos)
            s = np.std(precos[-10:]) if len(precos) >= 10 else 0
            bs = m + 2*s
            bi = m - 2*s
            h_list = [x['high'] for x in v[-5:]]
            l_list = [x['low'] for x in v[-5:]]
            h = max(h_list)
            l = min(l_list)
            stoch = ((precos[-1]-l)/(h-l))*100 if h != l else 50
            ema5 = np.mean(precos[-5:]) if len(precos) >= 5 else precos[-1]
            ema13 = np.mean(precos[-13:]) if len(precos) >= 13 else ema5
            macd = ema5 - ema13
            tend = sum(1 for i in range(-min(5, len(v)-1), 0) if precos[i] > precos[i-1])
            sc = sp = 0
            if rsi_val < 30: sc += 3
            elif rsi_val < 40: sc += 2
            if rsi_val > 70: sp += 3
            elif rsi_val > 60: sp += 2
            if precos[-1] <= bi*1.0004: sc += 3
            if precos[-1] >= bs*0.9996: sp += 3
            if stoch < 25: sc += 3
            elif stoch < 35: sc += 1
            if stoch > 75: sp += 3
            elif stoch > 65: sp += 1
            if macd > 0: sc += 2
            if macd < 0: sp += 2
            if tend >= 4: sc += 2
            if tend <= 1: sp += 2
            if sc >= 6 and sc > sp: return 'CALL', min(65+sc*2, 92)
            if sp >= 6 and sp > sc: return 'PUT', min(65+sp*2, 92)
            return None, 0
        except: return None, 0

class RaioNegro:
    def analisar(self, v):
        try:
            if len(v) < 12: return None, 0
            precos = np.array([x['close'] for x in v])
            ema5 = np.mean(precos[-5:]) if len(precos) >= 5 else precos[-1]
            ema13 = np.mean(precos[-13:]) if len(precos) >= 13 else ema5
            macd = ema5 - ema13
            sinal = macd * 0.5
            mom = precos[-1] - precos[-3] if len(precos) >= 3 else 0
            altas = sum(1 for i in range(-min(4, len(v)-1), 0) if precos[i] > precos[i-1])
            forca = (altas/max(4,1))*100
            sc = sp = 0
            if macd > sinal and macd > 0: sc += 3
            elif macd > sinal: sc += 1
            elif macd < sinal and macd < 0: sp += 3
            elif macd < sinal: sp += 1
            if mom > 0.00003: sc += 3
            elif mom > 0: sc += 1
            elif mom < -0.00003: sp += 3
            elif mom < 0: sp += 1
            if forca >= 50: sc += 2
            elif forca >= 30: sc += 1
            elif forca <= 30: sp += 2
            elif forca <= 50: sp += 1
            if sc >= 2 and sc > sp: return 'CALL', min(48+sc*4, 85)
            if sp >= 2 and sp > sc: return 'PUT', min(48+sp*4, 85)
            return None, 0
        except: return None, 0

class Tsunami:
    def analisar(self, v):
        try:
            if len(v) < 12: return None, 0
            precos = np.array([x['close'] for x in v])
            highs = np.array([x['high'] for x in v])
            lows = np.array([x['low'] for x in v])
            tr_list = [max(highs[i]-lows[i], abs(highs[i]-precos[i-1]), abs(lows[i]-precos[i-1])) for i in range(-min(7, len(v)-1), 0)]
            atr = np.mean(tr_list) if tr_list else 0
            plus_dm = sum(max(highs[i]-highs[i-1], 0) for i in range(-min(7, len(v)-1), 0) if highs[i]-highs[i-1] > lows[i-1]-lows[i])
            minus_dm = sum(max(lows[i-1]-lows[i], 0) for i in range(-min(7, len(v)-1), 0) if lows[i-1]-lows[i] > highs[i]-highs[i-1])
            pdi = (plus_dm/atr)*100 if atr > 0 else 0
            mdi = (minus_dm/atr)*100 if atr > 0 else 0
            adx = abs(pdi-mdi)/(pdi+mdi)*100 if (pdi+mdi) > 0 else 0
            aroon_up = ((7-highs[-7:].tolist().index(max(highs[-7:])))/7)*100 if len(highs) >= 7 else 50
            aroon_down = ((7-lows[-7:].tolist().index(min(lows[-7:])))/7)*100 if len(lows) >= 7 else 50
            sc = sp = 0
            if adx > 15 and pdi > mdi: sc += 3
            elif adx > 10 and pdi > mdi: sc += 1
            elif adx > 15 and mdi > pdi: sp += 3
            elif adx > 10 and mdi > pdi: sp += 1
            if aroon_up > 50: sc += 3
            elif aroon_up > 30: sc += 1
            if aroon_down > 50: sp += 3
            elif aroon_down > 30: sp += 1
            if sc >= 3 and sc > sp: return 'CALL', min(52+sc*3, 88)
            if sp >= 3 and sp > sc: return 'PUT', min(52+sp*3, 88)
            return None, 0
        except: return None, 0

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
            votos = {'CALL':0, 'PUT':0}
            confiancas = {'CALL':[], 'PUT':[]}
            for nome, estrategia in [('mortalha', self.mortalha), ('formiga', self.formiga),
                                      ('fortaleza', self.fortaleza), ('raio_negro', self.raio_negro),
                                      ('tsunami', self.tsunami)]:
                try:
                    d, c = estrategia.analisar(v)
                    if d:
                        resultados.append((nome, d, c))
                        votos[d] += 1
                        confiancas[d].append(c)
                except: pass
            total = len(resultados)
            if total < self.min_estrategias: return None, 0, total
            if votos['CALL'] >= self.min_estrategias and votos['CALL'] > votos['PUT']:
                conf = np.mean(confiancas['CALL'])
                bonus = (total-2)*3
                return 'CALL', min(conf+bonus, 95), total
            if votos['PUT'] >= self.min_estrategias and votos['PUT'] > votos['CALL']:
                conf = np.mean(confiancas['PUT'])
                bonus = (total-2)*3
                return 'PUT', min(conf+bonus, 95), total
            return None, 0, total
        except: return None, 0, 0
    
    def melhor_par(self, velas_dict, bloqueados, stats_pares, pares_bloqueados_corr):
        try:
            melhor = None
            melhor_score = 0
            for nome, velas in velas_dict.items():
                if nome in bloqueados or nome in pares_bloqueados_corr: continue
                if nome in stats_pares and stats_pares[nome]['total'] >= 5:
                    if stats_pares[nome]['taxa'] < 50: continue
                if len(velas) >= 30:
                    d, cf, num = self.analisar_completo(velas)
                    if d:
                        score = cf + (num*5)
                        if nome in stats_pares and stats_pares[nome]['total'] >= 5:
                            score += stats_pares[nome]['taxa'] * 0.2
                        if score > melhor_score:
                            melhor_score = score
                            melhor = {'ativo': nome, 'direcao': d, 'confianca': cf, 'estrategias': num}
            return melhor
        except: return None

class CerebroVisual:
    def __init__(self):
        self.historico = deque(maxlen=50)
        self.score_minimo = 55
        self.score_base = 55
        self.max_pavio_ratio = 0.7
        self.stats_pares = {nome: {'wins':0, 'losses':0, 'total':0, 'taxa':0} for nome in ATIVOS_OTC}
        self.tendencias = {nome: "NEUTRA" for nome in ATIVOS_OTC}
        self._ultima_exibicao_recusa = {}
        self.wins_seguidos = 0
        self.losses_seguidos = 0
        self.ultimo_loss_time = 0
        self.em_descanso = False
        self.descanso_ate = 0
    
    def atualizar_score_dinamico(self):
        if self.losses_seguidos >= 3: self.score_minimo = min(self.score_base+15, 70)
        elif self.losses_seguidos >= 2: self.score_minimo = min(self.score_base+10, 65)
        elif self.wins_seguidos >= 5: self.score_minimo = self.score_base
        elif self.wins_seguidos >= 3: self.score_minimo = min(self.score_base+5, 60)
        else: self.score_minimo = self.score_base
    
    def verificar_descanso(self):
        if self.em_descanso:
            if time.time() < self.descanso_ate:
                return True, f"😴 Em descanso até {datetime.fromtimestamp(self.descanso_ate).strftime('%H:%M:%S')}"
            else:
                self.em_descanso = False
        return False, ""
    
    def registrar_loss(self):
        self.losses_seguidos += 1
        self.wins_seguidos = 0
        self.ultimo_loss_time = time.time()
        if self.losses_seguidos >= 3: self.em_descanso = True; self.descanso_ate = time.time()+1800
        elif self.losses_seguidos >= 2: self.em_descanso = True; self.descanso_ate = time.time()+600
    
    def registrar_win(self):
        self.wins_seguidos += 1
        self.losses_seguidos = 0
        self.em_descanso = False
    
    def atualizar_stats(self, ativo, resultado):
        if ativo in self.stats_pares:
            self.stats_pares[ativo]['total'] += 1
            if resultado == 'win': self.stats_pares[ativo]['wins'] += 1
            else: self.stats_pares[ativo]['losses'] += 1
            total = self.stats_pares[ativo]['total']
            wins = self.stats_pares[ativo]['wins']
            self.stats_pares[ativo]['taxa'] = round((wins/total)*100, 1) if total > 0 else 0
    
    def calcular_volatilidade(self, velas):
        try:
            if len(velas) < 10: return 0
            closes = np.array([x['close'] for x in velas])
            return np.std(closes[-10:]) / np.mean(closes[-10:])
        except: return 0
    
    def analisar_tendencia_par(self, velas):
        try:
            if len(velas) < 21: return "NEUTRA"
            closes = np.array([v['close'] for v in velas])
            def ema(data, period):
                if len(data) < period: return np.mean(data)
                a = 2/(period+1)
                e = np.mean(data[:period])
                for x in data[period:]: e = (x-e)*a + e
                return e
            ema9 = ema(closes, 9)
            ema21 = ema(closes, 21)
            if ema9 > ema21 * 1.0002: return "ALTA 📈"
            elif ema9 < ema21 * 0.9998: return "BAIXA 📉"
            return "NEUTRA ➡️"
        except: return "NEUTRA"
    
    def atualizar_tendencias(self, velas_dict):
        for nome, velas in velas_dict.items():
            self.tendencias[nome] = self.analisar_tendencia_par(velas)
    
    def detectar_lta_ltb(self, velas):
        try:
            if len(velas) < 20: return "NEUTRA", 0, 0, ""
            lows = np.array([v['low'] for v in velas])
            highs = np.array([v['high'] for v in velas])
            fundos = []
            topos = []
            for i in range(2, len(lows)-2):
                if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                    fundos.append((i, lows[i]))
            for i in range(2, len(highs)-2):
                if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                    topos.append((i, highs[i]))
            lta_valida = ltb_valida = False
            nivel_lta = nivel_ltb = 0
            detalhes = ""
            if len(fundos) >= 2:
                f1, f2 = fundos[-2], fundos[-1]
                if f2[1] > f1[1]:
                    lta_valida = True
                    idx_diff = f2[0] - f1[0]
                    price_diff = f2[1] - f1[1]
                    nivel_lta = f2[1] + (price_diff/idx_diff)*(len(velas)-f2[0])
                    detalhes += f"LTA 📈 ({f1[1]:.5f}→{f2[1]:.5f}) "
            if len(topos) >= 2:
                t1, t2 = topos[-2], topos[-1]
                if t2[1] < t1[1]:
                    ltb_valida = True
                    idx_diff = t2[0] - t1[0]
                    price_diff = t2[1] - t1[1]
                    nivel_ltb = t2[1] + (price_diff/idx_diff)*(len(velas)-t2[0])
                    detalhes += f"LTB 📉 ({t1[1]:.5f}→{t2[1]:.5f}) "
            if lta_valida and ltb_valida: return "DUPLA", nivel_lta, nivel_ltb, detalhes
            elif lta_valida: return "LTA", nivel_lta, nivel_ltb, detalhes
            elif ltb_valida: return "LTB", nivel_lta, nivel_ltb, detalhes
            return "NEUTRA", 0, 0, ""
        except: return "NEUTRA", 0, 0, ""
    
    def filtro_lta_ltb(self, velas, direcao):
        tipo, nivel_lta, nivel_ltb, detalhes = self.detectar_lta_ltb(velas)
        if tipo == "NEUTRA": return True, ""
        preco_atual = velas[-1]['close']
        if direcao == 'CALL':
            if tipo == "LTA" or tipo == "DUPLA":
                if preco_atual < nivel_lta*0.9995:
                    return False, f"📈 Abaixo da LTA ({nivel_lta:.5f})"
            if tipo == "LTB" and preco_atual < nivel_ltb*1.0005:
                return False, f"📉 Abaixo da LTB ({nivel_ltb:.5f})"
        if direcao == 'PUT':
            if tipo == "LTB" or tipo == "DUPLA":
                if preco_atual > nivel_ltb*1.0005:
                    return False, f"📉 Acima da LTB ({nivel_ltb:.5f})"
            if tipo == "LTA" and preco_atual > nivel_lta*0.9995:
                return False, f"📈 Acima da LTA ({nivel_lta:.5f})"
        return True, ""
    
    def avaliacao_visual(self, velas, direcao):
        if len(velas) < 10: return 50, "Poucas velas"
        nota = 50
        detalhes = []
        highs = np.array([v['high'] for v in velas])
        lows = np.array([v['low'] for v in velas])
        ultimo_fundo = np.min(lows[-5:])
        ultimo_topo = np.max(highs[-5:])
        if direcao == 'CALL':
            if lows[-1] > ultimo_fundo * 1.0002: nota += 10; detalhes.append("Fundo ascendente")
        else:
            if highs[-1] < ultimo_topo * 0.9998: nota += 10; detalhes.append("Topo descendente")
        corpo_atual = abs(velas[-1]['close'] - velas[-1]['open'])
        pavio_sup = velas[-1]['high'] - max(velas[-1]['close'], velas[-1]['open'])
        pavio_inf = min(velas[-1]['close'], velas[-1]['open']) - velas[-1]['low']
        corpo_anterior = abs(velas[-2]['close'] - velas[-2]['open'])
        if direcao == 'CALL' and pavio_inf > corpo_atual*2 and pavio_sup < corpo_atual*0.3:
            nota += 15; detalhes.append("Martelo")
        elif direcao == 'PUT' and pavio_sup > corpo_atual*2 and pavio_inf < corpo_atual*0.3:
            nota += 15; detalhes.append("Estrela Cadente")
        elif corpo_atual > corpo_anterior*1.5:
            if direcao == 'CALL' and velas[-1]['close'] > velas[-2]['open']:
                nota += 15; detalhes.append("Engolfo de Alta")
            elif direcao == 'PUT' and velas[-1]['close'] < velas[-2]['open']:
                nota += 15; detalhes.append("Engolfo de Baixa")
        tendencia_visual = sum(1 for i in range(-4, 0) if velas[i]['close'] > velas[i-1]['close'])
        if direcao == 'CALL' and tendencia_visual >= 3: nota += 10; detalhes.append("Força visual (3+ velas de alta)")
        elif direcao == 'PUT' and tendencia_visual <= 1: nota += 10; detalhes.append("Força visual (3+ velas de baixa)")
        if direcao == 'CALL' and pavio_sup < corpo_atual*0.2: nota += 5; detalhes.append("Sem rejeição superior")
        elif direcao == 'PUT' and pavio_inf < corpo_atual*0.2: nota += 5; detalhes.append("Sem rejeição inferior")
        tipo, _, _, det_tend = self.detectar_lta_ltb(velas)
        if det_tend: detalhes.append(det_tend.strip())
        nota_final = min(nota, 100)
        return nota_final, ", ".join(detalhes) if detalhes else "Setup visual neutro"
    
    def filtro_volume(self, velas):
        try:
            if len(velas) < 10: return True, ""
            volumes = [v['volume'] for v in velas[-10:]]
            vol_atual = volumes[-1]
            vol_medio = np.mean(volumes[:-1]) if len(volumes) > 1 else vol_atual
            if vol_medio > 0 and vol_atual < vol_medio*1.1:
                return False, f"📊 Volume baixo ({vol_atual:.0f} < {vol_medio*1.1:.0f})"
            return True, ""
        except: return True, ""
    
    def filtrar_correlacao(self, sinais_por_par):
        bloqueados = set()
        if 'EURUSD' in sinais_por_par and 'GBPUSD' in sinais_por_par:
            sinal_eur = sinais_por_par['EURUSD']
            sinal_gbp = sinais_por_par['GBPUSD']
            if sinal_eur['direcao'] != sinal_gbp['direcao']:
                bloqueados.add('EURUSD')
                bloqueados.add('GBPUSD')
        return bloqueados
    
    def filtro_zona_seguranca(self, velas):
        try:
            if len(velas) < 20: return True, ""
            highs = np.array([v['high'] for v in velas])
            lows = np.array([v['low'] for v in velas])
            resistencia = np.max(highs[-20:])
            suporte = np.min(lows[-20:])
            preco_atual = velas[-1]['close']
            dist_resistencia = abs(preco_atual-resistencia)/preco_atual
            dist_suporte = abs(preco_atual-suporte)/preco_atual
            if dist_resistencia < 0.0003 or dist_suporte < 0.0003:
                return False, f"🛡️ Zona de congestão (S/R próximo: {suporte:.5f}/{resistencia:.5f})"
            return True, ""
        except: return True, ""
    
    def pode_exibir_recusa(self, par, direcao):
        chave = f"{par}_{direcao}"
        agora = time.time()
        if chave in self._ultima_exibicao_recusa and (agora-self._ultima_exibicao_recusa[chave]) < 300:
            return False
        self._ultima_exibicao_recusa[chave] = agora
        return True
    
    def avaliar(self, sinal, velas, sinais_por_par=None):
        direcao = sinal.get('direcao')
        ativo = sinal.get('ativo', '')
        em_descanso, msg_descanso = self.verificar_descanso()
        if em_descanso: return False, 0, [msg_descanso], 0, ""
        self.atualizar_score_dinamico()
        lta_ok, lta_msg = self.filtro_lta_ltb(velas, direcao)
        if not lta_ok: return False, 0, [lta_msg], 0, ""
        pavio_ok, pavio_msg = self._filtro_pavio(velas, direcao)
        if not pavio_ok: return False, 0, [pavio_msg], 0, ""
        tendencia_ok, tendencia_msg = self._filtro_tendencia_turbo(velas, direcao)
        if not tendencia_ok:
            if self.pode_exibir_recusa(ativo, direcao): return False, 0, [tendencia_msg], 0, ""
            else: return False, 0, ["__SILENCIADO__"], 0, ""
        volume_ok, volume_msg = self.filtro_volume(velas)
        if not volume_ok: return False, 0, [volume_msg], 0, ""
        zona_ok, zona_msg = self.filtro_zona_seguranca(velas)
        if not zona_ok: return False, 0, [zona_msg], 0, ""
        nota_visual, detalhes_visual = self.avaliacao_visual(velas, direcao)
        if nota_visual < 45: return False, 0, [f"👁️ Gráfico ruim ({detalhes_visual})"], nota_visual, detalhes_visual
        score = 0
        motivos = []
        conf = sinal.get('confianca', 0)
        score += (conf/100)*30
        if conf >= 70: motivos.append("Alta confiança")
        est = sinal.get('estrategias', 0)
        score += (est/5)*25
        if est >= 3: motivos.append(f"{est}/5 estratégias")
        vol = self.calcular_volatilidade(velas)
        if 0.0001 < vol < 0.002: score += 20; motivos.append("Volatilidade ideal")
        elif vol > 0: score += 10
        hora = datetime.now().hour
        if 6 <= hora <= 23: score += 15
        if 8 <= hora <= 17: motivos.append("Horário nobre")
        if len(self.historico) > 0 and np.mean(self.historico) > 70: score += 10
        score += (nota_visual/100)*15
        motivos.append(f"👁️ {detalhes_visual}")
        aprovado = score >= self.score_minimo
        return aprovado, score, motivos, nota_visual, detalhes_visual
    
    def registrar(self, resultado):
        self.historico.append(1 if resultado == 'win' else 0)
        if resultado == 'win': self.registrar_win()
        else: self.registrar_loss()
    
    def _filtro_pavio(self, velas, direcao):
        try:
            if len(velas) < 1: return True, ""
            v = velas[-1]
            corpo = abs(v['close'] - v['open'])
            if corpo == 0: return True, ""
            if direcao == 'CALL':
                ratio = (v['high'] - max(v['close'], v['open'])) / corpo
                if ratio > self.max_pavio_ratio: return False, f"🕯️ Pavio superior grande"
            else:
                ratio = (min(v['close'], v['open']) - v['low']) / corpo
                if ratio > self.max_pavio_ratio: return False, f"🕯️ Pavio inferior grande"
            return True, ""
        except: return True, ""
    
    def _filtro_tendencia_turbo(self, velas, direcao):
        try:
            if len(velas) < 20: return True, ""
            closes = np.array([v['close'] for v in velas])
            def ema(data, period):
                if len(data) < period: return np.mean(data)
                a = 2/(period+1)
                e = np.mean(data[:period])
                for x in data[period:]: e = (x-e)*a + e
                return e
            ema9, ema21 = ema(closes, 9), ema(closes, 21)
            dif_percent = abs(ema9-ema21)/ema21
            if dif_percent < 0.001: return True, ""
            if direcao == 'CALL' and ema9 <= ema21: return False, f"📈 EMA9 < EMA21"
            if direcao == 'PUT' and ema9 >= ema21: return False, f"📉 EMA9 > EMA21"
            return True, ""
        except: return True, ""

class IQAPI:
    def __init__(self, e, s, a):
        self.e = e
        self.s = s
        self.a = a
        self.api = None
        self.velas = {nome: deque(maxlen=100) for nome in a}
        self.ok = False
        self.erros = 0
    
    def conectar(self):
        for tentativa in range(5):
            try:
                if self.api:
                    try: self.api.close()
                    except: pass
                    time.sleep(2)
                self.api = IQ_Option(self.e, self.s)
                ok, _ = self.api.connect()
                if ok:
                    self.ok = True
                    self.erros = 0
                    print(f"  {C.G}✅ Reconectado!{C.E}")
                    return True
                print(f"  {C.Y}⚠️ Tentativa {tentativa+1}/5{C.E}")
                time.sleep(5*(tentativa+1))
            except Exception as e:
                print(f"  {C.Y}⚠️ Erro reconexão: {str(e)[:30]}{C.E}")
                time.sleep(5*(tentativa+1))
        self.ok = False
        return False
    
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
                                    'open': float(x['open']),
                                    'high': float(x['max']),
                                    'low': float(x['min']),
                                    'close': float(x['close']),
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

class Bot:
    def __init__(self):
        self.tg = Telegram(TOKEN, CHAT)
        self.m = QuantumIA()
        self.p = Placar()
        self.iq = IQAPI(EMAIL, SENHA, ATIVOS_OTC)
        self.cerebro = CerebroVisual()
        self.op = False
        self.g = 0
        self.ult = 0
        self.sinais = 0
        self.ultimo_sinal_ativo = {}
        self.intervalo_minimo = 180
        self.sinais_recusados = 0
        self.lta_ltb_info = {nome: "" for nome in ATIVOS_OTC}
    
    def pode_enviar(self, ativo):
        agora = time.time()
        if ativo in self.ultimo_sinal_ativo:
            if agora - self.ultimo_sinal_ativo[ativo] < self.intervalo_minimo:
                return False
        return True
    
    def registrar_envio(self, ativo):
        self.ultimo_sinal_ativo[ativo] = time.time()
    
    def fmt_sinal(self, s):
        he = (datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)).strftime('%H:%M')
        e = "🟢" if s['direcao'] == 'CALL' else "🔴"
        est = s.get('estrategias', 0)
        return f"""⚛️ SINAL QUANTUM IA ⚛️

⏰ Horário: {he}
💰 Ativo: {s['ativo']}-OTC
📈 Direção: {s['direcao']} {e}
⌛️ Expiração: M1
📊 Confiança: {s['confianca']:.0f}%
🧠 Estratégias: {est}/5
🛡️ Score IA: {s.get('score_ia', 0):.0f}/100

⚠️ Entrar somente no horário marcado.
🔄 1 recuperação (Gale 1)!"""
    
    def fmt_corr(self, r, s):
        return f"""{r}
📊 {s['ativo']}-OTC | {s['direcao']} {'🟢' if s['direcao']=='CALL' else '🔴'}
📊 Placar: 🟢{self.p.w}W 🟡{self.p.g1}G1 🔴{self.p.l}L"""
    
    def bateu(self, d, p, v):
        return v['high'] > p if d == 'CALL' else v['low'] < p
    
    async def esperar(self, seg=60):
        try:
            agora = datetime.now()
            alvo = agora.replace(minute=agora.minute+1, second=0, microsecond=0) if agora.second > 0 else agora.replace(second=0, microsecond=0) + timedelta(minutes=1)
            alvo += timedelta(seconds=seg)
            e = max(0, (alvo - agora).total_seconds())
            if e > 0:
                await asyncio.sleep(e)
                self.iq.atualizar()
        except: pass
    
    async def corrigir(self, sinal):
        at = sinal['ativo']
        d = sinal['direcao']
        try:
            await self.esperar(10)
            v = self.iq.velas[at]
            if len(v) < 2:
                self.op = False
                return
            pc = v[-1]['open']
            hora = v[-1]['time'].strftime('%H:%M')
            print(f"\n  ⚛️ {at}-OTC {d} | OPEN:{pc:.5f} | Vela:{hora}")
            await self.esperar(5)
            v = self.iq.velas[at]
            if len(v) > 0 and self.bateu(d, pc, v[-1]):
                r = self.p.win(0)
                print(f"  ✅ {r}")
                self.tg.send(self.fmt_corr(r, sinal))
                self.cerebro.registrar('win')
                self.cerebro.atualizar_stats(at, 'win')
                self.op = False
                return
            print(f"  ❌ Principal")
            self.g = 1
            v = self.iq.velas[at]
            pg = v[-1]['open'] if len(v) > 0 else pc
            print(f"  🔄 GALE 1 | OPEN:{pg:.5f}")
            await self.esperar(5)
            v = self.iq.velas[at]
            if len(v) > 0 and self.bateu(d, pg, v[-1]):
                r = self.p.win(1)
                print(f"  ✅ {r}")
                self.tg.send(self.fmt_corr(r, sinal))
                self.cerebro.registrar('win')
                self.cerebro.atualizar_stats(at, 'win')
                self.op = False
                return
            print(f"  ❌ GALE 1")
            r = self.p.loss()
            print(f"  🔴 {r}")
            self.tg.send(self.fmt_corr(r, sinal))
            self.cerebro.registrar('loss')
            self.cerebro.atualizar_stats(at, 'loss')
            self.op = False
        except Exception as e:
            print(f"  ❌ {e}")
            self.op = False
    
    async def catalogacao_inicial(self):
        print(f"\n  {C.GOLD}📊 CATALOGAÇÃO INICIAL (80 velas){C.E}")
        print(f"  {C.GOLD}{'─'*50}{C.E}")
        for nome in ATIVOS_OTC:
            velas = self.iq.velas[nome]
            if len(velas) < 35:
                print(f"  {C.Y}⚠️ {nome}: Poucas velas ({len(velas)}){C.E}")
                continue
            wins = 0
            total = 0
            for i in range(35, len(velas)-1):
                janela = list(velas)[i-35:i+1]
                d, cf, num = self.m.analisar_completo(janela)
                if d:
                    total += 1
                    vela_seguinte = list(velas)[i+1]
                    if self.bateu(d, vela_seguinte['open'], vela_seguinte):
                        wins += 1
            if total > 0:
                self.cerebro.stats_pares[nome]['wins'] = wins
                self.cerebro.stats_pares[nome]['total'] = total
                self.cerebro.stats_pares[nome]['taxa'] = round((wins/total)*100, 1)
                print(f"  {C.G}✅ {nome}: {wins}/{total} acertos ({self.cerebro.stats_pares[nome]['taxa']}%){C.E}")
            else:
                print(f"  {C.Y}⚠️ {nome}: Nenhum sinal encontrado nas velas{C.E}")
        print(f"  {C.GOLD}{'─'*50}{C.E}")
    
    async def run(self):
        banner()
        print(f"\n  ⚛️ Iniciando Quantum IA MODO TURBO...\n")
        if not self.iq.conectar():
            print(f"  ❌ Falha conexão!")
            return
        self.iq.atualizar()
        await self.catalogacao_inicial()
        print(f"\n  ✅ QUANTUM IA TURBO INICIADA | ⚡ +Sinais | 🧠 Cérebro Visual | 🔄 1 GALE | 🇧🇷 Brasília\n")
        self.tg.send(f"⚛️ *QUANTUM IA TURBO*\n📊 3 pares OTC\n⚡ +Sinais +Assertividade\n🇧🇷 Horário de Brasília\n⏰ {datetime.now().strftime('%H:%M:%S')}")
        while True:
            try:
                agora = datetime.now()
                if agora.second in [0, 30]:
                    try:
                        self.iq.atualizar()
                        self.cerebro.atualizar_tendencias(self.iq.velas)
                    except:
                        self.iq.ok = False
                    for nome in ATIVOS_OTC:
                        velas = self.iq.velas[nome]
                        if len(velas) >= 20:
                            tipo, _, _, det = self.cerebro.detectar_lta_ltb(velas)
                            self.lta_ltb_info[nome] = f"{tipo}" if tipo != "NEUTRA" else ""
                if not self.op:
                    try:
                        bloqueados = [a for a in ATIVOS_OTC if not self.pode_enviar(a)]
                        sinais_por_par = {}
                        for nome in ATIVOS_OTC:
                            if nome not in bloqueados and len(self.iq.velas[nome]) >= 30:
                                d, cf, num = self.m.analisar_completo(self.iq.velas[nome])
                                if d: sinais_por_par[nome] = {'direcao': d, 'confianca': cf, 'estrategias': num}
                        pares_bloqueados_corr = self.cerebro.filtrar_correlacao(sinais_por_par)
                        sinal = self.m.melhor_par(self.iq.velas, bloqueados, self.cerebro.stats_pares, pares_bloqueados_corr)
                        if sinal and time.time() - self.ult > 25:
                            aprovado, score, motivos, nota_visual, detalhes_visual = self.cerebro.avaliar(sinal, self.iq.velas[sinal['ativo']], sinais_por_par)
                            if aprovado:
                                self.op = True
                                self.sinais += 1
                                self.registrar_envio(sinal['ativo'])
                                sinal['score_ia'] = score
                                he = (agora.replace(second=0, microsecond=0) + timedelta(minutes=1)).strftime('%H:%M')
                                print(f"\n⚛️ #{self.sinais} {sinal['ativo']}-OTC {sinal['direcao']} | {sinal['confianca']:.0f}% | 🧠{sinal.get('estrategias',0)}/5 | 🛡️{score:.0f}/{self.cerebro.score_minimo} | 👁️{nota_visual:.0f}/100 | ⏰ {he}")
                                self.tg.send(self.fmt_sinal(sinal))
                                self.ult = time.time()
                                asyncio.create_task(self.corrigir(sinal))
                            else:
                                motivos_str = ', '.join([m for m in motivos if m != "__SILENCIADO__"])
                                if motivos_str:
                                    self.sinais_recusados += 1
                                    print(f"  {C.Y}🧠 Sinal recusado ({sinal['ativo']}-OTC {sinal['direcao']}): {motivos_str} (Score: {score:.0f}/{self.cerebro.score_minimo}){C.E}")
                    except Exception as e:
                        print(f"  {C.Y}⚠️ {str(e)[:30]}{C.E}")
                if agora.second in [0, 30]:
                    try:
                        w, l, g1 = self.p.w, self.p.l, self.p.g1
                        t = max(w+l, 1)
                        tx = round((w/t)*100, 1)
                        bloqueados_str = ','.join([a for a in ATIVOS_OTC if not self.pode_enviar(a)])
                        info = f" | 🔒 {bloqueados_str}" if bloqueados_str else ""
                        tendencias_str = " | ".join([f"{nome}:{self.cerebro.tendencias[nome]}" for nome in ATIVOS_OTC])
                        stats_str = " | ".join([f"{nome}:{self.cerebro.stats_pares[nome]['taxa']}%" for nome in ATIVOS_OTC])
                        lta_str = " | ".join([f"{nome}:{self.lta_ltb_info[nome]}" if self.lta_ltb_info[nome] else f"{nome}:--" for nome in ATIVOS_OTC])
                        score_str = f"🎯Score: {self.cerebro.score_minimo}"
                        descanso_str = "😴" if self.cerebro.em_descanso else ""
                        print(f"{C.GOLD}┌──────────────────────────────────────────────────────┐{C.E}")
                        print(f"{C.GOLD}│{C.E} ⏰ {agora.strftime('%H:%M:%S')} | 📨{self.sinais} | 🏆 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}% | 🛡️{self.sinais_recusados} recusados {descanso_str}{info}")
                        print(f"{C.GOLD}│{C.E} 📈 {tendencias_str} | {score_str}")
                        print(f"{C.GOLD}│{C.E} 📐 {lta_str}")
                        print(f"{C.GOLD}│{C.E} 📊 {stats_str}")
                        print(f"{C.GOLD}└──────────────────────────────────────────────────────┘{C.E}")
                    except: pass
                await asyncio.sleep(3)
            except KeyboardInterrupt:
                clear()
                print(f"\n👋 🟢{self.p.w}W 🟡{self.p.g1}G1 🔴{self.p.l}L | {self.sinais} sinais | 🛡️{self.sinais_recusados} recusados\n")
                self.tg.send(f"⚠️ *Desligado*\n🟢{self.p.w}W 🟡{self.p.g1}G1 🔴{self.p.l}L\n🛡️{self.sinais_recusados} recusados")
                break
            except Exception as e:
                print(f"  {C.R}❌ {str(e)[:40]}{C.E}")
                self.iq.ok = False
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(Bot().run())
