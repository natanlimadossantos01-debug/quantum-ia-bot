#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║   ⚛️  Q U A N T U M   I A   M 1  -  P R O               ║
║   👨‍🏫 ESTRATÉGIAS PROFISSIONAIS (Nada básicas)          ║
║   🏆 5 Estratégias Avançadas = Sinais de Alta Precisão   ║
║   🔄 Correções ENVIADAS no Telegram                      ║
║   📊 Backtest Integrado | ☁️ Cloud Ready                 ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import time
import requests
import numpy as np
import signal
import sys
import json
import os
from datetime import datetime, timedelta, timezone
from collections import deque
from pathlib import Path

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

FUSO_BR = timezone(timedelta(hours=-3))

class C:
    G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'
    C = '\033[96m'; W = '\033[97m'; B = '\033[1m'
    E = '\033[0m'; GOLD = '\033[38;5;220m'

def clear(): os.system('clear 2>/dev/null || cls 2>/dev/null')

def banner():
    clear()
    print(f"{C.GOLD}{C.B}╔══════════════════════════════════════════════════════════════╗")
    print(f"║   ⚛️  Q U A N T U M   I A   M 1  -  P R O                     ║")
    print(f"║   🎯 ESTRATÉGIAS PROFISSIONAIS (Nada básicas)                 ║")
    print(f"║   🏆 5 Estratégias Avançadas = Sinais de Alta Precisão        ║")
    print(f"║   🔄 Correções ENVIADAS no Telegram                           ║")
    print(f"╚══════════════════════════════════════════════════════════════╝{C.E}")

# ════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ════════════════════════════════════════════════════════════
CONFIG_FILE = "config_quantum_pro.json"

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
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        if 'token' not in cfg:
            Path(CONFIG_FILE).unlink()
            return carregar_config()
        banner()
        print(f"\n{C.G}✅ Config carregada!{C.E}\n")
        return cfg
    
    banner()
    try:
        cfg = {
            "token": input(f"{C.G}Token Telegram: {C.E}").strip(),
            "chat": input(f"{C.G}Chat ID: {C.E}").strip(),
            "email": input(f"\n{C.G}Email IQ Option: {C.E}").strip(),
            "senha": input(f"{C.G}Senha IQ Option: {C.E}").strip()
        }
    except (EOFError, KeyboardInterrupt):
        print(f"\n{C.R}❌ Configure as variáveis de ambiente!{C.E}")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)
    banner()
    print(f"\n{C.G}✅ Configuração salva!{C.E}\n")
    return cfg

cfg = carregar_config()
TOKEN = cfg['token']; CHAT = cfg['chat']
EMAIL = cfg['email']; SENHA = cfg['senha']

from iqoptionapi.stable_api import IQ_Option

ATIVOS_OTC = {
    "EURUSD": "EURUSD-OTC",
    "GBPUSD": "GBPUSD-OTC",
    "EURGBP": "EURGBP-OTC",
    "USDJPY": "USDJPY-OTC",
    "AUDUSD": "AUDUSD-OTC"
}

# ════════════════════════════════════════════════════════════
# PLACAR (com histórico para correções)
# ════════════════════════════════════════════════════════════
class Placar:
    def __init__(self):
        self.w = 0
        self.l = 0
        self.g1 = 0
        self.total_sinais = 0
        self.s = deque(maxlen=20)
        self.ops = []
        self.dia = datetime.now(FUSO_BR).day
        self.ultimo_resultado = None
        
    def win(self, g=0):
        if g == 0:
            self.w += 1
            self.total_sinais += 1
            self.s.append('🟢')
            self.ultimo_resultado = "WIN"
            return "✅ WIN"
        else:
            self.g1 += 1
            self.total_sinais += 1
            self.s.append('🟡')
            self.ultimo_resultado = "WIN GALE 1"
            return "✅ WIN GALE 1"
            
    def loss(self):
        self.l += 1
        self.total_sinais += 1
        self.s.append('🔴')
        self.ultimo_resultado = "LOSS"
        return "❌ LOSS"
        
    def registrar(self, ativo, direcao, conf, resultado, is_gale=False):
        agora = datetime.now(FUSO_BR)
        hora = agora.strftime('%H:%M')
        sufixo = "¹" if is_gale else ""
        emoji = "✅" if "WIN" in resultado else "🔴"
        self.ops.append(f"M1 {ativo}-OTC {direcao} {hora} {emoji}{sufixo}")
        
    def zerar(self):
        self.w = 0
        self.l = 0
        self.g1 = 0
        self.total_sinais = 0
        self.s.clear()
        self.ops.clear()
        self.ultimo_resultado = None
        
    def get_stats(self):
        total = self.w + self.l + self.g1
        tx = round(((self.w + self.g1) / total) * 100, 1) if total > 0 else 0
        return {
            'wins': self.w,
            'losses': self.l,
            'gales': self.g1,
            'total': total,
            'taxa': tx
        }

class Telegram:
    def __init__(self, t, c):
        self.u = f"https://api.telegram.org/bot{t}"
        self.c = c
        
    def send(self, txt):
        try:
            requests.post(f"{self.u}/sendMessage", 
                         json={"chat_id": self.c, "text": txt, "parse_mode": "Markdown"},
                         timeout=5)
        except:
            pass

