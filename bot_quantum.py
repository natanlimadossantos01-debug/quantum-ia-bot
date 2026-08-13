#!/usr/bin/env python3
"""
⚛️ QUANTUM BOT PRO - SINAIS TELEGRAM (14 ESTRATÉGIAS) + FILTROS AVANÇADOS
🕯️ 12 Quadrantes + 5-2-0 + Chinesa 3.0
🛡️ Filtros: EMA9, SMA20, RSI14, ATR14, Pavio, Vela Forte, Horário
🧠 Catalogador + escolha da melhor combinação
📨 Envia sinal + análise + resultado com placar (sem executar trades)
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os, random
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict
from pathlib import Path

signal.signal(signal.SIGCHLD, signal.SIG_IGN)
FUSO_BR = timezone(timedelta(hours=-3))

# ═══════════════════════════════════════════════════════════
# CONFIGURAÇÕES DE FILTROS (ajuste conforme necessário)
# ═══════════════════════════════════════════════════════════
CONFIANCA_MINIMA = 65          # Confiança mínima do sinal (percentual)
INTERVALO_MINIMO = 300         # Segundos entre sinais (5 min)

USAR_FILTRO_PAVIO = True       # Evita pavios longos
USAR_FILTRO_VELA_FORTE = True  # Evita volatilidade extrema
USAR_FILTRO_HORARIO = True     # Evita sessão asiática

USAR_FILTRO_EMA9 = False       # Sinal alinhado à EMA9
USAR_FILTRO_SMA20 = False      # Sinal alinhado à SMA20
USAR_FILTRO_RSI = True         # Evita sobrecompra/sobrevenda
USAR_FILTRO_ATR = True         # Exige volatilidade dentro de faixa

# Parâmetros do RSI e ATR
RSI_SOBRECOMPRA = 70           # CALL bloqueado se RSI > este valor
RSI_SOBREVENDA = 30            # PUT bloqueado se RSI < este valor
ATR_MIN = 0.0003               # Volatilidade mínima (ajuste para seu ativo)
ATR_MAX = 0.0015               # Volatilidade máxima (ajuste para seu ativo)

def banner():
    print("⚛️ QUANTUM BOT PRO - Sinais Telegram | 14 Estratégias | Filtros Avançados")

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
    "EURUSD":"EURUSD-OTC",
    "GBPUSD":"GBPUSD-OTC",
    "EURJPY":"EURJPY-OTC"
}

class Telegram:
    def __init__(self, t, c):
        self.url = f"https://api.telegram.org/bot{t}"
        self.c = c
    def send(self, txt):
        try: requests.post(f"{self.url}/sendMessage", json={"chat_id": self.c, "text": txt, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# ------------------------- ESTRATÉGIAS -------------------------
class EstrategiasM1:
    def __init__(self):
        self.velas = []
        self.quadrante_anterior = []
        self.quadrante_atual = []

    def add_vela(self, open_price, close_price, high, low):
        vela = [open_price, close_price, high, low]
        self.velas.append(vela)
        if len(self.velas) > 100:
            self.velas.pop(0)
        self._atualizar_quadrantes()

    def _atualizar_quadrantes(self):
        if len(self.velas) >= 10:
            self.quadrante_anterior = self.velas[-10:-5]
            self.quadrante_atual = self.velas[-5:]

    def get_cor(self, vela):
        if vela[1] > vela[0]: return 'up'
        elif vela[1] < vela[0]: return 'down'
        return 'doji'

    def contar_cores(self, velas, posicoes=None):
        if posicoes is None: posicoes = range(len(velas))
        ups = sum(1 for i in posicoes if i < len(velas) and self.get_cor(velas[i]) == 'up')
        downs = sum(1 for i in posicoes if i < len(velas) and self.get_cor(velas[i]) == 'down')
        return ups, downs

    def get_minoria(self, velas, posicoes=None):
        ups, downs = self.contar_cores(velas, posicoes)
        if ups < downs and ups > 0: return 'up'
        elif downs < ups and downs > 0: return 'down'
        return 'doji'

    def get_maioria(self, velas, posicoes=None):
        ups, downs = self.contar_cores(velas, posicoes)
        if ups > downs: return 'up'
        elif downs > ups: return 'down'
        return 'doji'

    # 12 quadrantes
    def mhi1(self):
        if len(self.quadrante_anterior) < 3: return None
        minoria = self.get_minoria(self.quadrante_anterior, [-3, -2, -1])
        if minoria == 'doji': return None
        return {'estrategia': 'MHI 1', 'direcao': 'CALL' if minoria == 'up' else 'PUT', 'entrada': 0}

    def mhi2(self):
        if len(self.quadrante_anterior) < 3: return None
        minoria = self.get_minoria(self.quadrante_anterior, [-3, -2, -1])
        if minoria == 'doji': return None
        return {'estrategia': 'MHI 2', 'direcao': 'CALL' if minoria == 'up' else 'PUT', 'entrada': 1}

    def mhi3(self):
        if len(self.quadrante_anterior) < 3: return None
        minoria = self.get_minoria(self.quadrante_anterior, [-3, -2, -1])
        if minoria == 'doji': return None
        return {'estrategia': 'MHI 3', 'direcao': 'CALL' if minoria == 'up' else 'PUT', 'entrada': 2}

    def vituxo2(self):
        if len(self.quadrante_anterior) < 3: return None
        maioria = self.get_maioria(self.quadrante_anterior, [0, 1, 2])
        if maioria == 'doji': return None
        return {'estrategia': 'VITUXO 2.0', 'direcao': 'CALL' if maioria == 'up' else 'PUT', 'entrada': 2}

    def c3(self):
        if len(self.quadrante_anterior) < 1: return None
        cor = self.get_cor(self.quadrante_anterior[0])
        if cor == 'doji': return None
        return {'estrategia': 'C3', 'direcao': 'CALL' if cor == 'up' else 'PUT', 'entrada': 0}

    def msf(self):
        if len(self.quadrante_anterior) < 1: return None
        cor = self.get_cor(self.quadrante_anterior[0])
        if cor == 'doji': return None
        direcao = 'PUT' if cor == 'up' else 'CALL'
        return {'estrategia': 'MSF', 'direcao': direcao, 'entrada': 4}

    def milhao_maioria(self):
        if len(self.quadrante_anterior) < 5: return None
        maioria = self.get_maioria(self.quadrante_anterior)
        if maioria == 'doji': return None
        return {'estrategia': 'Milhão (Maioria)', 'direcao': 'CALL' if maioria == 'up' else 'PUT', 'entrada': 0}

    def milhao_minoria(self):
        if len(self.quadrante_anterior) < 5: return None
        minoria = self.get_minoria(self.quadrante_anterior)
        if minoria == 'doji': return None
        return {'estrategia': 'Milhão (Minoria)', 'direcao': 'CALL' if minoria == 'up' else 'PUT', 'entrada': 0}

    def tres_vizinhos(self):
        if len(self.quadrante_atual) < 4: return None
        cor = self.get_cor(self.quadrante_atual[3])
        if cor == 'doji': return None
        return {'estrategia': '3 Vizinhos', 'direcao': 'CALL' if cor == 'up' else 'PUT', 'entrada': 4}

    def daka(self):
        if len(self.quadrante_anterior) < 4: return None
        cor = self.get_cor(self.quadrante_anterior[3])
        if cor == 'doji': return None
        return {'estrategia': 'DAKA', 'direcao': 'CALL' if cor == 'up' else 'PUT', 'entrada': 0}

    def estrategia_23(self):
        if len(self.quadrante_atual) < 1: return None
        cor = self.get_cor(self.quadrante_atual[0])
        if cor == 'doji': return None
        return {'estrategia': '23', 'direcao': 'CALL' if cor == 'up' else 'PUT', 'entrada': 1}

    def r7(self):
        if len(self.quadrante_anterior) < 8: return None
        cor = self.get_cor(self.quadrante_anterior[7])
        if cor == 'doji': return None
        return {'estrategia': 'R7', 'direcao': 'CALL' if cor == 'up' else 'PUT', 'entrada': 6}

    # 5-2-0
    def estrategia_520(self, v):
        try:
            if len(v) < 25: return None, 0
            precos = [x['close'] for x in v]
            mm5 = np.mean(precos[-5:])
            media20 = np.mean(precos[-20:])
            std20 = np.std(precos[-20:])
            bs = media20 + 2*std20
            bi = media20 - 2*std20
            atual = precos[-1]
            if atual > mm5 and atual <= bi*1.002: return 'CALL', 78
            if atual < mm5 and atual >= bs*0.998: return 'PUT', 78
            return None, 0
        except: return None, 0

    # Chinesa 3.0
    def chinesa_30(self, v):
        try:
            if len(v) < 30: return None, 0
            precos = [x['close'] for x in v]
            ma20 = np.mean(precos[-20:])
            suporte = min(x['low'] for x in v[-10:])
            resistencia = max(x['high'] for x in v[-10:])
            atual = precos[-1]
            if atual > ma20 and v[-1]['high'] > resistencia: return 'CALL', 80
            if atual < ma20 and v[-1]['low'] < suporte: return 'PUT', 80
            return None, 0
        except: return None, 0

    def executar_todas(self):
        sinais = []
        estrategias = [
            ('MHI 1', self.mhi1), ('MHI 2', self.mhi2), ('MHI 3', self.mhi3),
            ('VITUXO 2.0', self.vituxo2), ('C3', self.c3), ('MSF', self.msf),
            ('Milhão (Maioria)', self.milhao_maioria), ('Milhão (Minoria)', self.milhao_minoria),
            ('3 Vizinhos', self.tres_vizinhos), ('DAKA', self.daka),
            ('23', self.estrategia_23), ('R7', self.r7)
        ]
        for nome, func in estrategias:
            try:
                resultado = func()
                if resultado:
                    resultado['nome'] = nome
                    sinais.append(resultado)
            except: pass
        return sinais

# ------------------------- FILTROS AVANÇADOS -------------------------
class Filtros:
    @staticmethod
    def ema(velas, periodo=9):
        if len(velas) < periodo: return None
        precos = [v['close'] for v in velas]
        k = 2 / (periodo + 1)
        ema = precos[0]
        for p in precos[1:]:
            ema = p * k + ema * (1 - k)
        return ema

    @staticmethod
    def sma(velas, periodo=20):
        if len(velas) < periodo: return None
        precos = [v['close'] for v in velas]
        return np.mean(precos[-periodo:])

    @staticmethod
    def rsi(velas, periodo=14):
        if len(velas) < periodo + 1: return None
        precos = [v['close'] for v in velas]
        deltas = np.diff(precos[-periodo-1:])
        ganhos = np.where(deltas > 0, deltas, 0)
        perdas = np.where(deltas < 0, -deltas, 0)
        media_ganho = np.mean(ganhos)
        media_perda = np.mean(perdas)
        if media_perda == 0:
            return 100.0
        rs = media_ganho / media_perda
        return 100 - (100 / (1 + rs))

    @staticmethod
    def atr(velas, periodo=14):
        if len(velas) < periodo + 1: return None
        trs = []
        for i in range(-periodo, 0):
            h = velas[i]['high']
            l = velas[i]['low']
            c_prev = velas[i-1]['close'] if i > -periodo else velas[i]['open']
            tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
            trs.append(tr)
        return np.mean(trs)

    # Filtros booleanos
    @staticmethod
    def sinal_alinhado_ema(velas, direcao, periodo=9):
        ema_val = Filtros.ema(velas, periodo)
        if ema_val is None: return False
        fechamento = velas[-1]['close']
        return fechamento > ema_val if direcao == 'CALL' else fechamento < ema_val

    @staticmethod
    def sinal_alinhado_sma(velas, direcao, periodo=20):
        sma_val = Filtros.sma(velas, periodo)
        if sma_val is None: return False
        fechamento = velas[-1]['close']
        return fechamento > sma_val if direcao == 'CALL' else fechamento < sma_val

    @staticmethod
    def rsi_ok(velas, direcao):
        rsi_val = Filtros.rsi(velas, 14)
        if rsi_val is None: return True
        if direcao == 'CALL':
            return rsi_val < RSI_SOBRECOMPRA   # não sobrecomprado
        else:
            return rsi_val > RSI_SOBREVENDA    # não sobrevendido

    @staticmethod
    def atr_ok(velas):
        atr_val = Filtros.atr(velas, 14)
        if atr_val is None: return True
        return ATR_MIN <= atr_val <= ATR_MAX

    @staticmethod
    def pavio_ok(velas, direcao):
        va = velas[-1]
        corpo = abs(va['close'] - va['open'])
        if corpo == 0: return False
        if direcao == 'CALL':
            pavio_sup = va['high'] - max(va['close'], va['open'])
            return pavio_sup <= corpo * 0.4
        else:
            pavio_inf = min(va['close'], va['open']) - va['low']
            return pavio_inf <= corpo * 0.4

    @staticmethod
    def vela_forte_ok(velas):
        if len(velas) < 15: return True
        ranges = [velas[i]['high'] - velas[i]['low'] for i in range(-14, 0)]
        atr_val = np.mean(ranges)
        ultimo_range = velas[-1]['high'] - velas[-1]['low']
        return ultimo_range <= atr_val * 2.0

    @staticmethod
    def horario_ok():
        agora = datetime.now(FUSO_BR)
        hora = agora.hour
        if 22 <= hora or hora < 6:
            return False
        return True

# ------------------------- CATALOGADOR -------------------------
class Catalogador:
    def __init__(self):
        self.performance = {}
        self.total_operacoes = 0

    def registrar_resultado(self, estrategia, par, ganhou):
        chave = f"{estrategia}|{par}"
        if chave not in self.performance:
            self.performance[chave] = {'estrategia': estrategia, 'par': par, 'wins': 0, 'losses': 0, 'total': 0}
        self.performance[chave]['total'] += 1
        if ganhou: self.performance[chave]['wins'] += 1
        else: self.performance[chave]['losses'] += 1
        self.total_operacoes += 1

    def get_taxa(self, estrategia, par):
        chave = f"{estrategia}|{par}"
        if chave in self.performance:
            p = self.performance[chave]
            return round((p['wins']/p['total'])*100, 1) if p['total'] > 0 else 0
        return 0

    def get_melhores(self, min_ops=3):
        melhores = []
        for chave, p in self.performance.items():
            if p['total'] >= min_ops:
                taxa = (p['wins']/p['total'])*100
                melhores.append({'estrategia': p['estrategia'], 'par': p['par'], 'taxa': taxa, 'total': p['total'], 'wins': p['wins'], 'losses': p['losses']})
        melhores.sort(key=lambda x: x['taxa'], reverse=True)
        return melhores

    def escolher_melhor(self, min_ops=3):
        melhores = self.get_melhores(min_ops)
        if melhores:
            return [m for m in melhores if m['taxa'] >= 50][0] if any(m['taxa']>=50 for m in melhores) else melhores[0]
        return None

# ------------------------- TRADER PROFESSOR -------------------------
class TraderProfessor:
    def __init__(self):
        self.tendencias = {nome:"NEUTRA" for nome in ATIVOS_OTC}

    def ler_grafico(self, velas, direcao):
        if len(velas) < 5: return "Poucas velas"
        obs = []
        v, v1 = velas[-1], velas[-2]
        corpo = abs(v['close'] - v['open'])
        range_total = v['high'] - v['low']
        pavio_sup = v['high'] - max(v['close'], v['open'])
        pavio_inf = min(v['close'], v['open']) - v['low']
        if direcao == 'CALL':
            if pavio_inf > corpo*2 and pavio_sup < corpo*0.3: obs.append("🔨 Martelo")
            elif corpo > abs(v1['close']-v1['open'])*1.5 and v['close'] > v1['open']: obs.append("📈 Engolfo alta")
            if pavio_sup > corpo*0.6: obs.append("⚠️ Pavio superior")
        else:
            if pavio_sup > corpo*2 and pavio_inf < corpo*0.3: obs.append("💫 Estrela cadente")
            elif corpo > abs(v1['close']-v1['open'])*1.5 and v['close'] < v1['open']: obs.append("📉 Engolfo baixa")
            if pavio_inf > corpo*0.6: obs.append("⚠️ Pavio inferior")
        if corpo > range_total*0.6: obs.append("💪 Vela forte")
        precos = [x['close'] for x in velas]
        altas = sum(1 for i in range(-5,0) if i>=-len(precos)+1 and precos[i]>precos[i-1])
        if altas >= 4: obs.append("📈 Tendência alta")
        elif altas <= 1: obs.append("📉 Tendência baixa")
        else: obs.append("↔️ Sem direção")
        if not obs: obs.append("✅ Setup neutro")
        return " | ".join(obs)

    def explicar_entrada(self, sinal, velas):
        ativo = sinal['ativo']; direcao = sinal['direcao']; conf = sinal.get('confianca',0)
        est = sinal.get('estrategia','N/A')
        leitura = self.ler_grafico(velas, direcao)
        return f"""👨‍🏫 *ANÁLISE DO TRADER*

