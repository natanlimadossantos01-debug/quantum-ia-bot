#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   ⚛️  Q U A N T U M   I A   3 . 0         ║
║   🧠 Cérebro IA Trader Super Inteligente   ║
║   👁️ Olhos nas Velas | 📈 Análise Gráfica  ║
║   🏆 5 Estratégias + IA + Visão + Fluxo    ║
║   🔄 Gale 1 | ☁️ Cloud | 🕐 Horário Brasil ║
║   📊 Placar Diário Automático              ║
╚══════════════════════════════════════════════╝
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os
from datetime import datetime, timedelta, timezone
from collections import deque
from pathlib import Path

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

FUSO_BR = timezone(timedelta(hours=-3))

class C:
    G='\033[92m';Y='\033[93m';R='\033[91m';C='\033[96m';W='\033[97m';B='\033[1m';E='\033[0m';GOLD='\033[38;5;220m'

def clear(): os.system('clear 2>/dev/null || cls 2>/dev/null')

def banner():
    clear()
    print(f"{C.GOLD}{C.B}╔══════════════════════════════════════════════╗")
    print(f"║   ⚛️  Q U A N T U M   I A   3 . 0         ║")
    print(f"║   🧠 Cérebro IA | 👁️ Visão | 🌊 Fluxo      ║")
    print(f"║   🏆 5 Estratégias + IA + Olhos nas Velas  ║")
    print(f"╚══════════════════════════════════════════════╝{C.E}")

CONFIG_FILE = "config_quantum.json"

def carregar_config():
    cloud_token = os.environ.get('TELEGRAM_TOKEN')
    cloud_chat = os.environ.get('TELEGRAM_CHAT_ID')
    cloud_email = os.environ.get('IQ_EMAIL')
    cloud_senha = os.environ.get('IQ_SENHA')
    
    if cloud_token and cloud_chat and cloud_email and cloud_senha:
        banner()
        print(f"\n{C.G}✅ Modo CLOUD detectado!{C.E}\n")
        return {"token": cloud_token, "chat": cloud_chat, "email": cloud_email, "senha": cloud_senha}
    
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE) as f: cfg = json.load(f)
        if 'token' not in cfg: Path(CONFIG_FILE).unlink(); return carregar_config()
        banner(); print(f"\n{C.G}✅ Config carregada!{C.E}\n"); return cfg
    
    banner()
    try:
        cfg = {
            "token": input(f"{C.G}Token Telegram: {C.E}").strip(),
            "chat": input(f"{C.G}Chat ID: {C.E}").strip(),
            "email": input(f"\n{C.G}Email IQ: {C.E}").strip(),
            "senha": input(f"{C.G}Senha IQ: {C.E}").strip()
        }
    except (EOFError, KeyboardInterrupt):
        print(f"\n{C.R}❌ Configure as variáveis de ambiente!{C.E}")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'w') as f: json.dump(cfg, f, indent=2)
    banner(); print(f"\n{C.G}✅ Salvo!{C.E}\n"); return cfg

cfg = carregar_config()
TOKEN = cfg['token']; CHAT = cfg['chat']; EMAIL = cfg['email']; SENHA = cfg['senha']

from iqoptionapi.stable_api import IQ_Option

ATIVOS_OTC = {"EURUSD": "EURUSD-OTC", "GBPUSD": "GBPUSD-OTC", "EURGBP": "EURGBP-OTC"}

class Placar:
    def __init__(self): self.w = 0; self.l = 0; self.g1 = 0; self.s = deque(maxlen=20)
    def win(self, g=0):
        self.w += 1
        if g == 0: self.s.append('🟢'); return "✅ WIN"
        else: self.g1 += 1; self.s.append('🟡'); return "✅ WIN GALE 1"
    def loss(self): self.l += 1; self.s.append('🔴'); return "❌ LOSS"
    def zerar(self): self.w = 0; self.l = 0; self.g1 = 0; self.s.clear()