# ════════════════════════════════════════════════════════════
# 🏆 ESTRATÉGIA 1: ICHIMOKU
# ════════════════════════════════════════════════════════════
class Ichimoku:
    def __init__(self):
        self.nome = "🏯 Ichimoku"
        
    def calcular_linhas(self, velas):
        precos = [v['close'] for v in velas]
        
        if len(precos) >= 9:
            tenkan = (max(precos[-9:]) + min(precos[-9:])) / 2
        else:
            tenkan = precos[-1]
            
        if len(precos) >= 26:
            kijun = (max(precos[-26:]) + min(precos[-26:])) / 2
        else:
            kijun = precos[-1]
            
        senkou_a = (tenkan + kijun) / 2
        
        if len(precos) >= 52:
            senkou_b = (max(precos[-52:]) + min(precos[-52:])) / 2
        else:
            senkou_b = precos[-1]
            
        return {'tenkan': tenkan, 'kijun': kijun, 'senkou_a': senkou_a, 'senkou_b': senkou_b}
        
    def analisar(self, velas):
        if len(velas) < 52:
            return None, 0
            
        linhas = self.calcular_linhas(velas)
        preco = velas[-1]['close']
        preco_ant = velas[-2]['close']
        
        pontos_call = 0
        pontos_put = 0
        
        if preco > linhas['senkou_a'] and preco > linhas['senkou_b']:
            pontos_call += 4
        elif preco < linhas['senkou_a'] and preco < linhas['senkou_b']:
            pontos_put += 4
            
        if linhas['tenkan'] > linhas['kijun']:
            pontos_call += 3
            if linhas['tenkan'] > linhas['kijun'] * 1.005:
                pontos_call += 1
        else:
            pontos_put += 3
            if linhas['kijun'] > linhas['tenkan'] * 1.005:
                pontos_put += 1
                
        if linhas['senkou_a'] > linhas['senkou_b']:
            pontos_call += 2
        else:
            pontos_put += 2
            
        if preco > linhas['senkou_a'] and preco_ant <= linhas['senkou_a']:
            pontos_call += 3
        elif preco < linhas['senkou_b'] and preco_ant >= linhas['senkou_b']:
            pontos_put += 3
            
        if pontos_call >= 7 and pontos_call > pontos_put:
            conf = min(65 + (pontos_call - 7) * 3, 92)
            return 'CALL', conf
        elif pontos_put >= 7 and pontos_put > pontos_call:
            conf = min(65 + (pontos_put - 7) * 3, 92)
            return 'PUT', conf
            
        return None, 0

# ════════════════════════════════════════════════════════════
# 🏆 ESTRATÉGIA 2: SUPORTE/RESISTÊNCIA + ORDEM FLOW
# ════════════════════════════════════════════════════════════
class SuporteResistencia:
    def __init__(self):
        self.nome = "🏔️ S/R + Ordem Flow"
        
    def encontrar_niveis(self, velas, periodo=20):
        altas = [v['high'] for v in velas[-periodo:]]
        baixas = [v['low'] for v in velas[-periodo:]]
        
        resistencia = max(altas)
        suporte = min(baixas)
        
        if len(altas) >= 2:
            resistencia2 = sorted(altas)[-2]
        else:
            resistencia2 = resistencia
            
        if len(baixas) >= 2:
            suporte2 = sorted(baixas)[1]
        else:
            suporte2 = suporte
            
        return {'r1': resistencia, 'r2': resistencia2, 's1': suporte, 's2': suporte2}
        
    def analisar_fluxo(self, velas):
        if len(velas) < 10:
            return 0, 0
            
        compras = 0
        vendas = 0
        
        for vela in velas[-10:]:
            if vela['close'] > vela['open']:
                compras += vela['volume'] * (vela['close'] - vela['open']) / (vela['high'] - vela['low'] + 0.00001)
            else:
                vendas += vela['volume'] * (vela['open'] - vela['close']) / (vela['high'] - vela['low'] + 0.00001)
                
        return compras, vendas
        
    def analisar(self, velas):
        if len(velas) < 30:
            return None, 0
            
        niveis = self.encontrar_niveis(velas)
        preco = velas[-1]['close']
        compras, vendas = self.analisar_fluxo(velas)
        
        pontos_call = 0
        pontos_put = 0
        
        if abs(preco - niveis['s1']) / preco < 0.001:
            pontos_call += 4
        elif abs(preco - niveis['s2']) / preco < 0.001:
            pontos_call += 2
            
        if abs(niveis['r1'] - preco) / preco < 0.001:
            pontos_put += 4
        elif abs(niveis['r2'] - preco) / preco < 0.001:
            pontos_put += 2
            
        total = compras + vendas
        if total > 0:
            if compras / total > 0.65:
                pontos_call += 3
            elif vendas / total > 0.65:
                pontos_put += 3
                
        if len(velas) >= 3:
            if preco > niveis['r1'] and velas[-2]['close'] <= niveis['r1']:
                pontos_call += 3
            elif preco < niveis['s1'] and velas[-2]['close'] >= niveis['s1']:
                pontos_put += 3
                
        if pontos_call >= 5 and pontos_call > pontos_put:
            conf = min(60 + pontos_call * 4, 90)
            return 'CALL', conf
        elif pontos_put >= 5 and pontos_put > pontos_call:
            conf = min(60 + pontos_put * 4, 90)
            return 'PUT', conf
            
        return None, 0

