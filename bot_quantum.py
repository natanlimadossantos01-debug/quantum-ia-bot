#!/usr/bin/env python3
"""
⚛️ VDUB FX SNIPER - OTC M5
🎯 Estratégia: EMA Trend + TEMA/DEMA + Supertrend + Hull MA
📊 Score ponderado com múltiplos indicadores
🔄 Gale 1 normal
📡 4 Pares OTC confirmados
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os
from datetime import datetime, timedelta, timezone
from collections import deque
from pathlib import Path

signal.signal(signal.SIGCHLD, signal.SIG_IGN)
FUSO_BR = timezone(timedelta(hours=-3))

# Configurações
INTERVALO_MINIMO = 300       # 5 min entre sinais
USAR_GALE = True
ANTECEDENCIA = 30
SCORE_MINIMO = 55            # Score mínimo para gerar sinal

def banner():
    print("⚛️ VDUB SNIPER - OTC M5")

def carregar_config():
    token = os.environ.get('TELEGRAM_TOKEN')
    chat = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat:
        banner()
        print("✅ Modo CLOUD detectado!")
        return {"token": token, "chat": chat}
    print("❌ Configure TELEGRAM_TOKEN e TELEGRAM_CHAT_ID")
    sys.exit(1)

cfg = carregar_config()
TOKEN, CHAT = cfg['token'], cfg['chat']

ATIVOS_OTC = {
    "EURUSD": "EURUSD-OTC",
    "GBPUSD": "GBPUSD-OTC",
    "EURJPY": "EURJPY-OTC",
    "USDJPY": "USDJPY-OTC"
}

class Telegram:
    def __init__(self, t, c):
        self.url = f"https://api.telegram.org/bot{t}"
        self.c = c
    def send(self, txt):
        try: requests.post(f"{self.url}/sendMessage", json={"chat_id": self.c, "text": txt, "parse_mode": "Markdown"}, timeout=10)
        except: pass

class VdubSniper:
    def __init__(self):
        self.factor = 3
        self.pd = 1
    
    def _ema(self, dados, periodo):
        if len(dados) < periodo:
            return np.mean(dados) if len(dados) > 0 else 0
        alpha = 2 / (periodo + 1)
        ema = dados[0]
        for i in range(1, len(dados)):
            ema = alpha * dados[i] + (1 - alpha) * ema
        return ema
    
    def _wma(self, dados, periodo):
        if len(dados) < periodo:
            return np.mean(dados) if len(dados) > 0 else 0
        pesos = np.arange(1, periodo + 1)
        return np.sum(dados[-periodo:] * pesos) / np.sum(pesos)
    
    def _hull_ma(self, dados, periodo=8):
        if len(dados) < periodo:
            return np.mean(dados) if len(dados) > 0 else 0
        wma1 = self._wma(dados[-periodo//2:], periodo//2) if periodo//2 > 0 else dados[-1]
        wma2 = self._wma(dados[-periodo:], periodo)
        raw_hma = 2 * wma1 - wma2
        periodo_sqrt = max(1, int(np.sqrt(periodo)))
        return self._wma([raw_hma], min(periodo_sqrt, 1))
    
    def _atr(self, velas, periodo=14):
        if len(velas) < periodo + 1:
            return 0
        trs = []
        for i in range(-periodo, 0):
            if i > -len(velas):
                h = velas[i]['high']
                l = velas[i]['low']
                c_prev = velas[i-1]['close'] if i > -periodo else velas[i]['open']
                tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
                trs.append(tr)
        return np.mean(trs) if trs else 0
    
    def _supertrend(self, velas, periodo=1, factor=3):
        if len(velas) < 3:
            return 0, 0, 0
        
        highs = [v['high'] for v in velas]
        lows = [v['low'] for v in velas]
        closes = [v['close'] for v in velas]
        
        atr = self._atr(velas, periodo)
        if atr == 0:
            return 0, 0, 0
        
        hl2 = (highs[-1] + lows[-1]) / 2
        up = hl2 - factor * atr
        dn = hl2 + factor * atr
        
        trend = 1 if closes[-1] > dn else -1 if closes[-1] < up else 0
        
        return up, dn, trend
    
    def analisar(self, velas):
        try:
            if len(velas) < 25:
                return None, 0, {}
            
            closes = [v['close'] for v in velas]
            
            # EMAs
            ema13 = self._ema(closes, 13)
            ema21 = self._ema(closes, 21)
            ema13_ant = self._ema(closes[:-1], 13)
            ema21_ant = self._ema(closes[:-1], 21)
            
            # TEMA/DEMA
            e_ema1 = self._ema(closes, 1)
            e_ema2 = self._ema([e_ema1], 1)
            e_ema3 = self._ema([e_ema2], 1)
            tema = 1 * (e_ema1 - e_ema2) + e_ema3
            
            e_e1 = self._ema(closes, 8)
            e_e2 = self._ema([e_e1], 5)
            dema = 2 * e_e1 - e_e2
            
            # Hull MA
            hma = self._hull_ma(closes[-13:], 8)
            
            # Supertrend
            up, dn, trend = self._supertrend(velas)
            
            # Tendência
            tendencia_alta = ema13 > ema21 and ema13 > ema13_ant
            tendencia_baixa = ema13 < ema21 and ema13 < ema13_ant
            
            # Score
            score_call = 0
            score_put = 0
            detalhes = {}
            
            # 1. Tendência EMA (peso 30)
            if tendencia_alta:
                score_call += 30
                detalhes['tendencia'] = 'ALTA'
            elif tendencia_baixa:
                score_put += 30
                detalhes['tendencia'] = 'BAIXA'
            else:
                detalhes['tendencia'] = 'NEUTRA'
            
            # 2. TEMA/DEMA (peso 25)
            if tema > dema:
                score_call += 25
                detalhes['tema'] = 'BULLISH'
            elif tema < dema:
                score_put += 25
                detalhes['tema'] = 'BEARISH'
            
            # 3. Supertrend (peso 25)
            if trend == 1:
                score_call += 25
                detalhes['supertrend'] = 'UP'
            elif trend == -1:
                score_put += 25
                detalhes['supertrend'] = 'DOWN'
            
            # 4. Hull MA (peso 20)
            if closes[-1] > hma:
                score_call += 20
                detalhes['hull'] = 'ACIMA'
            elif closes[-1] < hma:
                score_put += 20
                detalhes['hull'] = 'ABAIXO'
            
            # Decisão
            if score_call > score_put and score_call >= SCORE_MINIMO:
                confianca = min(score_call, 95)
                return 'CALL', confianca, detalhes
            elif score_put > score_call and score_put >= SCORE_MINIMO:
                confianca = min(score_put, 95)
                return 'PUT', confianca, detalhes
            
            return None, 0, detalhes
            
        except Exception as e:
            return None, 0, {}

class BotVdub:
    def __init__(self):
        self.tg = Telegram(TOKEN, CHAT)
        self.velas = {nome: deque(maxlen=100) for nome in ATIVOS_OTC}
        self.estrategia = VdubSniper()
        self.iq_api = None
        self.placar = {'w': 0, 'g1': 0, 'l': 0}
        self.ult_sinal = 0
        self.ultimo_dia = datetime.now(FUSO_BR).day
    
    def conectar_iq(self):
        from iqoptionapi.stable_api import IQ_Option
        email = os.environ.get('IQ_EMAIL')
        senha = os.environ.get('IQ_SENHA')
        if not email or not senha:
            return None
        try:
            if self.iq_api:
                try: self.iq_api.close()
                except: pass
            self.iq_api = IQ_Option(email, senha)
            check, _ = self.iq_api.connect()
            if check:
                print("✅ Conectado à IQ Option.")
                return self.iq_api
            else:
                print("❌ Falha na conexão.")
                return None
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
    
    async def reconectar_se_necessario(self):
        if self.iq_api is None or not self.iq_api.check_connect():
            print("🔄 Reconectando...")
            return self.conectar_iq()
        return self.iq_api
    
    async def atualizar_velas(self):
        api = await self.reconectar_se_necessario()
        if not api:
            return
        for nome, ativo_id in ATIVOS_OTC.items():
            for retry in range(3):
                try:
                    if not api.check_connect():
                        api = await self.reconectar_se_necessario()
                        if not api:
                            break
                    c = api.get_candles(ativo_id, 300, 80, time.time())
                    if c and len(c) > 0:
                        self.velas[nome].clear()
                        for x in c[-80:]:
                            if isinstance(x, dict):
                                self.velas[nome].append({
                                    'time': datetime.fromtimestamp(x.get('from',0), FUSO_BR),
                                    'open': float(x['open']), 'high': float(x['max']),
                                    'low': float(x['min']), 'close': float(x['close']),
                                    'volume': int(x.get('volume',0))
                                })
                        break
                    time.sleep(2)
                except Exception as e:
                    print(f"Erro velas {nome}: {e}")
                    time.sleep(2)
    
    def buscar_sinal(self):
        melhor_sinal = None
        melhor_score = 0
        
        for par, velas in self.velas.items():
            if len(velas) < 25:
                continue
            direcao, confianca, detalhes = self.estrategia.analisar(velas)
            if direcao and confianca >= SCORE_MINIMO:
                if confianca > melhor_score:
                    melhor_score = confianca
                    melhor_sinal = {
                        'ativo': par,
                        'direcao': direcao,
                        'confianca': confianca,
                        'detalhes': detalhes
                    }
        
        return melhor_sinal
    
    def calcular_horario_entrada(self):
        agora = datetime.now(FUSO_BR)
        minuto = agora.minute
        resto = minuto % 5
        if resto == 0 and agora.second == 0:
            return agora.replace(second=0, microsecond=0)
        else:
            return agora.replace(second=0, microsecond=0) + timedelta(minutes=5 - resto)
    
    def formatar_sinal(self, sinal, horario):
        ativo = sinal['ativo']
        direcao = sinal['direcao']
        conf = sinal['confianca']
        detalhes = sinal.get('detalhes', {})
        hora = horario.strftime('%H:%M')
        detalhes_txt = "\n".join([f"• {k}: {v}" for k, v in detalhes.items()])
        
        return f"""🚨SINAL AO VIVO🚨

