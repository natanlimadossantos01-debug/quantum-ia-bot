#!/usr/bin/env python3
"""
⚛️ QUANTUM IA M5 - ESTRATÉGIAS OTC OTIMIZADAS
📊 Price Action + Suportes/Resistências + Breakouts
🎯 Foco em M5 para ativos OTC
🔄 Com gerenciamento de risco e volatilidade
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os
from datetime import datetime, timedelta, timezone
from collections import deque

signal.signal(signal.SIGCHLD, signal.SIG_IGN)
FUSO_BR = timezone(timedelta(hours=-3))

# Configurações M5
INTERVALO_MINIMO = 600       # 10 min entre sinais
USAR_GALE = True
ANTECEDENCIA = 30            
CONFIANCA_MINIMA = 70
TIMEFRAME = 300              # 5 minutos

# Volatilidade M5
ATR_MIN = 0.0003
ATR_MAX = 0.0020

def banner():
    print("⚛️ QUANTUM IA M5 - Estratégias OTC Otimizadas")

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

# ==================== FUNÇÕES AUXILIARES ====================

def calcular_regressao_linear(x, y):
    """Calcula regressão linear sem scipy"""
    n = len(x)
    if n < 2:
        return 0, 0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    numerador = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denominador = sum((xi - mean_x) ** 2 for xi in x)
    if denominador == 0:
        return 0, mean_y
    slope = numerador / denominador
    intercept = mean_y - slope * mean_x
    return slope, intercept

# ==================== ESTRATÉGIAS M5 OTC ====================

class PriceActionM5:
    def identificar_padroes(self, velas):
        if len(velas) < 5:
            return None, 0
        v1 = velas[-1]
        v2 = velas[-2]
        corpo1 = abs(v1['close'] - v1['open'])
        range1 = v1['high'] - v1['low']
        if range1 == 0:
            return None, 0
        # Engolfo de Alta
        if (v2['close'] < v2['open'] and v1['close'] > v1['open'] and
            v1['open'] < v2['close'] and v1['close'] > v2['open']):
            return ('CALL', 80)
        # Engolfo de Baixa
        elif (v2['close'] > v2['open'] and v1['close'] < v1['open'] and
              v1['open'] > v2['close'] and v1['close'] < v2['open']):
            return ('PUT', 80)
        return None, 0
    
    def analisar(self, velas):
        try:
            if len(velas) < 10:
                return None, 0
            padrao, conf = self.identificar_padroes(velas)
            if padrao:
                return padrao, conf
            return None, 0
        except:
            return None, 0

class SuporteResistenciaM5:
    def calcular_niveis(self, velas, periodo=20):
        if len(velas) < periodo:
            return None, None, None
        altas = [v['high'] for v in velas[-periodo:]]
        baixas = [v['low'] for v in velas[-periodo:]]
        closes = [v['close'] for v in velas[-periodo:]]
        resistencia = np.percentile(altas, 80)
        suporte = np.percentile(baixas, 20)
        sma = np.mean(closes)
        return suporte, resistencia, sma
    
    def analisar(self, velas):
        try:
            if len(velas) < 20:
                return None, 0
            suporte, resistencia, sma = self.calcular_niveis(velas)
            if suporte is None:
                return None, 0
            atual = velas[-1]['close']
            anterior = velas[-2]['close']
            if anterior < resistencia and atual > resistencia and atual > sma * 1.002:
                return 'CALL', 75
            elif anterior > suporte and atual < suporte and atual < sma * 0.998:
                return 'PUT', 75
            return None, 0
        except:
            return None, 0

class BreakoutM5:
    def identificar_consolidacao(self, velas):
        if len(velas) < 10:
            return None, None
        altas = [v['high'] for v in velas[-10:]]
        baixas = [v['low'] for v in velas[-10:]]
        max_range = max(altas) - min(baixas)
        avg_range = np.mean([v['high'] - v['low'] for v in velas[-10:]])
        if avg_range > 0 and max_range < avg_range * 1.5:
            return max(altas), min(baixas)
        return None, None
    
    def analisar(self, velas):
        try:
            if len(velas) < 15:
                return None, 0
            resistencia, suporte = self.identificar_consolidacao(velas)
            if resistencia is None:
                return None, 0
            atual = velas[-1]['close']
            anterior = velas[-2]['close']
            if anterior < resistencia and atual > resistencia:
                dif_percent = (atual - resistencia) / resistencia * 100
                if dif_percent > 0.03:
                    return 'CALL', 80
            elif anterior > suporte and atual < suporte:
                dif_percent = (suporte - atual) / suporte * 100
                if dif_percent > 0.03:
                    return 'PUT', 80
            return None, 0
        except:
            return None, 0

class TendenciaM5:
    def calcular_medias(self, velas):
        if len(velas) < 30:
            return None, None, None
        closes = [v['close'] for v in velas]
        sma5 = np.mean(closes[-5:])
        sma10 = np.mean(closes[-10:])
        sma20 = np.mean(closes[-20:])
        return sma5, sma10, sma20
    
    def analisar(self, velas):
        try:
            if len(velas) < 30:
                return None, 0
            sma5, sma10, sma20 = self.calcular_medias(velas)
            if sma5 is None:
                return None, 0
            atual = velas[-1]['close']
            if (sma5 > sma10 > sma20 and atual > sma5 and atual > sma20 * 1.002):
                return 'CALL', 75
            elif (sma5 < sma10 < sma20 and atual < sma5 and atual < sma20 * 0.998):
                return 'PUT', 75
            return None, 0
        except:
            return None, 0

# ==================== BOT M5 ====================

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
            except Exception as e:
                print(f"Erro velas {nome}: {e}")
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

    def buscar_sinal_consenso(self):
        melhores_sinais = []
        for par, velas in self.velas.items():
            if len(velas) < 30:
                continue
            atr = self.calcular_atr(velas, 14)
            if atr is None or atr < ATR_MIN or atr > ATR_MAX:
                continue
            precos = [v['close'] for v in velas]
            sma20 = sum(precos[-20:]) / 20
            atual = precos[-1]
            votos_call = []
            votos_put = []
            detalhes_estrategias = []
            for nome_est, est in self.estrategias_m5:
                resultado = est.analisar(velas)
                if resultado:
                    direcao, conf = resultado
                    if conf >= CONFIANCA_MINIMA:
                        if direcao == 'CALL':
                            votos_call.append((conf, nome_est))
                        else:
                            votos_put.append((conf, nome_est))
                        detalhes_estrategias.append(f"{nome_est}: {direcao} ({conf}%)")
            if len(votos_call) >= 2 and len(votos_call) > len(votos_put):
                if atual > sma20:
                    conf_media = sum(c[0] for c in votos_call) / len(votos_call)
                    melhores_sinais.append({
                        'ativo': par, 
                        'direcao': 'CALL', 
                        'confianca': conf_media,
                        'estrategias': detalhes_estrategias,
                        'atr': atr
                    })
            elif len(votos_put) >= 2 and len(votos_put) > len(votos_call):
                if atual < sma20:
                    conf_media = sum(c[0] for c in votos_put) / len(votos_put)
                    melhores_sinais.append({
                        'ativo': par, 
                        'direcao': 'PUT', 
                        'confianca': conf_media,
                        'estrategias': detalhes_estrategias,
                        'atr': atr
                    })
        if melhores_sinais:
            melhores_sinais.sort(key=lambda x: x['confianca'], reverse=True)
            return melhores_sinais[0]
        return None

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
        estrategias = sinal.get('estrategias', [])
        atr = sinal.get('atr', 0)
        hora = horario.strftime('%H:%M')
        emoji_dir = '🟢' if direcao == 'CALL' else '🔴'
        estrategias_str = '\n'.join(estrategias[:3])
        return f"""🚨 SINAL M5 OTC 🚨

⚛️ QUANTUM IA M5
⏲ EXPIRAÇÃO: 5 MINUTOS

👉🏼 HORARIO: {hora}

🏳 ATIVO: {ativo}-OTC {emoji_dir}
📊 DIREÇÃO: {direcao}
🎯 CONFIANÇA: {conf:.1f}%

📈 ESTRATÉGIAS CONFIRMANDO:
{estrategias_str}

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
        self.tg.send("🔥 *QUANTUM IA M5 ATIVADO*\n📊 4 Estratégias OTC Otimizadas\n🎯 Confluência 2+\n📊 Volatilidade ATR\n🔄 Gale 1")
        while True:
            try:
                self.verificar_zeramento_diario()
                await self.atualizar_velas()
                sinal = self.buscar_sinal_consenso()
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
    bot = BotM5()
    asyncio.run(bot.executar())