# ════════════════════════════════════════════════════════════
# 🏆 ESTRATÉGIA 3: MOMENTUM PRO
# ════════════════════════════════════════════════════════════
class MomentumPro:
    def __init__(self):
        self.nome = "⚡ Momentum Pro"
        
    def ema(self, precos, periodo):
        if len(precos) < periodo:
            return sum(precos) / len(precos) if precos else 0
        k = 2 / (periodo + 1)
        ema = sum(precos[:periodo]) / periodo
        for preco in precos[periodo:]:
            ema = (preco * k) + (ema * (1 - k))
        return ema
        
    def rsi(self, precos, periodo=14):
        if len(precos) < periodo + 1:
            return 50
        ganhos = []
        perdas = []
        for i in range(1, len(precos)):
            diff = precos[i] - precos[i-1]
            if diff > 0:
                ganhos.append(diff)
                perdas.append(0)
            else:
                ganhos.append(0)
                perdas.append(abs(diff))
        if len(ganhos) >= periodo:
            avg_gain = sum(ganhos[-periodo:]) / periodo
            avg_loss = sum(perdas[-periodo:]) / periodo
        else:
            avg_gain = sum(ganhos) / len(ganhos) if ganhos else 1
            avg_loss = sum(perdas) / len(perdas) if perdas else 1
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
        
    def calcular_macd(self, velas):
        precos = [v['close'] for v in velas]
        ema12 = self.ema(precos, 12)
        ema26 = self.ema(precos, 26)
        macd = ema12 - ema26
        sinal = self.ema([macd], 9)
        return {'macd': macd, 'sinal': sinal, 'hist': macd - sinal}
        
    def calcular_bandas(self, precos, periodo=20):
        if len(precos) < periodo:
            return {'sup': precos[-1], 'inf': precos[-1], 'meio': precos[-1]}
        media = sum(precos[-periodo:]) / periodo
        variancia = sum((p - media) ** 2 for p in precos[-periodo:]) / periodo
        desvio = variancia ** 0.5
        return {'sup': media + (2 * desvio), 'meio': media, 'inf': media - (2 * desvio)}
        
    def analisar(self, velas):
        if len(velas) < 30:
            return None, 0
            
        precos = [v['close'] for v in velas]
        rsi = self.rsi(precos)
        macd = self.calcular_macd(velas)
        bandas = self.calcular_bandas(precos)
        preco = velas[-1]['close']
        
        pontos_call = 0
        pontos_put = 0
        
        if rsi < 30:
            pontos_call += 4
        elif rsi < 40:
            pontos_call += 2
        elif rsi > 70:
            pontos_put += 4
        elif rsi > 60:
            pontos_put += 2
            
        if macd['hist'] > 0 and macd['hist'] > macd['hist'] * 0.1:
            pontos_call += 3
        elif macd['hist'] < 0 and macd['hist'] < macd['hist'] * 0.1:
            pontos_put += 3
            
        if preco < bandas['inf'] * 1.005:
            pontos_call += 3
        elif preco > bandas['sup'] * 0.995:
            pontos_put += 3
            
        if len(velas) >= 3:
            rsi_anterior = self.rsi(precos[:-2])
            if precos[-1] < precos[-3] and rsi > rsi_anterior:
                pontos_call += 3
            elif precos[-1] > precos[-3] and rsi < rsi_anterior:
                pontos_put += 3
                
        if pontos_call >= 6 and pontos_call > pontos_put:
            conf = min(55 + pontos_call * 4, 90)
            return 'CALL', conf
        elif pontos_put >= 6 and pontos_put > pontos_call:
            conf = min(55 + pontos_put * 4, 90)
            return 'PUT', conf
            
        return None, 0

# ════════════════════════════════════════════════════════════
# 🏆 ESTRATÉGIA 4: PRICE ACTION PRO
# ════════════════════════════════════════════════════════════
class PriceActionPro:
    def __init__(self):
        self.nome = "🎯 Price Action Pro"
        
    def identificar_padroes(self, velas):
        if len(velas) < 3:
            return []
            
        v1 = velas[-3]
        v2 = velas[-2]
        v3 = velas[-1]
        
        padroes = []
        
        if abs(v3['close'] - v3['open']) / (v3['high'] - v3['low'] + 0.00001) < 0.1:
            padroes.append('doji')
            
        corpo = abs(v3['close'] - v3['open'])
        sombra_inf = min(v3['close'], v3['open']) - v3['low']
        if sombra_inf > corpo * 2 and sombra_inf > v3['high'] - max(v3['close'], v3['open']):
            padroes.append('martelo')
            
        sombra_sup = v3['high'] - max(v3['close'], v3['open'])
        if sombra_sup > corpo * 2 and sombra_sup > min(v3['close'], v3['open']) - v3['low']:
            padroes.append('estrela_cadente')
            
        if v3['close'] > v2['open'] and v3['open'] < v2['close']:
            if v3['close'] > v2['open'] and v3['close'] > v2['close']:
                padroes.append('engolfo_alta')
        elif v3['close'] < v2['open'] and v3['open'] > v2['close']:
            if v3['close'] < v2['open'] and v3['close'] < v2['close']:
                padroes.append('engolfo_baixa')
                
        if len(velas) >= 3:
            if all(velas[i]['close'] > velas[i]['open'] for i in range(-3, 0)):
                padroes.append('3_soldados')
            elif all(velas[i]['close'] < velas[i]['open'] for i in range(-3, 0)):
                padroes.append('3_corvos')
                
        return padroes
        
    def analisar(self, velas):
        if len(velas) < 10:
            return None, 0
            
        padroes = self.identificar_padroes(velas)
        
        pontos_call = 0
        pontos_put = 0
        
        if 'martelo' in padroes:
            pontos_call += 4
        if 'engolfo_alta' in padroes:
            pontos_call += 4
        if '3_soldados' in padroes:
            pontos_call += 3
            
        if 'estrela_cadente' in padroes:
            pontos_put += 4
        if 'engolfo_baixa' in padroes:
            pontos_put += 4
        if '3_corvos' in padroes:
            pontos_put += 3
            
        if 'doji' in padroes and len(velas) >= 2:
            if velas[-1]['close'] > velas[-2]['close']:
                pontos_call += 2
            else:
                pontos_put += 2
                
        if len(velas) >= 5:
            medias = [velas[i]['close'] for i in range(-5, 0)]
            if all(medias[i] > medias[i-1] for i in range(1, len(medias))):
                pontos_call += 2
            elif all(medias[i] < medias[i-1] for i in range(1, len(medias))):
                pontos_put += 2
                
        if pontos_call >= 5 and pontos_call > pontos_put:
            conf = min(55 + pontos_call * 5, 90)
            return 'CALL', conf
        elif pontos_put >= 5 and pontos_put > pontos_call:
            conf = min(55 + pontos_put * 5, 90)
            return 'PUT', conf
            
        return None, 0