class Telegram:
    def __init__(self, t, c): self.u = f"https://api.telegram.org/bot{t}"; self.c = c
    def send(self, txt):
        try: requests.post(f"{self.u}/sendMessage", json={"chat_id": self.c, "text": txt, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# ═══════════════════════════════════════════
# 5 ESTRATÉGIAS
# ═══════════════════════════════════════════
class E1_Mortalha:
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

class E2_Formiga:
    def ema(self, p, pe):
        try:
            if len(p) < pe: return sum(p) / len(p) if p else 0
            return np.mean(p[-pe:])
        except: return 0
    def analisar(self, v):
        try:
            if len(v) < 15: return None, 0
            precos = np.array([x['close'] for x in v])
            highs = np.array([x['high'] for x in v])
            lows = np.array([x['low'] for x in v])
            ema5 = self.ema(precos, 5); ema10 = self.ema(precos, 10)
            dif = ((ema5 - ema10) / ema10) * 100 if ema10 > 0 else 0
            tp = [(h+l+c)/3 for h, l, c in zip(highs, lows, precos)]
            mtp = np.mean(tp[-7:]) if len(tp) >= 7 else np.mean(tp)
            desv = np.mean([abs(t-mtp) for t in tp[-7:]]) if len(tp) >= 7 else 1
            cci = (tp[-1] - mtp) / (0.015 * desv) if desv > 0 else 0
            obv = sum(v[i]['volume'] if precos[i] > precos[i-1] else -v[i]['volume'] for i in range(-min(5, len(v)-1), 0))
            sc = 0; sp = 0
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
            if sc >= 3 and sc > sp: return 'CALL', min(50 + sc * 4, 88)
            if sp >= 3 and sp > sc: return 'PUT', min(50 + sp * 4, 88)
            return None, 0
        except: return None, 0

class E3_Fortaleza:
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

class E4_RaioNegro:
    def analisar(self, v):
        try:
            if len(v) < 12: return None, 0
            precos = np.array([x['close'] for x in v])
            ema5 = np.mean(precos[-5:]) if len(precos) >= 5 else precos[-1]
            ema13 = np.mean(precos[-13:]) if len(precos) >= 13 else ema5
            macd = ema5 - ema13; sinal = macd * 0.5
            mom = precos[-1] - precos[-3] if len(precos) >= 3 else 0
            altas = sum(1 for i in range(-min(4, len(v)-1), 0) if precos[i] > precos[i-1])
            forca = (altas / max(4, 1)) * 100
            sc = 0; sp = 0
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
            if sc >= 2 and sc > sp: return 'CALL', min(48 + sc * 4, 85)
            if sp >= 2 and sp > sc: return 'PUT', min(48 + sp * 4, 85)
            return None, 0
        except: return None, 0

class E5_Tsunami:
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
# 👁️ OLHOS NAS VELAS (EXIGÊNCIA REDUZIDA)
# ═══════════════════════════════════════════
class OlhosNasVelas:
    def __init__(self):
        self.max_pavio_ratio = 0.7
    
    def analisar(self, velas, direcao):
        if len(velas) < 3: return 60, "Poucas velas"
        nota = 60
        detalhes = []
        try:
            v = velas[-1]; v1 = velas[-2]
            corpo = abs(v['close'] - v['open'])
            range_total = v['high'] - v['low']
            pavio_sup = v['high'] - max(v['close'], v['open'])
            pavio_inf = min(v['close'], v['open']) - v['low']
            
            if direcao == 'CALL':
                if pavio_inf > corpo * 1.5 and pavio_sup < corpo * 0.5:
                    nota += 20; detalhes.append("Martelo")
                elif (v['close'] > v['open'] and v1['close'] < v1['open'] and
                      v['close'] > v1['open'] and corpo > abs(v1['close']-v1['open'])*1.1):
                    nota += 18; detalhes.append("Engolfo Alta")
                elif corpo > range_total * 0.5 and v['close'] > v['open']:
                    nota += 12; detalhes.append("Vela forte")
            elif direcao == 'PUT':
                if pavio_sup > corpo * 1.5 and pavio_inf < corpo * 0.5:
                    nota += 20; detalhes.append("Estrela Cadente")
                elif (v['close'] < v['open'] and v1['close'] > v1['open'] and
                      v['close'] < v1['open'] and corpo > abs(v1['close']-v1['open'])*1.1):
                    nota += 18; detalhes.append("Engolfo Baixa")
                elif corpo > range_total * 0.5 and v['close'] < v['open']:
                    nota += 12; detalhes.append("Vela forte")
            
            precos = [x['close'] for x in velas]
            altas = sum(1 for i in range(-4, 0) if i >= -len(precos)+1 and precos[i] > precos[i-1])
            if direcao == 'CALL' and altas >= 2: nota += 10
            elif direcao == 'PUT' and altas <= 2: nota += 10
            
            if direcao == 'CALL' and pavio_sup < corpo * 0.5: nota += 8
            elif direcao == 'PUT' and pavio_inf < corpo * 0.5: nota += 8
            
            if direcao == 'CALL' and pavio_sup > corpo * 1.0: nota -= 10
            elif direcao == 'PUT' and pavio_inf > corpo * 1.0: nota -= 10
        except: pass
        
        return min(max(nota, 0), 100), ", ".join(detalhes) if detalhes else "Setup neutro"
    
    def fluxo_visual(self, velas):
        if len(velas) < 8: return 'NEUTRO', 0
        precos = [v['close'] for v in velas]
        altas = sum(1 for i in range(-8, 0) if i >= -len(precos)+1 and precos[i] > precos[i-1])
        baixas = 8 - altas
        corpos = [v['close'] - v['open'] for v in velas[-4:]]
        soma_corpos = sum(corpos)
        forca = max(altas, baixas) / 8
        if altas >= 5 and soma_corpos > 0: return 'CALL', forca
        if baixas >= 5 and soma_corpos < 0: return 'PUT', forca
        return 'NEUTRO', forca

# ═══════════════════════════════════════════
# 🧠 CÉREBRO IA TRADER (EXIGÊNCIA REDUZIDA)
# ═══════════════════════════════════════════
class CerebroIA:
    def __init__(self):
        self.olhos = OlhosNasVelas()
        self.pesos = {'mortalha': 1.0, 'formiga': 1.0, 'fortaleza': 1.0, 'raio_negro': 1.0, 'tsunami': 1.0}
        self.historico_est = {n: {'wins': 0, 'total': 0} for n in self.pesos}
        self.ops_totais = 0; self.ops_vencidas = 0
        self.score_minimo = 48
        self.modo_agressivo = True
    
    def aprender(self, detalhes, resultado):
        self.ops_totais += 1
        if 'WIN' in resultado: self.ops_vencidas += 1
        for nome in self.pesos:
            if nome in detalhes and '⚠️' not in str(detalhes[nome]) and '⏸️' not in str(detalhes[nome]):
                self.historico_est[nome]['total'] += 1
                if 'WIN' in resultado: self.historico_est[nome]['wins'] += 1
                t = self.historico_est[nome]['total']; w = self.historico_est[nome]['wins']
                if t >= 3: self.pesos[nome] = 0.5 + (w / t)
        if self.ops_totais >= 10:
            taxa = self.ops_vencidas / self.ops_totais
            self.score_minimo = 45 if taxa > 0.90 else (55 if taxa < 0.75 else 48)
            self.modo_agressivo = taxa > 0.85
    
    def avaliar(self, sinal, velas):
        direcao = sinal.get('direcao'); ativo = sinal.get('ativo', '')
        nota_visual, motivo_visual = self.olhos.analisar(velas, direcao)
        if nota_visual < 25: return False, 0, [f"👁️ Visual ruim ({nota_visual})"]
        
        fluxo, forca = self.olhos.fluxo_visual(velas)
        if fluxo != 'NEUTRO' and fluxo != direcao and forca >= 0.80:
            return False, 0, [f"🌊 Contra fluxo {fluxo}"]
        
        score = 0; motivos = []
        conf = sinal.get('confianca', 0); score += (conf / 100) * 30
        est = sinal.get('estrategias', 0); score += (est / 5) * 20
        if est >= 3: motivos.append(f"{est}/5 estratégias")
        score += (nota_visual / 100) * 20; motivos.append(f"👁️ {motivo_visual}")
        if fluxo == direcao: score += int(forca * 15)
        hora = datetime.now(FUSO_BR).hour
        if 6 <= hora <= 23: score += 10
        if self.ops_totais >= 5 and (self.ops_vencidas/max(self.ops_totais,1)) > 0.75: score += 5
        if est >= 4: score += 5
        
        aprovado = score >= self.score_minimo
        return aprovado, score, motivos

# ═══════════════════════════════════════════
# ⚛️ QUANTUM IA
# ═══════════════════════════════════════════
class QuantumIA:
    def __init__(self):
        self.e1 = E1_Mortalha(); self.e2 = E2_Formiga(); self.e3 = E3_Fortaleza()
        self.e4 = E4_RaioNegro(); self.e5 = E5_Tsunami()
        self.cerebro = CerebroIA()
        self.min_confirmacoes = 3; self.confianca_minima = 48
        
    def analisar(self, v):
        if len(v) < 30: return None, 0, 0, {}
        votos = {'CALL': 0, 'PUT': 0}; confiancas = {'CALL': [], 'PUT': []}; detalhes = {}
        estrategias = [
            ('mortalha', self.e1), ('formiga', self.e2), ('fortaleza', self.e3),
            ('raio_negro', self.e4), ('tsunami', self.e5)
        ]
        for nome, est in estrategias:
            try:
                d, c = est.analisar(v)
                if d and c >= self.confianca_minima:
                    votos[d] += self.cerebro.pesos.get(nome, 1.0)
                    confiancas[d].append(c); detalhes[nome] = f"{d} {c:.0f}%"
                elif d: detalhes[nome] = f"{d} {c:.0f}% ⚠️"
                else: detalhes[nome] = "⏸️"
            except: detalhes[nome] = "❌"
        
        tc, tp = votos['CALL'], votos['PUT']
        total_vot = sum(1 for v in detalhes.values() if '⚠️' not in str(v) and '⏸️' not in str(v) and '❌' not in str(v))
        
        if tc >= self.min_confirmacoes and tc > tp:
            conf = np.mean(confiancas['CALL']); return 'CALL', min(conf+(tc-2)*4,95), total_vot, detalhes
        if tp >= self.min_confirmacoes and tp > tc:
            conf = np.mean(confiancas['PUT']); return 'PUT', min(conf+(tp-2)*4,95), total_vot, detalhes
        return None, 0, total_vot, detalhes
    
    def melhor_par(self, velas_dict, bloqueados, stats_pares):
        self.cerebro.stats_pares = stats_pares
        melhor = None; melhor_score = 0
        for nome, velas in velas_dict.items():
            if nome in bloqueados: continue
            if nome in stats_pares and stats_pares[nome]['total'] >= 5:
                if stats_pares[nome]['taxa'] < 50: continue
            if len(velas) >= 30:
                d, cf, num, det = self.analisar(velas)
                if d:
                    sinal_temp = {'direcao': d, 'confianca': cf, 'estrategias': num, 'detalhes': det, 'ativo': nome}
                    aprovado, score, motivos = self.cerebro.avaliar(sinal_temp, velas)
                    if aprovado:
                        fs = cf + (num*5) + (score*0.3)
                        if nome in stats_pares and stats_pares[nome]['total'] >= 5: fs += stats_pares[nome]['taxa']*0.2
                        if fs > melhor_score: melhor_score = fs; melhor = {'ativo': nome, 'direcao': d, 'confianca': cf, 'estrategias': num, 'detalhes': det, 'score_ia': score}
        return melhor

# ═══════════════════════════════════════════
# CATÁLOGO DE PARES
# ═══════════════════════════════════════════
class CatalogoPares:
    def __init__(self): self.stats = {nome: {'wins': 0, 'losses': 0, 'total': 0, 'taxa': 0} for nome in ATIVOS_OTC}
    def atualizar(self, ativo, resultado):
        if ativo in self.stats:
            self.stats[ativo]['total'] += 1
            if resultado == 'win': self.stats[ativo]['wins'] += 1
            else: self.stats[ativo]['losses'] += 1
            t = self.stats[ativo]['total']; w = self.stats[ativo]['wins']
            self.stats[ativo]['taxa'] = round((w/t)*100,1) if t>0 else 0

# ═══════════════════════════════════════════
# IQ API
# ═══════════════════════════════════════════
class IQAPI:
    def __init__(self, e, s, a): self.e=e; self.s=s; self.a=a; self.api=None; self.velas={nome:deque(maxlen=100) for nome in a}; self.ok=False; self.erros=0
    def conectar(self):
        for t in range(5):
            try:
                if self.api:
                    try: self.api.close()
                    except: pass
                    time.sleep(2)
                self.api = IQ_Option(self.e, self.s); ok, _ = self.api.connect()
                if ok: self.ok=True; self.erros=0; return True
                time.sleep(5*(t+1))
            except: time.sleep(5*(t+1))
        self.ok=False; return False
    def obter(self, ativo_id, qtd=80):
        for retry in range(3):
            if not self.ok and not self.conectar(): return 0
            try:
                c = self.api.get_candles(ativo_id, 60, qtd, time.time())
                if c and len(c)>0:
                    nome = [k for k,v in self.a.items() if v==ativo_id][0]; self.velas[nome].clear()
                    for x in c[-qtd:]:
                        if isinstance(x, dict):
                            try: self.velas[nome].append({'time':datetime.fromtimestamp(x.get('from',0),FUSO_BR),'open':float(x['open']),'high':float(x['max']),'low':float(x['min']),'close':float(x['close']),'volume':int(x.get('volume',0))})
                            except: pass
                    return len(c)
            except:
                self.ok=False
                if retry<2: time.sleep(3); continue
        return 0
    def atualizar(self):
        if not self.ok: self.conectar()
        for n,i in self.a.items():
            try: self.obter(i)
            except: pass

# ═══════════════════════════════════════════
# BOT
# ═══════════════════════════════════════════
class Bot:
    def __init__(self):
        self.tg=Telegram(TOKEN,CHAT); self.m=QuantumIA(); self.p=Placar(); self.iq=IQAPI(EMAIL,SENHA,ATIVOS_OTC)
        self.catalogo=CatalogoPares(); self.op=False; self.g=0; self.ult=0; self.sinais=0
        self.ultimo_sinal_ativo={}; self.intervalo_minimo=180
        self.ultimo_dia=datetime.now(FUSO_BR).day; self.placar_enviado=False

    def pode_enviar(self, ativo):
        agora=time.time()
        if ativo in self.ultimo_sinal_ativo:
            if agora-self.ultimo_sinal_ativo[ativo]<self.intervalo_minimo: return False
        return True
    def registrar_envio(self, ativo): self.ultimo_sinal_ativo[ativo]=time.time()
    def _barra(self, pct): p=int(pct/10); return '█'*p+'░'*(10-p)

    def fechar_dia(self):
        agora=datetime.now(FUSO_BR); data=agora.strftime('%d/%m/%Y')
        dias={'Monday':'Segunda','Tuesday':'Terça','Wednesday':'Quarta','Thursday':'Quinta','Friday':'Sexta','Saturday':'Sábado','Sunday':'Domingo'}
        dia=dias.get(agora.strftime('%A'),'')
        w=self.p.w; g1=self.p.g1; l=self.p.l; total=max(w+l,1); tx=round((w/total)*100,1)
        lucro=round(w*1.6+g1*0.4-l*5,2)
        msg=f"""📊 *PLACAR DIÁRIO FINALIZADO*

🗓️ *{data} ({dia})*
⏰ {agora.strftime('%H:%M')}

┌──────────────────────────┐
│ ⚛️ QUANTUM IA 3.0       │
│ 🟢 Wins: {w}              │
│ 🟡 Gale 1: {g1}            │
│ 🔴 Losses: {l}            │
│ 📨 Sinais: {w+g1+l}       │
│ 🎯 Assertividade: {tx}%   │
│ [{self._barra(tx)}]      │
│ 💰 Lucro: +R${lucro}      │
└──────────────────────────┘

🔄 *Placar zerado!*"""
        self.tg.send(msg)
        print(f"\n{C.GOLD}╔══════════════════════════════╗{C.E}")
        print(f"{C.GOLD}║ 📊 PLACAR DIÁRIO FINALIZADO ║{C.E}")
        print(f"{C.GOLD}║ 🗓️ {data} ({dia})     ║{C.E}")
        print(f"{C.GOLD}║ 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}% 💰+R${lucro} ║{C.E}")
        print(f"{C.GOLD}╚══════════════════════════════╝{C.E}\n")
        self.p.zerar(); self.sinais=0
        print(f"  {C.G}🔄 Placar ZERADO! Novo dia!{C.E}\n")

    def fmt_sinal(self, s):
        agora=datetime.now(FUSO_BR)
        he=(agora.replace(second=0,microsecond=0)+timedelta(minutes=1)).strftime('%H:%M')
        e="🟢" if s['direcao']=='CALL' else "🔴"
        est=s.get('estrategias',0); score=s.get('score_ia',0)
        return f"""⚛️ SINAL QUANTUM IA ⚛️

⏰ Horário: {he}
💰 Ativo: {s['ativo']}-OTC
📈 Direção: {s['direcao']} {e}
⌛️ Expiração: M1
📊 Confiança: {s['confianca']:.0f}%
🧠 Estratégias: {est}/5
🛡️ Score IA: {score:.0f}/100

⚠️ Entrar somente no horário marcado.
🔄 1 recuperação (Gale 1)!"""

    def fmt_corr(self, r, s):
        return f"""{r}
📊 {s['ativo']}-OTC | {s['direcao']} {'🟢' if s['direcao']=='CALL' else '🔴'}
📊 Placar: 🟢{self.p.w}W 🟡{self.p.g1}G1 🔴{self.p.l}L
🎯 Assertividade: {round((self.p.w/max(self.p.w+self.p.l,1))*100,1)}%"""

    def bateu(self, d, p, v): return v['high']>p if d=='CALL' else v['low']<p

    async def esperar(self, seg=60):
        try:
            agora=datetime.now(FUSO_BR)
            alvo=agora.replace(second=0,microsecond=0)+timedelta(minutes=1)+timedelta(seconds=seg)
            e=max(0,(alvo-agora).total_seconds())
            if e>0: await asyncio.sleep(e)
            self.iq.atualizar()
        except: pass

    async def corrigir(self, sinal):
        at=sinal['ativo']; d=sinal['direcao']
        try:
            await self.esperar(8); v=self.iq.velas[at]
            if len(v)<2: self.op=False; return
            pc=v[-1]['open']; hora=v[-1]['time'].strftime('%H:%M')
            print(f"\n  ⚛️ {at}-OTC {d} | OPEN:{pc:.5f} | Vela:{hora}")
            await self.esperar(5); v=self.iq.velas[at]
            if len(v)>0 and self.bateu(d,pc,v[-1]):
                r=self.p.win(0); print(f"  ✅ {r}"); self.tg.send(self.fmt_corr(r,sinal))
                self.catalogo.atualizar(at,'win'); self.m.cerebro.aprender(sinal.get('detalhes',{}),'WIN'); self.op=False; return
            print(f"  ❌ Principal")
            self.g=1; v=self.iq.velas[at]; pg=v[-1]['open'] if len(v)>0 else pc
            print(f"  🔄 GALE 1 | OPEN:{pg:.5f}"); await self.esperar(5); v=self.iq.velas[at]
            if len(v)>0 and self.bateu(d,pg,v[-1]):
                r=self.p.win(1); print(f"  ✅ {r}"); self.tg.send(self.fmt_corr(r,sinal))
                self.catalogo.atualizar(at,'win'); self.m.cerebro.aprender(sinal.get('detalhes',{}),'WIN GALE 1'); self.op=False; return
            print(f"  ❌ GALE 1"); r=self.p.loss(); print(f"  🔴 {r}"); self.tg.send(self.fmt_corr(r,sinal))
            self.catalogo.atualizar(at,'loss'); self.m.cerebro.aprender(sinal.get('detalhes',{}),'LOSS'); self.op=False
        except Exception as e: print(f"  ❌ {e}"); self.op=False

    async def catalogacao_inicial(self):
        print(f"\n  {C.GOLD}📊 CATALOGAÇÃO INICIAL (80 velas){C.E}")
        print(f"  {C.GOLD}{'─'*50}{C.E}")
        for nome in ATIVOS_OTC:
            velas=self.iq.velas[nome]
            if len(velas)<35: print(f"  {C.Y}⚠️ {nome}: Poucas velas ({len(velas)}){C.E}"); continue
            wins=0; total=0
            for i in range(35,len(velas)-1):
                janela=list(velas)[i-35:i+1]; d,cf,num,det=self.m.analisar(janela)
                if d:
                    total+=1; vela_seguinte=list(velas)[i+1]
                    if self.bateu(d,vela_seguinte['open'],vela_seguinte): wins+=1
            if total>0:
                self.catalogo.stats[nome]['wins']=wins; self.catalogo.stats[nome]['total']=total
                self.catalogo.stats[nome]['taxa']=round((wins/total)*100,1)
                print(f"  {C.G}✅ {nome}: {wins}/{total} acertos ({self.catalogo.stats[nome]['taxa']}%){C.E}")
            else: print(f"  {C.Y}⚠️ {nome}: Nenhum sinal encontrado{C.E}")
        print(f"  {C.GOLD}{'─'*50}{C.E}")

    async def run(self):
        banner()
        print(f"\n  ⚛️ Iniciando Quantum IA 3.0...\n")
        print(f"  🕐 Horário Brasil: {datetime.now(FUSO_BR).strftime('%H:%M:%S')}\n")
        if not self.iq.conectar(): print(f"  ❌ Falha conexão!"); return
        self.iq.atualizar(); await self.catalogacao_inicial()
        self.ultimo_dia=datetime.now(FUSO_BR).day
        print(f"\n  ✅ QUANTUM IA 3.0 | 🧠 IA + 👁️ Visão + 🌊 Fluxo | 3/5 Entra | Gale 1\n")
        self.tg.send(f"⚛️ *QUANTUM IA 3.0*\n🧠 Cérebro IA Trader\n👁️ Olhos nas Velas\n🌊 Fluxo Visual\n🏆 5 Estratégias\n⏰ {datetime.now(FUSO_BR).strftime('%H:%M:%S')}")

        while True:
            try:
                agora=datetime.now(FUSO_BR)
                if agora.hour==23 and agora.minute==59 and not self.placar_enviado: self.fechar_dia(); self.placar_enviado=True
                if agora.day!=self.ultimo_dia: self.ultimo_dia=agora.day; self.placar_enviado=False
                if agora.second in [0,30]:
                    try: self.iq.atualizar()
                    except: self.iq.ok=False
                if not self.op:
                    try:
                        bloqueados=[a for a in ATIVOS_OTC if not self.pode_enviar(a)]
                        sinal=self.m.melhor_par(self.iq.velas,bloqueados,self.catalogo.stats)
                        if sinal and time.time()-self.ult>25:
                            self.op=True; self.sinais+=1; self.registrar_envio(sinal['ativo'])
                            he=(agora.replace(second=0,microsecond=0)+timedelta(minutes=1)).strftime('%H:%M')
                            print(f"\n⚛️ #{self.sinais} {sinal['ativo']}-OTC {sinal['direcao']} | {sinal['confianca']:.0f}% | {sinal.get('estrategias',0)}/5 | 🛡️{sinal.get('score_ia',0):.0f}/100 | ⏰ {he}")
                            self.tg.send(self.fmt_sinal(sinal)); self.ult=time.time()
                            asyncio.create_task(self.corrigir(sinal))
                    except: pass
                if agora.second in [0,30]:
                    try:
                        w,l,g1=self.p.w,self.p.l,self.p.g1; t=max(w+l,1); tx=round((w/t)*100,1)
                        lucro=round(w*1.6+g1*0.4-l*5,2)
                        stats_str=" | ".join([f"{n}:{self.catalogo.stats[n]['taxa']}%" for n in ATIVOS_OTC])
                        print(f"{C.GOLD}┌──────────────────────────────────────────────────────────┐{C.E}")
                        print(f"{C.GOLD}│{C.E} ⏰ {agora.strftime('%H:%M:%S')} | 📨{self.sinais} | 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}% | 💰+R${lucro}")
                        print(f"{C.GOLD}│{C.E} 📊 {stats_str}")
                        print(f"{C.GOLD}│{C.E} 🧠 Score mín: {self.m.cerebro.score_minimo} | {'⚡Agr' if self.m.cerebro.modo_agressivo else '🛡️Def'}")
                        print(f"{C.GOLD}└──────────────────────────────────────────────────────────┘{C.E}")
                    except: pass
                await asyncio.sleep(3)
            except KeyboardInterrupt:
                clear(); w,l,g1=self.p.w,self.p.l,self.p.g1; t=max(w+l,1); tx=round((w/t)*100,1)
                lucro=round(w*1.6+g1*0.4-l*5,2)
                print(f"\n👋 🟢{w}W 🟡{g1}G1 🔴{l}L | 🎯{tx}% | 💰+R${lucro} | 📨{self.sinais}\n")
                self.tg.send(f"⚠️ *Desligado*\n🟢{w}W 🟡{g1}G1 🔴{l}L\n🎯{tx}%\n💰+R${lucro}")
                if self.iq.api:
                    try: self.iq.api.close()
                    except: pass
                break
            except Exception as e:
                print(f"  {C.R}❌ {str(e)[:40]}{C.E}"); self.iq.ok=False; await asyncio.sleep(5)

if __name__=="__main__":
    asyncio.run(Bot().run())
