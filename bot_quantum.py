#!/usr/bin/env python3
"""
⚛️ QUANTUM IA M5 - OTC OTIMIZADO - ANTI-TRAVAMENTO
📊 4 Estratégias
🎯 Confiança mínima: 62%
🛡️ ATR ampliado
🔄 Reconexão automática
💓 Heartbeat
✅ Correção: close vs open
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os
from datetime import datetime, timedelta, timezone
from collections import deque
from pathlib import Path

signal.signal(signal.SIGCHLD, signal.SIG_IGN)
FUSO_BR = timezone(timedelta(hours=-3))

INTERVALO_MINIMO = 600
USAR_GALE = True
ANTECEDENCIA = 30
CONFIANCA_MINIMA = 62          # Confiança mínima 62%
TIMEFRAME = 300

# ATR ampliado
ATR_MIN = 0.00005
ATR_MAX = 0.0050

def banner():
    print("⚛️ QUANTUM IA M5 - OTC | Confiança 62%+")

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
}

class Telegram:
    def __init__(self, t, c):
        self.url = f"https://api.telegram.org/bot{t}"
        self.c = c
    def send(self, txt):
        try: 
            requests.post(f"{self.url}/sendMessage", 
                         json={"chat_id": self.c, "text": txt, "parse_mode": "Markdown"}, 
                         timeout=10)
        except: 
            pass

class PriceActionM5:
    def analisar(self, velas):
        try:
            if len(velas) < 5:
                return None, 0
            v1 = velas[-1]
            v2 = velas[-2]
            if (v2['close'] < v2['open'] and v1['close'] > v1['open'] and
                v1['open'] < v2['close'] and v1['close'] > v2['open']):
                return ('CALL', 80)
            elif (v2['close'] > v2['open'] and v1['close'] < v1['open'] and
                  v1['open'] > v2['close'] and v1['close'] < v2['open']):
                return ('PUT', 80)
            return None, 0
        except:
            return None, 0

class SuporteResistenciaM5:
    def analisar(self, velas):
        try:
            if len(velas) < 20:
                return None, 0
            altas = [v['high'] for v in velas[-20:]]
            baixas = [v['low'] for v in velas[-20:]]
            resistencia = np.percentile(altas, 80)
            suporte = np.percentile(baixas, 20)
            atual = velas[-1]['close']
            anterior = velas[-2]['close']
            if anterior < resistencia and atual > resistencia:
                return 'CALL', 75
            elif anterior > suporte and atual < suporte:
                return 'PUT', 75
            return None, 0
        except:
            return None, 0

class BreakoutM5:
    def analisar(self, velas):
        try:
            if len(velas) < 10:
                return None, 0
            altas = [v['high'] for v in velas[-10:]]
            baixas = [v['low'] for v in velas[-10:]]
            resistencia = max(altas)
            suporte = min(baixas)
            atual = velas[-1]['close']
            if atual > resistencia:
                return 'CALL', 80
            elif atual < suporte:
                return 'PUT', 80
            return None, 0
        except:
            return None, 0

class TendenciaM5:
    def analisar(self, velas):
        try:
            if len(velas) < 30:
                return None, 0
            closes = [v['close'] for v in velas]
            sma5 = np.mean(closes[-5:])
            sma20 = np.mean(closes[-20:])
            atual = velas[-1]['close']
            if sma5 > sma20 and atual > sma5:
                return 'CALL', 75
            elif sma5 < sma20 and atual < sma5:
                return 'PUT', 75
            return None, 0
        except:
            return None, 0

class BotM5:
    def __init__(self):
        self.tg = Telegram(TOKEN, CHAT)
        self.velas = {nome: deque(maxlen=100) for nome in ATIVOS_OTC}
        self.estrategias_m5 = [
            ('📊 Price Action', PriceActionM5()),
            ('🏛️ Suporte/Resistência', SuporteResistenciaM5()),
            ('🚀 Breakout', BreakoutM5()),
            ('📈 Tendência', TendenciaM5())
        ]
        self.iq_api = None
        self.placar = {'w': 0, 'g1': 0, 'l': 0}
        self.ult_sinal = 0
        self.sinais = 0
        self.ultimo_dia = datetime.now(FUSO_BR).day

    def conectar_iq(self):
        from iqoptionapi.stable_api import IQ_Option
        email = os.environ.get('IQ_EMAIL')
        senha = os.environ.get('IQ_SENHA')
        if not email or not senha:
            print("❌ IQ_EMAIL e IQ_SENHA não configurados")
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
            try:
                if not api.check_connect():
                    api = await self.reconectar_se_necessario()
                    if not api:
                        break
                c = api.get_candles(ativo_id, TIMEFRAME, 80, time.time())
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
                    print(f"✅ {nome}: {len(self.velas[nome])} velas")
            except Exception as e:
                print(f"Erro {nome}: {e}")
                await asyncio.sleep(2)

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
        """Aceita 1+ estratégia com confiança >= 62%"""
        melhor_sinal = None
        melhor_score = 0
        
        for par, velas in self.velas.items():
            if len(velas) < 20:
                continue
            
            atr = self.calcular_atr(velas, 14)
            if atr is None or atr < ATR_MIN or atr > ATR_MAX:
                print(f"🚫 {par}: ATR={atr:.6f} fora da faixa")
                continue
            
            for nome_est, est in self.estrategias_m5:
                resultado = est.analisar(velas)
                if resultado and len(resultado) >= 2:
                    d, c = resultado[0], resultado[1]
                    if d in ('CALL', 'PUT') and c >= CONFIANCA_MINIMA:
                        print(f"✅ {par} | {nome_est}: {d} {c:.0f}%")
                        if c > melhor_score:
                            melhor_score = c
                            melhor_sinal = {
                                'ativo': par,
                                'direcao': d,
                                'confianca': c,
                                'estrategia': nome_est,
                                'atr': atr
                            }
        
        if melhor_sinal is None:
            print("❌ Nenhum sinal")
        
        return melhor_sinal

    def calcular_horario_entrada(self):
        agora = datetime.now(FUSO_BR)
        minutos = agora.minute
        proximo = ((minutos // 5) + 1) * 5
        if proximo >= 60:
            proximo = 0
            agora += timedelta(hours=1)
        return agora.replace(minute=proximo, second=0, microsecond=0)

    def formatar_sinal(self, sinal, horario):
        ativo = sinal['ativo']
        direcao = sinal['direcao']
        conf = sinal['confianca']
        estrategia = sinal['estrategia']
        atr = sinal.get('atr', 0)
        hora = horario.strftime('%H:%M')
        emoji_dir = '🟢' if direcao == 'CALL' else '🔴'
        return f"""🚨 SINAL M5 OTC 🚨