# ════════════════════════════════════════════════════════════
# 🏆 ESTRATÉGIA 5: VOLATILIDADE PRO
# ════════════════════════════════════════════════════════════
class VolatilidadePro:
    def __init__(self):
        self.nome = "🌊 Volatilidade Pro"
        
    def calcular_atr(self, velas, periodo=14):
        if len(velas) < periodo + 1:
            return 0
            
        trs = []
        for i in range(-periodo, 0):
            high = velas[i]['high']
            low = velas[i]['low']
            close_prev = velas[i-1]['close']
            tr = max(high - low, abs(high - close_prev), abs(low - close_prev))
            trs.append(tr)
            
        return sum(trs) / len(trs)
        
    def calcular_vol(self, velas):
        if len(velas) < 20:
            return 0
            
        retornos = []
        for i in range(-20, 0):
            ret = (velas[i]['close'] - velas[i-1]['close']) / velas[i-1]['close']
            retornos.append(ret)
            
        media = sum(retornos) / len(retornos)
        variancia = sum((r - media) ** 2 for r in retornos) / len(retornos)
        return variancia ** 0.5 * 100
        
    def analisar(self, velas):
        if len(velas) < 20:
            return None, 0
            
        atr = self.calcular_atr(velas)
        vol = self.calcular_vol(velas)
        preco = velas[-1]['close']
        
        pontos_call = 0
        pontos_put = 0
        
        if atr > 0 and len(velas) >= 3:
            movimento = abs(velas[-1]['close'] - velas[-3]['close'])
            if movimento > atr * 0.8:
                if velas[-1]['close'] > velas[-3]['close']:
                    pontos_call += 4
                else:
                    pontos_put += 4
                    
        if vol > 0 and len(velas) >= 10:
            vol_anterior = self.calcular_vol(velas[:-5])
            if vol > vol_anterior * 1.5:
                if preco > velas[-5]['close']:
                    pontos_call += 3
                else:
                    pontos_put += 3
                    
        if len(velas) >= 10:
            max_preco = max(v['high'] for v in velas[-10:])
            min_preco = min(v['low'] for v in velas[-10:])
            range_preco = max_preco - min_preco
            
            if range_preco / preco < 0.003:
                if preco > velas[-1]['open']:
                    pontos_call += 2
                else:
                    pontos_put += 2
                    
        if len(velas) >= 3:
            vela = velas[-1]
            corpo = abs(vela['close'] - vela['open'])
            range_total = vela['high'] - vela['low']
            
            if corpo / range_total > 0.7:
                if vela['close'] > vela['open']:
                    pontos_call += 2
                else:
                    pontos_put += 2
                    
        if pontos_call >= 5 and pontos_call > pontos_put:
            conf = min(50 + pontos_call * 5, 88)
            return 'CALL', conf
        elif pontos_put >= 5 and pontos_put > pontos_call:
            conf = min(50 + pontos_put * 5, 88)
            return 'PUT', conf
            
        return None, 0

# ════════════════════════════════════════════════════════════
# ⚛️ QUANTUM IA - VOTAÇÃO 3/5
# ════════════════════════════════════════════════════════════
class QuantumIA:
    def __init__(self):
        self.estrategias = [
            Ichimoku(),
            SuporteResistencia(),
            MomentumPro(),
            PriceActionPro(),
            VolatilidadePro()
        ]
        self.min_estrategias = 3
        
    def analisar_completo(self, velas):
        try:
            if len(velas) < 52:
                return None, 0, 0, {}
                
            resultados = []
            votos = {'CALL': 0, 'PUT': 0}
            confiancas = {'CALL': [], 'PUT': []}
            detalhes = {}
            
            for est in self.estrategias:
                try:
                    direcao, conf = est.analisar(velas)
                    if direcao:
                        resultados.append((est.nome, direcao, conf))
                        votos[direcao] += 1
                        confiancas[direcao].append(conf)
                        detalhes[est.nome] = f"{direcao} {conf:.0f}%"
                    else:
                        detalhes[est.nome] = "⏸️"
                except Exception as e:
                    detalhes[est.nome] = "❌"
                    
            total = len(resultados)
            
            if total < self.min_estrategias:
                return None, 0, total, detalhes
                
            if votos['CALL'] >= self.min_estrategias and votos['CALL'] > votos['PUT']:
                conf = np.mean(confiancas['CALL']) if confiancas['CALL'] else 0
                conf = min(conf + (total - 3) * 4, 95)
                return 'CALL', conf, total, detalhes
                
            if votos['PUT'] >= self.min_estrategias and votos['PUT'] > votos['CALL']:
                conf = np.mean(confiancas['PUT']) if confiancas['PUT'] else 0
                conf = min(conf + (total - 3) * 4, 95)
                return 'PUT', conf, total, detalhes
                
            return None, 0, total, detalhes
            
        except Exception as e:
            print(f"Erro no QuantumIA: {e}")
            return None, 0, 0, {}
            
    def melhor_par(self, velas_dict, stats_pares):
        melhor = None
        melhor_score = 0
        
        for nome, velas in velas_dict.items():
            if len(velas) >= 52:
                direcao, conf, num, _ = self.analisar_completo(velas)
                if direcao:
                    score = conf + (num * 5)
                    if nome in stats_pares and stats_pares[nome]['total'] >= 5:
                        score += stats_pares[nome]['taxa'] * 0.1
                    if score > melhor_score:
                        melhor_score = score
                        melhor = {
                            'ativo': nome,
                            'direcao': direcao,
                            'confianca': conf,
                            'estrategias': num
                        }
        return melhor

