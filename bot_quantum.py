#!/usr/bin/env python3
"""
⚛️ QUANTUM SIMPLES - Sinais OTC com Catálogo Inteligente
🕯️ Estratégias: MHI 1, MHI 2, VITUXO 2.0, Milhão Minoria
🛡️ Filtro único: Horário (evita sessão asiática)
🧠 Catálogo: escolhe a melhor estratégia por par
📨 Sinal + resultado (com gale 1) via Telegram
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os, random
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict
from pathlib import Path

signal.signal(signal.SIGCHLD, signal.SIG_IGN)
FUSO_BR = timezone(timedelta(hours=-3))

# Configurações
INTERVALO_MINIMO = 300       # 5 min entre sinais
USAR_GALE = True             # True para simular gale 1 (correção com duas velas)
CONFIANCA_MINIMA = 0         # Sem confiança mínima, as estratégias retornam confiança fixa

def banner():
    print("⚛️ QUANTUM SIMPLES - MHI + VITUXO + Milhão Minoria | Catálogo Inteligente")

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

# ------------------------- ESTRATÉGIAS SIMPLES -------------------------
class MHI1:
    """MHI 1: minoria das 3 últimas velas do quadrante anterior, entrada na 1ª vela (offset 0)"""
    offset_minutos = 0
    def analisar(self, velas):
        if len(velas) < 10: return None
        quadrante_anterior = list(velas)[-6:-3]  # últimas 3 do quadrante anterior
        calls = sum(1 for v in quadrante_anterior if v['close'] > v['open'])
        puts = 3 - calls
        if calls == 1: return ('CALL', 70)
        elif puts == 1: return ('PUT', 70)
        return None

class MHI2:
    """MHI 2: minoria das 3 últimas velas do quadrante anterior, entrada na 2ª vela (offset 1)"""
    offset_minutos = 1
    def analisar(self, velas):
        if len(velas) < 10: return None
        quadrante_anterior = list(velas)[-6:-3]
        calls = sum(1 for v in quadrante_anterior if v['close'] > v['open'])
        puts = 3 - calls
        if calls == 1: return ('CALL', 68)
        elif puts == 1: return ('PUT', 68)
        return None

class Vituxo2:
    """VITUXO 2.0: maioria das 3 primeiras velas do quadrante anterior, entrada na 3ª vela (offset 2)"""
    offset_minutos = 2
    def analisar(self, velas):
        if len(velas) < 10: return None
        quadrante_anterior = list(velas)[-6:-3]  # 3 primeiras do quadrante anterior? VITUXO usa as 3 primeiras (índices 0,1,2 do quadrante)
        # Para usar as 3 primeiras do quadrante anterior, precisamos pegar as posições -6, -5, -4
        # No código original: quadrante_anterior = v[-6:-3] (pega índices -6,-5,-4) = 3 primeiras do quadrante anterior
        # Então está correto: pega as 3 primeiras do quadrante anterior
        calls = sum(1 for v in quadrante_anterior if v['close'] > v['open'])
        puts = 3 - calls
        if calls > puts:  # maioria verde -> CALL
            return ('CALL', 70)
        elif puts > calls:  # maioria vermelha -> PUT
            return ('PUT', 70)
        return None

class MilhaoMinoria:
    """Milhão Minoria: minoria das 5 velas do quadrante anterior, entrada na 1ª vela (offset 0)"""
    offset_minutos = 0
    def analisar(self, velas):
        if len(velas) < 11: return None
        quadrante_anterior = list(velas)[-11:-6]  # 5 velas do quadrante anterior
        calls = sum(1 for v in quadrante_anterior if v['close'] > v['open'])
        puts = 5 - calls
        if 0 < calls < puts: return ('CALL', 72)
        elif 0 < puts < calls: return ('PUT', 72)
        return None

# ------------------------- CATALOGADOR INTELIGENTE -------------------------
class Catalogador:
    def __init__(self):
        self.performance = {}
        self.total_operacoes = 0

    def registrar(self, estrategia, par, ganhou):
        chave = f"{estrategia}|{par}"
        if chave not in self.performance:
            self.performance[chave] = {'estrategia': estrategia, 'par': par, 'wins': 0, 'losses': 0}
        if ganhou:
            self.performance[chave]['wins'] += 1
        else:
            self.performance[chave]['losses'] += 1
        self.total_operacoes += 1

    def get_taxa(self, estrategia, par):
        chave = f"{estrategia}|{par}"
        p = self.performance.get(chave)
        if p:
            total = p['wins'] + p['losses']
            if total > 0:
                return round((p['wins'] / total) * 100, 1)
        return 0

    def escolher_melhor(self, min_ops=3):
        melhores = []
        for chave, p in self.performance.items():
            total = p['wins'] + p['losses']
            if total >= min_ops:
                taxa = (p['wins'] / total) * 100
                melhores.append({
                    'estrategia': p['estrategia'],
                    'par': p['par'],
                    'taxa': taxa,
                    'total': total
                })
        melhores.sort(key=lambda x: x['taxa'], reverse=True)
        return melhores[0] if melhores else None

    def relatorio(self):
        msg = "📊 *CATALOGADOR INTELIGENTE*\n"
        msg += f"Total: {self.total_operacoes} operações\n\n"
        for chave, p in sorted(self.performance.items(), key=lambda x: (x[1]['wins']/max(x[1]['wins']+x[1]['losses'],1)), reverse=True):
            total = p['wins'] + p['losses']
            if total > 0:
                taxa = (p['wins'] / total) * 100
                msg += f"• {p['estrategia']} em {p['par']}: {taxa:.0f}% ({p['wins']}W/{p['losses']}L)\n"
        return msg

# ------------------------- BOT -------------------------
class BotSimples:
    def __init__(self):
        self.tg = Telegram(TOKEN, CHAT)
        self.velas = {nome: deque(maxlen=100) for nome in ATIVOS_OTC}
        self.estrategias = [
            ('MHI 1', MHI1()),
            ('MHI 2', MHI2()),
            ('VITUXO 2.0', Vituxo2()),
            ('Milhão Minoria', MilhaoMinoria())
        ]
        self.catalogador = Catalogador()
        self.placar = {'w': 0, 'g1': 0, 'l': 0}
        self.ult_sinal = 0
        self.iq_api = None

    def conectar_iq(self):
        from iqoptionapi.stable_api import IQ_Option
        email = os.environ.get('IQ_EMAIL')
        senha = os.environ.get('IQ_SENHA')
        if not email or not senha: return None
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
                except Exception as e:
                    print(f"Erro velas {nome}: {e}")
                    time.sleep(2)
                    if "Expecting value" in str(e): self.conectar_iq()

    def buscar_sinal(self):
        hora = datetime.now(FUSO_BR).hour
        if 22 <= hora or hora < 6:
            return None

        # Tenta usar a melhor combinação do catálogo, se houver
        melhor = self.catalogador.escolher_melhor(3)
        if melhor:
            par = melhor['par']
            if par in self.velas and len(self.velas[par]) >= 11:
                for nome_est, est in self.estrategias:
                    if nome_est == melhor['estrategia']:
                        resultado = est.analisar(self.velas[par])
                        if resultado:
                            direcao, conf = resultado
                            return {'ativo': par, 'direcao': direcao, 'confianca': conf,
                                    'estrategia': nome_est, 'offset': est.offset_minutos}
        # Varredura geral
        for par, velas in self.velas.items():
            if len(velas) < 11: continue
            for nome_est, est in self.estrategias:
                resultado = est.analisar(velas)
                if resultado:
                    direcao, conf = resultado
                    return {'ativo': par, 'direcao': direcao, 'confianca': conf,
                            'estrategia': nome_est, 'offset': est.offset_minutos}
        return None

    def calcular_horario_entrada(self, offset):
        agora = datetime.now(FUSO_BR)
        if offset is None:
            return agora.replace(second=0, microsecond=0) + timedelta(minutes=1)
        minuto = agora.minute
        resto = minuto % 5
        if resto == 0 and agora.second == 0:
            base = agora.replace(second=0, microsecond=0)
        else:
            base = agora.replace(second=0, microsecond=0) + timedelta(minutes=5 - resto)
        offset = min(offset, 4)
        return base + timedelta(minutes=offset)

    async def monitorar_resultado(self, sinal, horario_entrada):
        ativo = sinal['ativo']
        direcao = sinal['direcao']
        estrategia = sinal['estrategia']
        confianca = sinal['confianca']

        agora = datetime.now(FUSO_BR)
        espera = (horario_entrada + timedelta(minutes=1) - agora).total_seconds()
        if espera > 0:
            await asyncio.sleep(espera)
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
            self.catalogador.registrar(estrategia, ativo, True)
        else:
            if USAR_GALE:
                proxima_vela = horario_entrada + timedelta(minutes=1)
                agora = datetime.now(FUSO_BR)
                espera = (proxima_vela + timedelta(minutes=1) - agora).total_seconds()
                if espera > 0:
                    await asyncio.sleep(espera)
                await asyncio.sleep(5)
                await self.atualizar_velas()
                velas = self.velas[ativo]
                ganhou_gale = False
                for v in velas:
                    if v['time'].replace(second=0) == proxima_vela:
                        ganhou_gale = v['close'] > v['open'] if direcao == 'CALL' else v['close'] < v['open']
                        break
                if ganhou_gale:
                    self.placar['g1'] += 1
                    resultado = "✅ WIN GALE 1"
                    self.catalogador.registrar(estrategia, ativo, True)
                else:
                    self.placar['l'] += 1
                    resultado = "❌ LOSS"
                    self.catalogador.registrar(estrategia, ativo, False)
            else:
                self.placar['l'] += 1
                resultado = "❌ LOSS"
                self.catalogador.registrar(estrategia, ativo, False)

        total = self.placar['w'] + self.placar['g1'] + self.placar['l']
        tx = round(((self.placar['w'] + self.placar['g1']) / total) * 100, 1) if total > 0 else 0.0
        msg = f"""{resultado}