👁️ *Gráfico:* {leitura}
🧠 *Estratégia:* {est}
🎯 *Decisão:* {direcao} com {conf:.0f}% de confiança
⚔️ *A vitória começa na execução perfeita, não no resultado.*"""

# ------------------------- BOT -------------------------
class BotProSinais:
    def __init__(self):
        self.tg = Telegram(TOKEN, CHAT)
        self.velas = {nome: deque(maxlen=100) for nome in ATIVOS_OTC}
        self.estrategias_quadrantes = EstrategiasM1()
        self.catalogador = Catalogador()
        self.trader = TraderProfessor()
        self.ult_sinal = 0
        self.sinais_enviados = 0
        self.placar = {'w': 0, 'g1': 0, 'l': 0}
        self.iq_api = None
        self.estrategia_atual = None
        self.par_atual = None

    def conectar_iq(self):
        from iqoptionapi.stable_api import IQ_Option
        email = os.environ.get('IQ_EMAIL')
        senha = os.environ.get('IQ_SENHA')
        if not email or not senha: return None
        try:
            if self.iq_api is not None:
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
            print(f"❌ Erro de conexão: {e}")
            return None

    async def atualizar_velas(self):
        if self.iq_api is None or not self.iq_api.check_connect():
            if not self.conectar_iq(): return
        for nome, ativo_id in ATIVOS_OTC.items():
            for retry in range(3):
                try:
                    c = self.iq_api.get_candles(ativo_id, 60, 80, time.time())
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
                except json.decoder.JSONDecodeError:
                    time.sleep(3)
                    self.conectar_iq()
                except Exception as e:
                    print(f"❌ Erro velas {nome}: {e}")
                    time.sleep(2)
                    if "Expecting value" in str(e): self.conectar_iq()

    def buscar_sinal(self):
        if USAR_FILTRO_HORARIO and not Filtros.horario_ok():
            return None
        for nome_par, velas in self.velas.items():
            if len(velas) < 30: continue

            # Preenche quadrantes para estratégias de quadrante
            self.estrategias_quadrantes.velas = []
            for v in velas:
                self.estrategias_quadrantes.add_vela(v['open'], v['close'], v['high'], v['low'])
            sinais_quad = self.estrategias_quadrantes.executar_todas()

            for s in sinais_quad:
                d = s['direcao']
                # Aplica todos os filtros
                if USAR_FILTRO_PAVIO and not Filtros.pavio_ok(velas, d): continue
                if USAR_FILTRO_VELA_FORTE and not Filtros.vela_forte_ok(velas): continue
                if USAR_FILTRO_EMA9 and not Filtros.sinal_alinhado_ema(velas, d): continue
                if USAR_FILTRO_SMA20 and not Filtros.sinal_alinhado_sma(velas, d): continue
                if USAR_FILTRO_RSI and not Filtros.rsi_ok(velas, d): continue
                if USAR_FILTRO_ATR and not Filtros.atr_ok(velas): continue

                return {
                    'ativo': nome_par,
                    'direcao': d,
                    'confianca': CONFIANCA_MINIMA,
                    'estrategia': s['nome'],
                    'velas': velas
                }

            # Estratégia 5-2-0
            d520, c520 = self.estrategias_quadrantes.estrategia_520(velas)
            if d520 and c520 >= CONFIANCA_MINIMA:
                if USAR_FILTRO_PAVIO and not Filtros.pavio_ok(velas, d520): pass
                elif USAR_FILTRO_VELA_FORTE and not Filtros.vela_forte_ok(velas): pass
                elif USAR_FILTRO_EMA9 and not Filtros.sinal_alinhado_ema(velas, d520): pass
                elif USAR_FILTRO_SMA20 and not Filtros.sinal_alinhado_sma(velas, d520): pass
                elif USAR_FILTRO_RSI and not Filtros.rsi_ok(velas, d520): pass
                elif USAR_FILTRO_ATR and not Filtros.atr_ok(velas): pass
                else:
                    return {'ativo': nome_par, 'direcao': d520, 'confianca': c520, 'estrategia': '5-2-0', 'velas': velas}

            # Estratégia Chinesa 3.0
            dch, cch = self.estrategias_quadrantes.chinesa_30(velas)
            if dch and cch >= CONFIANCA_MINIMA:
                if USAR_FILTRO_PAVIO and not Filtros.pavio_ok(velas, dch): pass
                elif USAR_FILTRO_VELA_FORTE and not Filtros.vela_forte_ok(velas): pass
                elif USAR_FILTRO_EMA9 and not Filtros.sinal_alinhado_ema(velas, dch): pass
                elif USAR_FILTRO_SMA20 and not Filtros.sinal_alinhado_sma(velas, dch): pass
                elif USAR_FILTRO_RSI and not Filtros.rsi_ok(velas, dch): pass
                elif USAR_FILTRO_ATR and not Filtros.atr_ok(velas): pass
                else:
                    return {'ativo': nome_par, 'direcao': dch, 'confianca': cch, 'estrategia': 'Chinesa 3.0', 'velas': velas}
        return None

    def _calcular_assertividade(self):
        total = self.placar['w'] + self.placar['g1'] + self.placar['l']
        return round(((self.placar['w'] + self.placar['g1']) / total) * 100, 1) if total > 0 else 0.0

    async def monitorar_resultado(self, sinal, horario_entrada):
        ativo = sinal['ativo']; direcao = sinal['direcao']; confianca = sinal['confianca']; estrategia = sinal['estrategia']
        agora = datetime.now(FUSO_BR)
        espera = (horario_entrada + timedelta(minutes=1) - agora).total_seconds()
        if espera > 0: await asyncio.sleep(espera)
        await asyncio.sleep(5)
        await self.atualizar_velas()
        velas = self.velas[ativo]
        ganhou = False
        for v in velas:
            if v['time'].replace(second=0) == horario_entrada:
                ganhou = v['close'] > v['open'] if direcao == 'CALL' else v['close'] < v['open']
                break
        if ganhou:
            self.placar['w'] += 1
            resultado = "✅ WIN"
            self.catalogador.registrar_resultado(estrategia, ativo, True)
        else:
            # Gale 1
            proximo_candle = horario_entrada + timedelta(minutes=1)
            agora = datetime.now(FUSO_BR)
            espera = (proximo_candle + timedelta(minutes=1) - agora).total_seconds()
            if espera > 0: await asyncio.sleep(espera)
            await asyncio.sleep(5)
            await self.atualizar_velas()
            velas = self.velas[ativo]
            ganhou_gale = False
            for v in velas:
                if v['time'].replace(second=0) == proximo_candle:
                    ganhou_gale = v['close'] > v['open'] if direcao == 'CALL' else v['close'] < v['open']
                    break
            if ganhou_gale:
                self.placar['g1'] += 1
                resultado = "✅ WIN GALE 1"
                self.catalogador.registrar_resultado(estrategia, ativo, True)
            else:
                self.placar['l'] += 1
                resultado = "❌ LOSS"
                self.catalogador.registrar_resultado(estrategia, ativo, False)
        tx = self._calcular_assertividade()
        msg = f"""{resultado}