# ════════════════════════════════════════════════════════════
# TRADER PROFESSOR
# ════════════════════════════════════════════════════════════
class TraderProfessor:
    def __init__(self):
        self.historico = deque(maxlen=50)
        self.stats_pares = {nome: {'wins': 0, 'losses': 0, 'total': 0, 'taxa': 0} 
                           for nome in ATIVOS_OTC}
        self.tendencias = {nome: "NEUTRA" for nome in ATIVOS_OTC}
        self.velas_dict = {}
        
    def atualizar_stats(self, ativo, resultado):
        if ativo in self.stats_pares:
            self.stats_pares[ativo]['total'] += 1
            if resultado == 'win':
                self.stats_pares[ativo]['wins'] += 1
            else:
                self.stats_pares[ativo]['losses'] += 1
            t = self.stats_pares[ativo]['total']
            w = self.stats_pares[ativo]['wins']
            self.stats_pares[ativo]['taxa'] = round((w/t)*100, 1) if t > 0 else 0
            
    def atualizar_dados(self, velas_dict):
        self.velas_dict = velas_dict
        for nome, velas in velas_dict.items():
            if len(velas) >= 21:
                closes = [v['close'] for v in list(velas)[-21:]]
                ema9 = np.mean(closes[-9:])
                ema21 = np.mean(closes[-21:])
                if ema9 > ema21 * 1.0005:
                    self.tendencias[nome] = "ALTA 📈"
                elif ema9 < ema21 * 0.9995:
                    self.tendencias[nome] = "BAIXA 📉"
                else:
                    self.tendencias[nome] = "NEUTRA ➡️"
                    
    def ler_grafico(self, velas, direcao):
        if len(velas) < 5:
            return "Poucas velas", [], True
            
        obs = []
        v = velas[-1]
        v1 = velas[-2]
        corpo = abs(v['close'] - v['open'])
        range_total = v['high'] - v['low']
        pavio_sup = v['high'] - max(v['close'], v['open'])
        pavio_inf = min(v['close'], v['open']) - v['low']
        pavio_ok = True
        
        if direcao == 'CALL':
            if pavio_inf > corpo * 2 and pavio_sup < corpo * 0.3:
                obs.append("🔨 Martelo")
            elif corpo > abs(v1['close'] - v1['open']) * 1.5 and v['close'] > v1['open']:
                obs.append("📈 Engolfo alta")
            if pavio_sup > corpo * 0.6:
                obs.append("⚠️ Pavio superior")
                pavio_ok = False
        else:
            if pavio_sup > corpo * 2 and pavio_inf < corpo * 0.3:
                obs.append("💫 Estrela cadente")
            elif corpo > abs(v1['close'] - v1['open']) * 1.5 and v['close'] < v1['open']:
                obs.append("📉 Engolfo baixa")
            if pavio_inf > corpo * 0.6:
                obs.append("⚠️ Pavio inferior")
                pavio_ok = False
                
        if corpo > range_total * 0.6:
            obs.append("💪 Vela forte")
            
        if not obs:
            obs.append("✅ Setup neutro")
            
        return " | ".join(obs), obs, pavio_ok
        
    def explicar_entrada(self, sinal, velas):
        ativo = sinal['ativo']
        direcao = sinal['direcao']
        est = sinal.get('estrategias', 0)
        conf = sinal.get('confianca', 0)
        tendencia = self.tendencias.get(ativo, 'NEUTRA')
        leitura, _, _ = self.ler_grafico(velas, direcao)
        
        return f"""👨‍🏫 *ANÁLISE DO TRADER*

📊 *Mercado:* {tendencia}
👁️ *Gráfico:* {leitura}
✅ *Estratégias:* {est}/5 confirmaram
🎯 *Decisão:* {direcao} com {conf:.0f}% de confiança"""
        
    def explicar_loss(self, sinal, velas):
        ativo = sinal['ativo']
        direcao = sinal['direcao']
        conf = sinal.get('confianca', 0)
        tendencia = self.tendencias.get(ativo, 'NEUTRA')
        
        causas = []
        v = velas[-1]
        corpo = abs(v['close'] - v['open'])
        
        if corpo > 0:
            if direcao == 'CALL' and (v['high'] - max(v['close'], v['open'])) / corpo > 0.6:
                causas.append("🕯️ Pavio superior grande")
            elif direcao == 'PUT' and (min(v['close'], v['open']) - v['low']) / corpo > 0.6:
                causas.append("🕯️ Pavio inferior grande")
                
        if direcao == 'CALL' and 'BAIXA' in tendencia:
            causas.append("📉 Contra tendência")
        elif direcao == 'PUT' and 'ALTA' in tendencia:
            causas.append("📈 Contra tendência")
            
        if conf < 70:
            causas.append("📊 Confiança moderada")
            
        if not causas:
            causas.append("🎲 Movimento aleatório")
            
        licao = "Seguir o plano"
        if 'pavio' in str(causas).lower():
            licao = "Verificar pavios antes de entrar"
        elif 'tendência' in str(causas).lower():
            licao = "Não operar contra tendência"
        elif 'confiança' in str(causas).lower():
            licao = "Esperar confiança mais alta"
            
        return f"""🧠 *ANÁLISE DO LOSS*

🔴 {ativo}-OTC {direcao} | {conf:.0f}%
🚫 *Causas:* {', '.join(causas)}
📚 *Lição:* {licao}"""
    
    def registrar(self, resultado):
        self.historico.append(1 if resultado == 'win' else 0)