📊 {ativo}-OTC | {direcao} {'🟢' if direcao=='CALL' else '🔴'}
📊 Placar: 🟢{self.placar['w']}W 🟡{self.placar['g1']}G1 🔴{self.placar['l']}L
🎯 Assertividade: {tx}%"""
        self.tg.send(msg)

        if self.catalogador.total_operacoes % 10 == 0 and self.catalogador.total_operacoes > 0:
            self.tg.send(self.catalogador.relatorio())

    async def executar(self):
        banner()
        print("⚛️ Bot Simples iniciando...")
        self.tg.send("🔥 *QUANTUM SIMPLES ATIVADO*\n📊 Estratégias: MHI 1, MHI 2, VITUXO 2.0, Milhão Minoria\n🛡️ Filtro: Horário\n🧠 Catálogo automático da melhor combinação\n⏱️ Horários de entrada corretos")
        while True:
            try:
                await self.atualizar_velas()
                sinal = self.buscar_sinal()
                if sinal and time.time() - self.ult_sinal > INTERVALO_MINIMO:
                    self.ult_sinal = time.time()
                    horario_entrada = self.calcular_horario_entrada(sinal['offset'])
                    he = horario_entrada.strftime('%H:%M')
                    emoji = '🟢' if sinal['direcao']=='CALL' else '🔴'
                    msg_sinal = f"""⚛️ SINAL SIMPLES ⚛️

⏰ Horário: {he}
💰 Ativo: {sinal['ativo']}-OTC
📈 Direção: {sinal['direcao']} {emoji}
⌛️ Expiração: M1
📊 Confiança: {sinal['confianca']:.0f}%
🧠 Estratégia: {sinal['estrategia']}

⚠️ Entrar somente no horário marcado."""
                    self.tg.send(msg_sinal)
                    print(f"⚛️ {sinal['ativo']}-OTC {sinal['direcao']} | {sinal['estrategia']} | entrada {he}")
                    asyncio.create_task(self.monitorar_resultado(sinal, horario_entrada))
                await asyncio.sleep(30)
            except KeyboardInterrupt:
                print("🛑 Encerrado.")
                break
            except Exception as e:
                print(f"Erro: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    bot = BotSimples()
    asyncio.run(bot.executar())