✳️ VDUB SNIPER ✅
⏲ EXPIRAÇÃO: M5

👉🏼 HORARIO: {hora}

🏳ATIVO: {ativo}-OTC {direcao}

📊 Confiança: {conf:.0f}%

📈 Indicadores:
{detalhes_txt}

🍀🍀BOA SORTE 🍀 🍀"""
    
    async def monitorar_resultado(self, sinal, horario_entrada):
        ativo = sinal['ativo']
        direcao = sinal['direcao']
        agora = datetime.now(FUSO_BR)
        espera = (horario_entrada + timedelta(minutes=5) - agora).total_seconds()
        if espera > 0:
            await asyncio.sleep(espera)
        await asyncio.sleep(10)
        await self.atualizar_velas()
        velas = self.velas[ativo]
        
        ganhou = False
        for v in velas:
            if v['time'].replace(second=0, microsecond=0) == horario_entrada.replace(second=0, microsecond=0):
                ganhou = v['close'] > v['open'] if direcao == 'CALL' else v['close'] < v['open']
                break
        
        if ganhou:
            self.placar['w'] += 1
            resultado = "✅ WIN"
        else:
            if USAR_GALE:
                proxima_vela = horario_entrada + timedelta(minutes=5)
                agora = datetime.now(FUSO_BR)
                espera = (proxima_vela + timedelta(minutes=5) - agora).total_seconds()
                if espera > 0:
                    await asyncio.sleep(espera)
                await asyncio.sleep(10)
                await self.atualizar_velas()
                velas = self.velas[ativo]
                ganhou_gale = False
                for v in velas:
                    if v['time'].replace(second=0, microsecond=0) == proxima_vela.replace(second=0, microsecond=0):
                        ganhou_gale = v['close'] > v['open'] if direcao == 'CALL' else v['close'] < v['open']
                        break
                if ganhou_gale:
                    self.placar['g1'] += 1
                    resultado = "✅ WIN GALE 1"
                else:
                    self.placar['l'] += 1
                    resultado = "❌ LOSS"
            else:
                self.placar['l'] += 1
                resultado = "❌ LOSS"
        
        total = self.placar['w'] + self.placar['g1'] + self.placar['l']
        tx = round(((self.placar['w'] + self.placar['g1']) / total) * 100, 1) if total > 0 else 0.0
        msg = f"""{resultado}