⚛️ QUANTUM IA M5
⏲ EXPIRAÇÃO: 5 MINUTOS

👉🏼 HORARIO: {hora}

🏳 ATIVO: {ativo}-OTC {emoji_dir}
📊 DIREÇÃO: {direcao}
🎯 CONFIANÇA: {conf:.1f}%

📈 ESTRATÉGIA: {estrategia}

📊 VOLATILIDADE: {atr:.5f}

🍀🍀 BOA SORTE 🍀🍀"""

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
                if direcao == 'CALL':
                    ganhou = v['close'] > v['open']
                else:
                    ganhou = v['close'] < v['open']
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
                        if direcao == 'CALL':
                            ganhou_gale = v['close'] > v['open']
                        else:
                            ganhou_gale = v['close'] < v['open']
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
        print("⚛️ Bot M5 OTC iniciando...")
        self.tg.send(f"🔥 *QUANTUM IA M5 OTC*\n📊 4 Estratégias\n🎯 Confiança {CONFIANCA_MINIMA}%+\n📊 ATR ampliado\n🔄 Gale 1\n💓 Heartbeat")
        while True:
            try:
                self.verificar_zeramento_diario()
                
                agora = datetime.now(FUSO_BR)
                if agora.second == 0:
                    total_velas = sum(len(v) for v in self.velas.values())
                    print(f"💓 {agora.strftime('%H:%M:%S')} | Velas: {total_velas} | Sinais: {self.sinais}")
                    
                    if total_velas == 0:
                        print("🔄 Sem velas! Reconectando...")
                        self.iq_api = None
                
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
                    self.sinais += 1
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
    bot = BotM5()
    asyncio.run(bot.executar())