📊 {ativo}-OTC | {direcao} {'🟢' if direcao=='CALL' else '🔴'}
📊 Placar: 🟢{self.placar['w']}W 🟡{self.placar['g1']}G1 🔴{self.placar['l']}L
🎯 Assertividade: {tx}%"""
        self.tg.send(msg)

    async def executar(self):
        banner()
        print("⚛️ Bot Pro Telegram com filtros avançados iniciando...")
        self.tg.send("🔥 *QUANTUM BOT PRO ATIVADO*\n📊 14 Estratégias | M1\n🛡️ Filtros: EMA9, SMA20, RSI, ATR, Pavio, Vela Forte, Horário\n⏱️ Sinais a cada 5min | Placar + Catalogador")
        while True:
            try:
                await self.atualizar_velas()
                sinal = self.buscar_sinal()
                if sinal and time.time() - self.ult_sinal > INTERVALO_MINIMO:
                    self.sinais_enviados += 1
                    self.ult_sinal = time.time()
                    agora = datetime.now(FUSO_BR)
                    proximo_candle = agora.replace(second=0, microsecond=0) + timedelta(minutes=1)
                    he = proximo_candle.strftime('%H:%M')
                    emoji = '🟢' if sinal['direcao']=='CALL' else '🔴'
                    msg_sinal = f"""⚛️ SINAL QUANTUM PRO ⚛️

⏰ Horário: {he}
💰 Ativo: {sinal['ativo']}-OTC
📈 Direção: {sinal['direcao']} {emoji}
⌛️ Expiração: M1
📊 Confiança: {sinal['confianca']:.0f}%
🧠 Estratégia: {sinal['estrategia']}

⚠️ Entrar somente no horário marcado.
🔄 1 recuperação (Gale 1)!"""
                    self.tg.send(msg_sinal)
                    analise = self.trader.explicar_entrada(sinal, sinal['velas'])
                    self.tg.send(analise)
                    print(f"⚛️ #{self.sinais_enviados} {sinal['ativo']}-OTC {sinal['direcao']} | {sinal['confianca']:.0f}% | {sinal['estrategia']}")
                    asyncio.create_task(self.monitorar_resultado(sinal, proximo_candle))
                await asyncio.sleep(30)
            except KeyboardInterrupt:
                print("🛑 Encerrado.")
                break
            except Exception as e:
                print(f"Erro: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    bot = BotProSinais()
    asyncio.run(bot.executar())