📊 {ativo}-OTC | {direcao} {'🟢' if direcao=='CALL' else '🔴'}
📊 Placar: 🟢{self.placar['w']}W 🟡{self.placar['g1']}G1 🔴{self.placar['l']}L
🎯 Assertividade: {tx}%"""
        self.tg.send(msg)
    
    def verificar_zeramento_diario(self):
        agora = datetime.now(FUSO_BR)
        if agora.day != self.ultimo_dia:
            self.ultimo_dia = agora.day
            self.placar = {'w': 0, 'g1': 0, 'l': 0}
            self.tg.send("🔄 *PLACAR ZERADO*")
            print("🔄 Placar zerado.")
    
    async def executar(self):
        banner()
        print("⚛️ Bot Vdub Sniper iniciando...")
        self.tg.send("🔥 *VDUB SNIPER ATIVADO*\n📊 EMA + TEMA/DEMA + Supertrend + Hull MA\n🔄 Gale 1\n🎯 4 Pares OTC")
        while True:
            try:
                self.verificar_zeramento_diario()
                await self.atualizar_velas()
                sinal = self.buscar_sinal()
                if sinal and time.time() - self.ult_sinal > INTERVALO_MINIMO:
                    horario_entrada = self.calcular_horario_entrada()
                    horario_envio = horario_entrada - timedelta(seconds=ANTECEDENCIA)
                    agora = datetime.now(FUSO_BR)
                    espera = (horario_envio - agora).total_seconds()
                    if espera > 0:
                        await asyncio.sleep(espera)
                    self.ult_sinal = time.time()
                    msg = self.formatar_sinal(sinal, horario_entrada)
                    self.tg.send(msg)
                    asyncio.create_task(self.monitorar_resultado(sinal, horario_entrada))
                await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("🛑 Encerrado.")
                break
            except Exception as e:
                print(f"Erro: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    bot = BotVdub()
    asyncio.run(bot.executar())