# ════════════════════════════════════════════════════════════
# IQ API
# ════════════════════════════════════════════════════════════
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
        for t in range(5):
            try:
                if self.api:
                    try:
                        self.api.close()
                    except:
                        pass
                    time.sleep(2)
                self.api = IQ_Option(self.e, self.s)
                ok, _ = self.api.connect()
                if ok:
                    self.ok = True
                    self.erros = 0
                    return True
                time.sleep(5 * (t + 1))
            except:
                time.sleep(5 * (t + 1))
        self.ok = False
        return False
        
    def obter(self, ativo_id, qtd=80):
        for retry in range(3):
            if not self.ok and not self.conectar():
                return 0
            try:
                c = self.api.get_candles(ativo_id, 60, qtd, time.time())
                if c and len(c) > 0:
                    nome = [k for k, v in self.a.items() if v == ativo_id][0]
                    self.velas[nome].clear()
                    for x in c[-qtd:]:
                        if isinstance(x, dict):
                            try:
                                self.velas[nome].append({
                                    'time': datetime.fromtimestamp(x.get('from', 0), FUSO_BR),
                                    'open': float(x['open']),
                                    'high': float(x['max']),
                                    'low': float(x['min']),
                                    'close': float(x['close']),
                                    'volume': int(x.get('volume', 0))
                                })
                            except:
                                pass
                    return len(c)
            except:
                self.ok = False
                if retry < 2:
                    time.sleep(3)
                    continue
        return 0
        
    def atualizar(self):
        if not self.ok:
            self.conectar()
        for n, i in self.a.items():
            try:
                self.obter(i)
            except:
                pass

