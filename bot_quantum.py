#!/usr/bin/env python3
"""
⚛️ QUANTUM IA M5 - ESTRATÉGIAS OTC OTIMIZADAS
📊 Price Action + Suportes/Resistências + Breakouts
🎯 Foco em M5 para ativos OTC
🔄 Com gerenciamento de risco e volatilidade
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os, random
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict
from pathlib import Path

signal.signal(signal.SIGCHLD, signal.SIG_IGN)
FUSO_BR = timezone(timedelta(hours=-3))

# Configurações M5
INTERVALO_MINIMO = 600       # 10 min entre sinais (2 velas M5)
USAR_GALE = True
ANTECEDENCIA = 30            
CONFIANCA_MINIMA = 70        # Aumentado para M5
TIMEFRAME = 300              # 5 minutos

# Volatilidade M5 (ajustada)
ATR_MIN = 0.0003
ATR_MAX = 0.0020

# Limites de risco
RISCO_MAXIMO_POR_OPERACAO = 0.02  # 2% do capital
STOP_LOSS_PERCENTUAL = 0.005      # 0.5% de stop

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
    "AUDUSD": "AUDUSD-OTC"  # Adicionado mais ativo
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
        
    # Calcular médias
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    # Calcular slope e intercept
    numerador = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denominador = sum((xi - mean_x) ** 2 for xi in x)
    
    if denominador == 0:
        return 0, mean_y
        
    slope = numerador / denominador
    intercept = mean_y - slope * mean_x
    
    return slope, intercept

# ==================== ESTRATÉGIAS M5 OTC ====================

class PriceActionM5:
    """Estratégia baseada em ação de preço para M5 OTC"""
    
    def identificar_padroes(self, velas):
        """Identifica padrões de candlestick e price action"""
        if len(velas) < 5:
            return None, 0
            
        # Últimas velas
        v1 = velas[-1]  # Vela atual
        v2 = velas[-2]  # Vela anterior
        
        # Calcular tamanhos
        corpo1 = abs(v1['close'] - v1['open'])
        corpo2 = abs(v2['close'] - v2['open'])
        range1 = v1['high'] - v1['low']
        range2 = v2['high'] - v2['low']
        
        # Evitar divisão por zero
        if range1 == 0:
            return None, 0
            
        # Identificar padrões
        padroes = []
        
        # Engolfo de Alta (Bullish Engulfing)
        if (v2['close'] < v2['open'] and  # Vela anterior é bearish
            v1['close'] > v1['open'] and  # Vela atual é bullish
            v1['open'] < v2['close'] and  # Abriu abaixo do fechamento anterior
            v1['close'] > v2['open']):    # Fechou acima da abertura anterior
            padroes.append(('CALL', 80))
            
        # Engolfo de Baixa (Bearish Engulfing)
        elif (v2['close'] > v2['open'] and  # Vela anterior é bullish
              v1['close'] < v1['open'] and  # Vela atual é bearish
              v1['open'] > v2['close'] and  # Abriu acima do fechamento anterior
              v1['close'] < v2['open']):    # Fechou abaixo da abertura anterior
            padroes.append(('PUT', 80))
            
        # Martelo (Hammer) - Alta
        elif (v1['close'] > v1['open'] and  # Bullish
              corpo1 < range1 * 0.3 and     # Corpo pequeno
              (v1['open'] - v1['low']) > corpo1 * 2):  # Sombra inferior longa
            padroes.append(('CALL', 75))
            
        # Estrela Cadente (Shooting Star) - Baixa
        elif (v1['close'] < v1['open'] and  # Bearish
              corpo1 < range1 * 0.3 and     # Corpo pequeno
              (v1['high'] - v1['close']) > corpo1 * 2):  # Sombra superior longa
            padroes.append(('PUT', 75))
            
        # Doji - Indefinição (pode ser reversão)
        elif corpo1 < range1 * 0.1:
            # Verificar contexto
            if len(velas) >= 10:
                # Se estava em tendência de alta, pode reverter para baixa
                tendencia = self.analisar_tendencia(velas)
                if tendencia == 'ALTA':
                    padroes.append(('PUT', 65))
                elif tendencia == 'BAIXA':
                    padroes.append(('CALL', 65))
        
        if padroes:
            return padroes[0]
        return None, 0
    
    def analisar_tendencia(self, velas):
        """Analisa tendência de curto prazo usando regressão linear"""
        if len(velas) < 10:
            return 'NEUTRO'
            
        closes = [v['close'] for v in velas[-10:]]
        x = list(range(len(closes)))
        
        slope, _ = calcular_regressao_linear(x, closes)
        
        if slope > 0.0001:
            return 'ALTA'
        elif slope < -0.0001:
            return 'BAIXA'
        return 'NEUTRO'
    
    def analisar(self, velas):
        """Análise principal da estratégia"""
        try:
            if len(velas) < 10:
                return None, 0
                
            padrao, conf = self.identificar_padroes(velas)
            if padrao:
                return padrao, conf
                
            # Análise de momentum
            closes = [v['close'] for v in velas[-5:]]
            if len(closes) >= 5:
                # Aceleração de preço
                dif1 = closes[-1] - closes[-2]
                dif2 = closes[-2] - closes[-3]
                if dif1 > dif2 * 1.5 and dif1 > 0:
                    return 'CALL', 70
                elif dif1 < dif2 * 1.5 and dif1 < 0:
                    return 'PUT', 70
                    
            return None, 0
        except Exception as e:
            print(f"Erro PriceAction: {e}")
            return None, 0

class SuporteResistenciaM5:
    """Estratégia de Suportes e Resistências para M5 OTC"""
    
    def __init__(self):
        self.niveis = {}
        self.ultima_atualizacao = {}
    
    def calcular_niveis(self, velas, periodo=20):
        """Calcula níveis de suporte e resistência"""
        if len(velas) < periodo:
            return None, None, None
            
        # Pivots recentes
        altas = [v['high'] for v in velas[-periodo:]]
        baixas = [v['low'] for v in velas[-periodo:]]
        closes = [v['close'] for v in velas[-periodo:]]
        
        # Resistência = topo do range
        resistencia = np.percentile(altas, 80)
        suporte = np.percentile(baixas, 20)
        
        # Média móvel como suporte/resistência dinâmica
        sma = np.mean(closes)
        
        return suporte, resistencia, sma
    
    def analisar(self, velas):
        """Análise baseada em suportes/resistências"""
        try:
            if len(velas) < 20:
                return None, 0
                
            suporte, resistencia, sma = self.calcular_niveis(velas)
            if suporte is None:
                return None, 0
                
            atual = velas[-1]['close']
            anterior = velas[-2]['close']
            
            # Breakout de resistência
            if anterior < resistencia and atual > resistencia:
                # Confirmar volume (se disponível)
                if atual > sma * 1.002:  # Acima da média
                    return 'CALL', 75
                    
            # Breakout de suporte
            elif anterior > suporte and atual < suporte:
                if atual < sma * 0.998:  # Abaixo da média
                    return 'PUT', 75
                    
            # Reversão em suporte (pullback)
            elif atual > suporte and atual < suporte * 1.002 and anterior < suporte:
                return 'CALL', 70
                
            # Reversão em resistência (pullback)
            elif atual < resistencia and atual > resistencia * 0.998 and anterior > resistencia:
                return 'PUT', 70
                
            return None, 0
        except Exception as e:
            print(f"Erro SuporteResistencia: {e}")
            return None, 0

class BreakoutM5:
    """Estratégia de Breakout para M5 OTC"""
    
    def identificar_consolidacao(self, velas):
        """Identifica período de consolidação"""
        if len(velas) < 10:
            return None, None
            
        # Range das últimas 10 velas
        altas = [v['high'] for v in velas[-10:]]
        baixas = [v['low'] for v in velas[-10:]]
        
        max_range = max(altas) - min(baixas)
        avg_range = np.mean([v['high'] - v['low'] for v in velas[-10:]])
        
        # Consolidação = range pequeno comparado às velas
        if avg_range > 0 and max_range < avg_range * 1.5:
            return max(altas), min(baixas)
        return None, None
    
    def analisar(self, velas):
        """Análise de breakouts"""
        try:
            if len(velas) < 15:
                return None, 0
                
            resistencia, suporte = self.identificar_consolidacao(velas)
            if resistencia is None:
                return None, 0
                
            atual = velas[-1]['close']
            anterior = velas[-2]['close']
            
            # Breakout com confirmação
            if anterior < resistencia and atual > resistencia:
                # Verificar se o movimento é forte
                dif_percent = (atual - resistencia) / resistencia * 100
                if dif_percent > 0.03:  # Movimento de pelo menos 0.03%
                    return 'CALL', 80
                    
            elif anterior > suporte and atual < suporte:
                dif_percent = (suporte - atual) / suporte * 100
                if dif_percent > 0.03:
                    return 'PUT', 80
                    
            return None, 0
        except Exception as e:
            print(f"Erro Breakout: {e}")
            return None, 0

class TendenciaM5:
    """Estratégia baseada em tendência com médias móveis"""
    
    def calcular_medias(self, velas):
        """Calcula médias móveis"""
        if len(velas) < 30:
            return None, None, None
            
        closes = [v['close'] for v in velas]
        sma5 = np.mean(closes[-5:])
        sma10 = np.mean(closes[-10:])
        sma20 = np.mean(closes[-20:])
        
        return sma5, sma10, sma20
    
    def analisar(self, velas):
        """Análise de tendência"""
        try:
            if len(velas) < 30:
                return None, 0
                
            sma5, sma10, sma20 = self.calcular_medias(velas)
            if sma5 is None:
                return None, 0
                
            atual = velas[-1]['close']
            
            # Tendência de alta confirmada
            if (sma5 > sma10 > sma20 and 
                atual > sma5 and
                atual > sma20 * 1.002):
                return 'CALL', 75
                
            # Tendência de baixa confirmada
            elif (sma5 < sma10 < sma20 and 
                  atual < sma5 and
                  atual < sma20 * 0.998):
                return 'PUT', 75
                
            # Cruzamento de médias (Golden/Death Cross)
            if len(velas) >= 31:
                sma5_ant = np.mean([v['close'] for v in velas[-6:-1]])
                sma10_ant = np.mean([v['close'] for v in velas[-11:-1]])
                
                if sma5_ant < sma10_ant and sma5 > sma10:
                    return 'CALL', 70
                elif sma5_ant > sma10_ant and sma5 < sma10:
                    return 'PUT', 70
                    
            return None, 0
        except Exception as e:
            print(f"Erro Tendencia: {e}")
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
        self.sinais_ativos = {}  # Para rastrear sinais em andamento

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
        """Atualiza velas M5"""
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
                    # M5 = 300 segundos
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
                        break
                    time.sleep(2)
                except Exception as e:
                    print(f"Erro velas {nome}: {e}")
                    time.sleep(2)

    def calcular_atr(self, velas, periodo=14):
        """Calcula ATR para M5"""
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

    def calcular_volatilidade_relativa(self, velas):
        """Calcula volatilidade relativa para M5"""
        if len(velas) < 20:
            return 0
            
        closes = [v['close'] for v in velas[-20:]]
        # Calcular retornos logarítmicos
        returns = []
        for i in range(1, len(closes)):
            if closes[i-1] > 0:
                returns.append(np.log(closes[i] / closes[i-1]))
        
        if not returns:
            return 0
            
        return np.std(returns) * 100  # Volatilidade em percentual

    def buscar_sinal_consenso(self):
        """Busca sinais com consenso das estratégias M5"""
        melhores_sinais = []
        
        for par, velas in self.velas.items():
            if len(velas) < 30:
                continue

            # Verificar volatilidade
            atr = self.calcular_atr(velas, 14)
            if atr is None or atr < ATR_MIN or atr > ATR_MAX:
                continue

            # Calcular média móvel para confirmação de tendência
            precos = [v['close'] for v in velas]
            sma20 = sum(precos[-20:]) / 20
            sma50 = sum(precos[-50:]) / 50 if len(precos) >= 50 else sma20
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

            # Confluência de estratégias
            if len(votos_call) >= 2 and len(votos_call) > len(votos_put):
                # Verificar tendência de alta
                if atual > sma20 and sma20 > sma50 * 0.999:
                    conf_media = sum(c[0] for c in votos_call) / len(votos_call)
                    # Bônus de confiança pela tendência
                    conf_media = min(conf_media * 1.05, 95)
                    
                    melhores_sinais.append({
                        'ativo': par, 
                        'direcao': 'CALL', 
                        'confianca': conf_media,
                        'estrategias': detalhes_estrategias,
                        'atr': atr,
                        'sma20': sma20,
                        'atual': atual
                    })

            elif len(votos_put) >= 2 and len(votos_put) > len(votos_call):
                if atual < sma20 and sma20 < sma50 * 1.001:
                    conf_media = sum(c[0] for c in votos_put) / len(votos_put)
                    conf_media = min(conf_media * 1.05, 95)
                    
                    melhores_sinais.append({
                        'ativo': par, 
                        'direcao': 'PUT', 
                        'confianca': conf_media,
                        'estrategias': detalhes_estrategias,
                        'atr': atr,
                        'sma20': sma20,
                        'atual': atual
                    })

        # Ordenar por confiança
        if melhores_sinais:
            melhores_sinais.sort(key=lambda x: x['confianca'], reverse=True)
            return melhores_sinais[0]
            
        return None

    def calcular_horario_entrada(self):
        """Calcula horário de entrada para M5"""
        agora = datetime.now(FUSO_BR)
        # Próximo candle M5
        minutos = agora.minute
        proximo = ((minutos // 5) + 1) * 5
        if proximo >= 60:
            proximo = 0
            agora += timedelta(hours=1)
        return agora.replace(minute=proximo, second=0, microsecond=0)

    def formatar_sinal(self, sinal, horario):
        """Formata sinal para envio"""
        ativo = sinal['ativo']
        direcao = sinal['direcao']
        conf = sinal['confianca']
        estrategias = sinal.get('estrategias', [])
        atr = sinal.get('atr', 0)
        
        hora = horario.strftime('%H:%M')
        
        # Emoji para direção
        emoji_dir = '🟢' if direcao == 'CALL' else '🔴'
        
        # Estratégias que concordaram
        estrategias_str = '\n'.join(estrategias[:3])  # Mostrar até 3
        
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
        """Monitora resultado da operação M5"""
        ativo = sinal['ativo']
        direcao = sinal['direcao']
        
        # Aguardar 5 minutos (M5)
        agora = datetime.now(FUSO_BR)
        espera = (horario_entrada + timedelta(minutes=5) - agora).total_seconds()
        if espera > 0:
            await asyncio.sleep(espera)
        
        await asyncio.sleep(10)  # Aguardar fechamento
        await self.atualizar_velas()
        velas = self.velas[ativo]
        
        # Verificar resultado
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
                # Gale 1 - entrar na próxima vela M5
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
        
        # Atualizar estatísticas
        total = self.placar['w'] + self.placar['g1'] + self.placar['l']
        tx = round(((self.placar['w'] + self.placar['g1']) / total) * 100, 1) if total > 0 else 0.0
        
        msg = f"""{resultado}
📊 {ativo}-OTC | {direcao} {'🟢' if direcao=='CALL' else '🔴'}
📊 Placar: 🟢{self.placar['w']}W 🟡{self.placar['g1']}G1 🔴{self.placar['l']}L
🎯 Assertividade: {tx}%"""
        
        self.tg.send(msg)

    def verificar_zeramento_diario(self):
        """Zera placar diariamente"""
        agora = datetime.now(FUSO_BR)
        if agora.day != self.ultimo_dia:
            self.ultimo_dia = agora.day
            self.placar = {'w': 0, 'g1': 0, 'l': 0}
            self.tg.send("🔄 *PLACAR ZERADO*")
            print("🔄 Placar zerado.")

    async def executar(self):
        """Loop principal do bot"""
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
                    
                    # Iniciar monitoramento
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
