#!/usr/bin/env python3
"""
⚛️ ICT SILVER BULLET - MODO FLEXÍVEL
🎯 Liquidez + Pullback + Rejeição
📊 6 Pares Forex
🛡️ Filtros flexíveis
🔄 Gale 1
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os
from datetime import datetime, timedelta, timezone
from collections import deque
from pathlib import Path
import yfinance as yf

signal.signal(signal.SIGCHLD, signal.SIG_IGN)
FUSO_BR = timezone(timedelta(hours=-3))

# Configurações
INTERVALO_MINIMO = 300       # 5 min entre sinais
USAR_GALE = True
ANTECEDENCIA = 30
SCORE_MINIMO = 50            # Reduzido de 70 para 50

# Volatilidade ampliada
ATR_MIN = 0.00005
ATR_MAX = 0.0080

def banner():
    print("⚛️ ICT SILVER BULLET - Modo Flexível")

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

ATIVOS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "EURJPY": "EURJPY=X"
}

class Telegram:
    def __init__(self, t, c):
        self.url = f"https://api.telegram.org/bot{t}"
        self.c = c
    def send(self, txt):
        try: requests.post(f"{self.url}/sendMessage", json={"chat_id": self.c, "text": txt, "parse_mode": "Markdown"}, timeout=10)
        except: pass

class ICTSilverBullet:
    def __init__(self):
        pass
    
    def horario_ok(self):
        agora = datetime.now(FUSO_BR)
        dia = agora.weekday()
        return dia < 5  # Segunda a sexta
    
    def _ema(self, dados, periodo):
        if len(dados) < periodo:
            return np.mean(dados) if len(dados) > 0 else 0
        alpha = 2 / (periodo + 1)
        ema = dados[0]
        for i in range(1, len(dados)):
            ema = alpha * dados[i] + (1 - alpha) * ema
        return ema
    
    def analisar(self, velas):
        if len(velas) < 20:
            return None, 0, {}
        
        if not self.horario_ok():
            return None, 0, {}
        
        precos = [v['close'] for v in velas]
        ema20 = self._ema(precos, 20)
        atual = precos[-1]
        
        max_5 = max(v['high'] for v in velas[-5:])
        min_5 = min(v['low'] for v in velas[-5:])
        
        vela = velas[-1]
        corpo = abs(vela['close'] - vela['open'])
        if corpo == 0:
            return None, 0, {}
        
        pavio_sup = vela['high'] - max(vela['close'], vela['open'])
        pavio_inf = min(vela['close'], vela['open']) - vela['low']
        
        detalhes = {}
        score_call = 0
        score_put = 0
        
        # CALL
        if atual > ema20:
            score_call += 30
            detalhes['tendencia'] = 'ALTA'
            
            # Pullback no suporte
            if vela['low'] <= min_5 * 1.002:
                score_call += 20
                detalhes['zona'] = 'SUPORTE'
            
            # Rejeição (pavio inferior >= 1x corpo)
            if pavio_inf >= corpo * 1.0:
                score_call += 30
                detalhes['rejeicao'] = 'PAVIO INFERIOR'
        
        # PUT
        if atual < ema20:
            score_put += 30
            detalhes['tendencia'] = 'BAIXA'
            
            # Pullback na resistência
            if vela['high'] >= max_5 * 0.998:
                score_put += 20
                detalhes['zona'] = 'RESISTÊNCIA'
            
            # Rejeição (pavio superior >= 1x corpo)
            if pavio_sup >= corpo * 1.0:
                score_put += 30
                detalhes['rejeicao'] = 'PAVIO SUPERIOR'
        
        if score_call > score_put and score_call >= SCORE_MINIMO:
            return 'CALL', score_call, detalhes
        elif score_put > score_call and score_put >= SCORE_MINIMO:
            return 'PUT', score_put, detalhes
        
        return None, 0, detalhes

class BotICT:
    def __init__(self):
        self.tg = Telegram(TOKEN, CHAT)
        self.velas = {nome: deque(maxlen=100) for nome in ATIVOS}
        self.estrategia = ICTSilverBullet()
        self.placar = {'w': 0, 'g1': 0, 'l': 0}
        self.ult_sinal = 0
        self.ultimo_dia = datetime.now(FUSO_BR).day
    
    def atualizar_velas(self):
        for nome, symbol in ATIVOS.items():
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period="1d", interval="5m")
                
                if df is not None and len(df) > 0:
                    self.velas[nome].clear()
                    for index, row in df.iterrows():
                        self.velas[nome].append({
                            'time': index.to_pydatetime().astimezone(FUSO_BR),
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': int(row['Volume']) if 'Volume' in row else 0
                        })
                    print(f"✅ {nome}: {len(self.velas[nome])} velas")
                else:
                    print(f"⚠️ {nome}: sem dados")
            except Exception as e:
                print(f"❌ {nome}: {e}")
        
        print()
    
    def calcular_atr(self, velas, periodo=14):
        if len(velas) < periodo + 1:
            return None
        trs = []
        for i in range(-periodo, 0):
            h = velas[i]['high']
            l = velas[i]['low']
            c_prev = velas[i-1]['close'] if i > -periodo else velas[i]['open']
            tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
            trs.append(tr)
        return np.mean(trs)
    
    def buscar_sinal(self):
        for par, velas in self.velas.items():
            if len(velas) < 20:
                continue
            
            atr = self.calcular_atr(velas, 14)
            if atr is None or atr < ATR_MIN or atr > ATR_MAX:
                print(f"🚫 {par}: ATR={atr:.6f} fora da faixa")
                continue
            
            direcao, confianca, detalhes = self.estrategia.analisar(velas)
            if direcao and confianca >= SCORE_MINIMO:
                print(f"✅ {par}: {direcao} {confianca:.0f}%")
                return {'ativo': par, 'direcao': direcao, 'confianca': confianca, 'detalhes': detalhes}
        
        print("❌ Nenhum sinal")
        return None
    
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

✳️ ICT SILVER BULLET ✅
⏲ EXPIRAÇÃO: M5

👉🏼 HORARIO: {hora}

🏳ATIVO: {ativo} {direcao}

📊 Confiança: {conf:.0f}%

📈 Setup:
{detalhes_txt}

🍀🍀BOA SORTE 🍀 🍀"""
    
    async def monitorar_resultado(self, sinal, horario_entrada):
        ativo = sinal['ativo']
        direcao = sinal['direcao']
        
        agora = datetime.now(FUSO_BR)
        espera = (horario_entrada + timedelta(minutes=5) - agora).total_seconds()
        if espera > 0:
            await asyncio.sleep(espera)
        await asyncio.sleep(30)
        self.atualizar_velas()
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
                await asyncio.sleep(30)
                self.atualizar_velas()
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
📊 {ativo} | {direcao} {'🟢' if direcao=='CALL' else '🔴'}
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
        print("⚛️ Bot ICT Silver Bullet flexível iniciando...")
        self.tg.send("🔥 *ICT SILVER BULLET ATIVADO*\n📊 Modo Flexível\n🎯 6 Pares\n🔄 Gale 1\n📡 Yahoo Finance")
        
        while True:
            try:
                self.verificar_zeramento_diario()
                self.atualizar_velas()
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
                
                await asyncio.sleep(30)
                
            except KeyboardInterrupt:
                print("🛑 Encerrado.")
                break
            except Exception as e:
                print(f"Erro: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    bot = BotICT()
    asyncio.run(bot.executar())