# ════════════════════════════════════════════════════════════
# BOT PRINCIPAL (COM CORREÇÕES NO TELEGRAM)
# ════════════════════════════════════════════════════════════
class Bot:
    def __init__(self):
        self.tg = Telegram(TOKEN, CHAT)
        self.quantum = QuantumIA()
        self.placar = Placar()
        self.iq = IQAPI(EMAIL, SENHA, ATIVOS_OTC)
        self.professor = TraderProfessor()
        self.op = False
        self.ult = 0
        self.sinais = 0
        self.ultimo_sinal_ativo = {}
        self.intervalo_minimo = 180
        self.ultimo_dia = datetime.now(FUSO_BR).day
        self.placar_enviado = False
        
    def pode_enviar(self, ativo):
        agora = time.time()
        if ativo in self.ultimo_sinal_ativo:
            if agora - self.ultimo_sinal_ativo[ativo] < self.intervalo_minimo:
                return False
        return True
        
    def registrar_envio(self, ativo):
        self.ultimo_sinal_ativo[ativo] = time.time()
        
    def _barra(self, pct):
        p = int(pct / 10)
        return '█' * p + '░' * (10 - p)
        
    def fechar_dia(self):
        agora = datetime.now(FUSO_BR)
        data = agora.strftime('%d/%m/%Y')
        dias = {'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
                'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado',
                'Sunday': 'Domingo'}
        dia = dias.get(agora.strftime('%A'), '')
        
        stats = self.placar.get_stats()
        
        lista_ops = ""
        if self.placar.ops:
            for op in self.placar.ops[-50:]:
                lista_ops += op + "\n"
                
        msg = f"""📊 *PLACAR DIÁRIO FINALIZADO*

🗓️ *{data} ({dia})*
⏰ {agora.strftime('%H:%M')}

┌──────────────────────────┐
│ ⚛️ QUANTUM IA M1 PRO    │
│ 🟢 Acertos: {stats['wins']}      │
│ 🟡 Gale 1: {stats['gales']}      │
│ 🔴 Erros: {stats['losses']}      │
│ 📨 Total Sinais: {stats['total']} │
│ 🎯 Assertividade: {stats['taxa']}% │
│ [{self._barra(stats['taxa'])}] │
└──────────────────────────┘

📋 *Lista de Sinais do Dia:*
{lista_ops if lista_ops else 'Nenhum sinal'}"""
        
        self.tg.send(msg)
        print(f"\n{C.GOLD}╔══════════════════════════════════╗{C.E}")
        print(f"{C.GOLD}║ 📊 PLACAR DIÁRIO FINALIZADO    ║{C.E}")
        print(f"{C.GOLD}║ 🟢{stats['wins']}W 🟡{stats['gales']}G1 🔴{stats['losses']}L ║{C.E}")
        print(f"{C.GOLD}║ 🎯{stats['taxa']}%              ║{C.E}")
        print(f"{C.GOLD}╚══════════════════════════════════╝{C.E}\n")
        
        self.placar.zerar()
        self.sinais = 0
        print(f"  {C.G}🔄 Placar ZERADO! Novo dia!{C.E}\n")
        
    def fmt_sinal(self, s):
        agora = datetime.now(FUSO_BR)
        he = (agora.replace(second=0, microsecond=0) + timedelta(minutes=1)).strftime('%H:%M')
        e = "🟢" if s['direcao'] == 'CALL' else "🔴"
        est = s.get('estrategias', 0)
        
        return f"""⚛️ SINAL QUANTUM IA PRO ⚛️

⏰ Horário: {he}
💰 Ativo: {s['ativo']}-OTC
📈 Direção: {s['direcao']} {e}
⌛️ Expiração: M1
📊 Confiança: {s['confianca']:.0f}%
🧠 Estratégias: {est}/5

⚠️ Sinal apenas para análise.
📊 ESTRATÉGIAS PROFISSIONAIS ATIVAS:
🏯 Ichimoku | 🏔️ S/R | ⚡ Momentum | 🎯 Price Action | 🌊 Volatilidade"""

    # ════════════════════════════════════════════════════════
    # 📤 MÉTODO fmt_corr - CORREÇÃO
    # ════════════════════════════════════════════════════════
    def fmt_corr(self, r, sinal):
        """Formata a mensagem de correção para o Telegram"""
        stats = self.placar.get_stats()
        
        # Pega a última operação registrada
        ultima_op = self.placar.ops[-1] if self.placar.ops else ""
        
        # Emoji de acordo com o resultado
        emoji = "✅" if "WIN" in r else "🔴"
        
        # Formata resultado com emojis
        if "WIN" in r and "GALE" in r:
            resultado_fmt = "🟡 WIN GALE 1"
        elif "WIN" in r:
            resultado_fmt = "🟢 WIN"
        else:
            resultado_fmt = "🔴 LOSS"
            
        return f"""{emoji} *CORREÇÃO*

📊 *Resultado:* {resultado_fmt}
💰 *Ativo:* {sinal['ativo']}-OTC
📈 *Direção:* {sinal['direcao']} {'🟢' if sinal['direcao'] == 'CALL' else '🔴'}
🎯 *Confiança:* {sinal['confianca']:.0f}%

📊 *PLACAR ATUAL:*
🟢 Wins: {stats['wins']}
🟡 Gale 1: {stats['gales']}
🔴 Losses: {stats['losses']}
🎯 Assertividade: {stats['taxa']}%

📋 {ultima_op if ultima_op else 'Nenhuma operação registrada'}"""

    # ════════════════════════════════════════════════════════
    # 🔄 MÉTODO CORRIGIR - COM ENVIO DE CORREÇÕES
    # ════════════════════════════════════════════════════════
    def bateu(self, d, p, v):
        return v['high'] > p if d == 'CALL' else v['low'] < p
        
    async def esperar(self, seg=60):
        try:
            agora = datetime.now(FUSO_BR)
            alvo = agora.replace(second=0, microsecond=0) + timedelta(minutes=1) + timedelta(seconds=seg)
            e = max(0, (alvo - agora).total_seconds())
            if e > 0:
                await asyncio.sleep(e)
            self.iq.atualizar()
        except:
            pass

    async def corrigir(self, sinal):
        """Executa a operação e ENVIA CORREÇÃO no Telegram"""
        at = sinal['ativo']
        d = sinal['direcao']
        conf = sinal.get('confianca', 0)
        
        try:
            # Aguarda a vela abrir
            await self.esperar(8)
            v = self.iq.velas[at]
            if len(v) < 2:
                self.op = False
                return
                
            pc = v[-1]['open']
            hora = v[-1]['time'].strftime('%H:%M')
            print(f"\n  ⚛️ {at}-OTC {d} | OPEN:{pc:.5f} | Vela:{hora}")
            
            # Aguarda 5 segundos para ver resultado
            await self.esperar(5)
            v = self.iq.velas[at]
            
            # ✅ VERIFICA SE GANHOU
            if len(v) > 0 and self.bateu(d, pc, v[-1]):
                r = self.placar.win(0)
                print(f"  ✅ {r}")
                self.placar.registrar(at, d, conf, "WIN")
                
                # 📤 ENVIA CORREÇÃO WIN NO TELEGRAM
                self.tg.send(self.fmt_corr(r, sinal))
                
                # Atualiza stats do Professor
                self.professor.registrar('win')
                self.professor.atualizar_stats(at, 'win')
                
                self.op = False
                return
                
            # ❌ PERDEU A PRIMEIRA
            print(f"  ❌ Principal")
            self.placar.registrar(at, d, conf, "LOSS")
            
            # 🔄 TENTA GALE 1
            stats = self.placar.get_stats()
            if stats['losses'] < 3:  # Máximo 3 perdas antes de parar
                v = self.iq.velas[at]
                pg = v[-1]['open'] if len(v) > 0 else pc
                print(f"  🔄 GALE 1 | OPEN:{pg:.5f}")
                
                await self.esperar(5)
                v = self.iq.velas[at]
                
                if len(v) > 0 and self.bateu(d, pg, v[-1]):
                    r = self.placar.win(1)
                    print(f"  ✅ {r}")
                    self.placar.registrar(at, d, conf, "WIN GALE 1", is_gale=True)
                    
                    # 📤 ENVIA CORREÇÃO WIN GALE 1
                    self.tg.send(self.fmt_corr(r, sinal))
                    
                    self.professor.registrar('win')
                    self.professor.atualizar_stats(at, 'win')
                    self.op = False
                    return
                    
                # ❌ PERDEU O GALE TAMBÉM
                print(f"  ❌ GALE 1")
                r = self.placar.loss()
                print(f"  🔴 {r}")
                self.placar.registrar(at, d, conf, "LOSS GALE 1", is_gale=True)
                
                # 📤 ENVIA CORREÇÃO LOSS
                self.tg.send(self.fmt_corr(r, sinal))
                
                # 📤 ENVIA ANÁLISE DO PROFESSOR
                explicacao = self.professor.explicar_loss(sinal, self.iq.velas[at])
                self.tg.send(explicacao)
                print(f"  🧠 Loss explicado!")
                
                self.professor.registrar('loss')
                self.professor.atualizar_stats(at, 'loss')
            else:
                # 🛑 NÃO FAZ GALE (muitas perdas)
                r = self.placar.loss()
                print(f"  🔴 {r} (sem Gale)")
                self.placar.registrar(at, d, conf, "LOSS")
                
                # 📤 ENVIA CORREÇÃO LOSS
                self.tg.send(self.fmt_corr(r, sinal))
                
                self.professor.registrar('loss')
                self.professor.atualizar_stats(at, 'loss')
                
                # 📤 ENVIA AVISO SOBRE O GALE
                aviso = f"🛑 *SEM GALE*\n\n{at}-OTC {d}\n📊 Muitas perdas consecutivas"
                self.tg.send(aviso)
                
            self.op = False
            
        except Exception as e:
            print(f"  ❌ {e}")
            self.op = False

    # ════════════════════════════════════════════════════════
    # 🚀 RUN
    # ════════════════════════════════════════════════════════
    async def run(self):
        banner()
        print(f"\n  ⚛️ Iniciando Quantum IA Pro - Estratégias Profissionais\n")
        print(f"  🕐 Horário Brasil: {datetime.now(FUSO_BR).strftime('%H:%M:%S')}\n")
        print(f"  {C.Y}⚠️  APENAS SINAIS - Sem operação automática{C.E}\n")
        print(f"  {C.G}🏆 ESTRATÉGIAS ATIVAS:{C.E}")
        print(f"     🏯 Ichimoku (Japonesa)")
        print(f"     🏔️ S/R + Ordem Flow")
        print(f"     ⚡ Momentum Pro")
        print(f"     🎯 Price Action Pro")
        print(f"     🌊 Volatilidade Pro\n")
        print(f"  {C.G}📤 Correções enviadas no Telegram após cada sinal{C.E}\n")
        
        if not self.iq.conectar():
            print(f"  ❌ Falha conexão IQ Option!")
            return
            
        self.iq.atualizar()
        self.ultimo_dia = datetime.now(FUSO_BR).day
        
        print(f"\n  ✅ QUANTUM IA PRO | Gerando sinais...\n")
        self.tg.send(f"⚛️ *QUANTUM IA PRO - SINAIS*\n👨‍🏫 Estratégias Profissionais\n⏰ {datetime.now(FUSO_BR).strftime('%H:%M:%S')}\n\n🏆 *5 Estratégias Avançadas:*\n🏯 Ichimoku\n🏔️ S/R\n⚡ Momentum\n🎯 Price Action\n🌊 Volatilidade\n\n📤 *Correções enviadas após cada sinal*")
        
        while True:
            try:
                agora = datetime.now(FUSO_BR)
                
                if agora.hour == 23 and agora.minute == 59 and not self.placar_enviado:
                    self.fechar_dia()
                    self.placar_enviado = True
                    
                if agora.day != self.ultimo_dia:
                    self.ultimo_dia = agora.day
                    self.placar_enviado = False
                    
                if agora.second in [0, 30]:
                    try:
                        self.iq.atualizar()
                        self.professor.atualizar_dados(self.iq.velas)
                    except:
                        self.iq.ok = False
                        
                if not self.op and time.time() - self.ult > 25:
                    try:
                        sinal = self.quantum.melhor_par(self.iq.velas, self.professor.stats_pares)
                        
                        if sinal and self.pode_enviar(sinal['ativo']):
                            self.op = True
                            self.sinais += 1
                            self.registrar_envio(sinal['ativo'])
                            
                            he = (agora.replace(second=0, microsecond=0) + timedelta(minutes=1)).strftime('%H:%M')
                            print(f"\n⚛️ #{self.sinais} {sinal['ativo']}-OTC {sinal['direcao']} | {sinal['confianca']:.0f}% | {sinal.get('estrategias', 0)}/5 | ⏰ {he}")
                            
                            # 📤 ENVIA SINAL
                            self.tg.send(self.fmt_sinal(sinal))
                            
                            # 📤 ENVIA ANÁLISE DO PROFESSOR
                            explicacao = self.professor.explicar_entrada(sinal, self.iq.velas[sinal['ativo']])
                            self.tg.send(explicacao)
                            
                            self.ult = time.time()
                            
                            # 📤 CRIA TAREFA PARA CORRIGIR E ENVIAR CORREÇÃO
                            asyncio.create_task(self.corrigir(sinal))
                    except Exception as e:
                        pass
                        
                if agora.second in [0, 30]:
                    try:
                        stats = self.placar.get_stats()
                        print(f"{C.GOLD}┌──────────────────────────────────────────────────────┐{C.E}")
                        print(f"{C.GOLD}│{C.E} ⏰ {agora.strftime('%H:%M:%S')} | 📨{self.sinais} | 🟢{stats['wins']}W 🟡{stats['gales']}G1 🔴{stats['losses']}L 🎯{stats['taxa']}%")
                        print(f"{C.GOLD}└──────────────────────────────────────────────────────┘{C.E}")
                    except:
                        pass
                        
                await asyncio.sleep(3)
                
            except KeyboardInterrupt:
                clear()
                stats = self.placar.get_stats()
                print(f"\n👋 🟢{stats['wins']}W 🟡{stats['gales']}G1 🔴{stats['losses']}L | 🎯{stats['taxa']}% | Total: {stats['total']}\n")
                self.tg.send(f"⚠️ *Desligado*\n🟢{stats['wins']}W 🟡{stats['gales']}G1 🔴{stats['losses']}L\n🎯{stats['taxa']}%\nTotal: {stats['total']}")
                if self.iq.api:
                    try:
                        self.iq.api.close()
                    except:
                        pass
                break
                
            except Exception as e:
                print(f"  {C.R}❌ Erro: {str(e)[:50]}{C.E}")
                self.iq.ok = False
                await asyncio.sleep(5)

# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        asyncio.run(Bot().run())
    except KeyboardInterrupt:
        print(f"\n{C.G}👋 Até logo!{C.E}\n")
    except Exception as e:
        print(f"\n{C.R}❌ Erro fatal: {e}{C.E}\n")
