#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════╗
║   ⚛️  Q U A N T U M   I A   M 1   v2.0        ║
║   🔄 Gale 1 | 🧠 Cérebro Visual + Trader      ║
║   👁️ Visão Gráfica | 📈 LTA/LTB              ║
║   ⚡ MODO TURBO: +Sinais +Assertividade        ║
║   ☁️ Railway Ready | 🇧🇷 Brasília             ║
╚══════════════════════════════════════════════════╝
"""

import asyncio
import logging
import os
import signal
import sys
import json
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import requests

# ════════════════════════════════════════════════
# 🇧🇷 HORÁRIO DE BRASÍLIA
# ════════════════════════════════════════════════
os.environ["TZ"] = "America/Sao_Paulo"
time.tzset()

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

# ════════════════════════════════════════════════
# 📋 LOGGING
# ════════════════════════════════════════════════
LOG_FILE = Path("quantum_ia.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger("QuantumIA")


# ════════════════════════════════════════════════
# 🎨 CORES DO TERMINAL
# ════════════════════════════════════════════════
class Cor:
    VERDE  = "\033[92m"
    AMARELO= "\033[93m"
    VERM   = "\033[91m"
    CIANO  = "\033[96m"
    BRANCO = "\033[97m"
    NEGRITO= "\033[1m"
    RESET  = "\033[0m"
    OURO   = "\033[38;5;220m"


def limpar_tela():
    os.system("clear 2>/dev/null || cls 2>/dev/null")


def exibir_banner():
    limpar_tela()
    print(f"{Cor.OURO}{Cor.NEGRITO}╔══════════════════════════════════════════════════╗")
    print(f"║   ⚛️  Q U A N T U M   I A   M 1   v2.0        ║")
    print(f"║   🔄 Gale 1 | 🧠 Cérebro Visual + Trader      ║")
    print(f"║   ⚡ MODO TURBO | 🇧🇷 Brasília               ║")
    print(f"╚══════════════════════════════════════════════════╝{Cor.RESET}")


# ════════════════════════════════════════════════
# ✅ CONFIGURAÇÃO
# ════════════════════════════════════════════════
def carregar_config() -> dict:
    obrigatorios = ["TELEGRAM_TOKEN", "CHAT_ID", "IQ_EMAIL", "IQ_PASSWORD"]
    ausentes = [k for k in obrigatorios if not os.environ.get(k)]
    if ausentes:
        log.error(f"Variáveis de ambiente ausentes: {', '.join(ausentes)}")
        sys.exit(1)
    return {
        "token"  : os.environ["TELEGRAM_TOKEN"],
        "chat"   : os.environ["CHAT_ID"],
        "email"  : os.environ["IQ_EMAIL"],
        "senha"  : os.environ["IQ_PASSWORD"],
        "demo"   : os.environ.get("IQ_DEMO", "0") == "1",
    }


CFG = carregar_config()

try:
    from iqoptionapi.stable_api import IQ_Option
except ImportError:
    log.error("iqoptionapi não encontrada. Instale: pip install iqoptionapi")
    sys.exit(1)

# ════════════════════════════════════════════════
# 📊 PARES OTC — ampliado para 5 pares
# ════════════════════════════════════════════════
ATIVOS_OTC: dict[str, str] = {
    "EURUSD" : "EURUSD-OTC",
    "GBPUSD" : "GBPUSD-OTC",
    "EURGBP" : "EURGBP-OTC",
    "EURJPY" : "EURJPY-OTC",
    "USDJPY" : "USDJPY-OTC",
}

# Arquivo de persistência de estatísticas
STATS_FILE = Path("quantum_stats.json")


# ════════════════════════════════════════════════
# 📈 PLACAR
# ════════════════════════════════════════════════
class Placar:
    def __init__(self):
        self.wins       = 0
        self.losses     = 0
        self.gale1      = 0   # wins por gale
        self.historico  = deque(maxlen=30)
        self.sequencia  = deque(maxlen=20)   # emoji de cada resultado

    def registrar_win(self, nivel_gale: int = 0) -> str:
        self.wins += 1
        if nivel_gale == 0:
            self.sequencia.append("🟢")
            self.historico.append(1)
            return "✅ WIN"
        else:
            self.gale1 += 1
            self.sequencia.append("🟡")
            self.historico.append(1)
            return f"✅ WIN GALE {nivel_gale}"

    def registrar_loss(self) -> str:
        self.losses += 1
        self.sequencia.append("🔴")
        self.historico.append(0)
        return "❌ LOSS"

    @property
    def total(self) -> int:
        return self.wins + self.losses

    @property
    def taxa_acerto(self) -> float:
        return round((self.wins / self.total) * 100, 1) if self.total else 0.0

    def __str__(self) -> str:
        return f"🟢{self.wins}W 🟡{self.gale1}G1 🔴{self.losses}L ({self.taxa_acerto}%)"


# ════════════════════════════════════════════════
# 📡 TELEGRAM
# ════════════════════════════════════════════════
class Telegram:
    def __init__(self, token: str, chat_id: str):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id  = chat_id

    def enviar(self, texto: str, parse_mode: str = "HTML") -> bool:
        try:
            resp = requests.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": self.chat_id, "text": texto, "parse_mode": parse_mode},
                timeout=5,
            )
            if not resp.ok:
                log.warning(f"Telegram retornou {resp.status_code}: {resp.text[:100]}")
                return False
            return True
        except requests.RequestException as err:
            log.warning(f"Erro ao enviar Telegram: {err}")
            return False


# ════════════════════════════════════════════════
# 📐 UTILITÁRIOS MATEMÁTICOS
# ════════════════════════════════════════════════
def sma(dados: list | np.ndarray, periodo: int) -> float:
    dados = list(dados)
    if not dados:
        return 0.0
    trecho = dados[-periodo:] if len(dados) >= periodo else dados
    return float(np.mean(trecho))


def ema_calc(dados: np.ndarray, periodo: int) -> float:
    if len(dados) < periodo:
        return float(np.mean(dados)) if len(dados) > 0 else 0.0
    alpha = 2 / (periodo + 1)
    resultado = float(np.mean(dados[:periodo]))
    for preco in dados[periodo:]:
        resultado = (float(preco) - resultado) * alpha + resultado
    return resultado


def wma(dados: list | np.ndarray, periodo: int) -> float:
    dados = np.array(dados, dtype=float)
    if len(dados) < periodo:
        return float(np.mean(dados)) if len(dados) > 0 else 0.0
    pesos  = np.arange(1, periodo + 1, dtype=float)
    trecho = dados[-periodo:]
    return float(np.dot(trecho, pesos) / pesos.sum())


def rsi_calc(precos: np.ndarray, periodo: int = 7) -> float:
    if len(precos) < periodo + 1:
        return 50.0
    diffs  = np.diff(precos[-(periodo + 1):])
    ganhos = np.where(diffs > 0, diffs, 0.0)
    perdas = np.where(diffs < 0, -diffs, 0.0)
    mg = ganhos.mean()
    mp = perdas.mean()
    if mp == 0:
        return 100.0
    return round(100 - (100 / (1 + mg / mp)), 2)


def atr_calc(velas: list, periodo: int = 7) -> float:
    if len(velas) < 2:
        return 0.0
    trs = []
    for i in range(max(1, len(velas) - periodo), len(velas)):
        high   = velas[i]["high"]
        low    = velas[i]["low"]
        close_ant = velas[i - 1]["close"]
        trs.append(max(high - low, abs(high - close_ant), abs(low - close_ant)))
    return float(np.mean(trs)) if trs else 0.0


# ════════════════════════════════════════════════
# 🧠 ESTRATÉGIAS
# ════════════════════════════════════════════════

class Mortalha:
    """Oscilador baseado em diferença de SMAs (estilo MACD simplificado)."""

    def analisar(self, velas: list) -> tuple[Optional[str], float]:
        if len(velas) < 30:
            return None, 0.0
        try:
            closes = np.array([v["close"] for v in velas], dtype=float)
            b1 = np.zeros(len(closes))
            for i in range(len(closes)):
                if i >= 33:
                    b1[i] = sma(closes[: i + 1], 1) - sma(closes[: i + 1], 34)
            b2 = np.zeros(len(b1))
            for i in range(len(b1)):
                if i >= 3:
                    b2[i] = wma(b1[: i + 1], 4)
            if b1[-1] > b2[-1] and b1[-2] <= b2[-2]:
                conf = min(45 + abs(b1[-1] - b2[-1]) * 10_000, 90)
                return "CALL", conf
            if b1[-1] < b2[-1] and b1[-2] >= b2[-2]:
                conf = min(45 + abs(b1[-1] - b2[-1]) * 10_000, 90)
                return "PUT", conf
        except Exception as err:
            log.debug(f"Mortalha erro: {err}")
        return None, 0.0


class Formiga:
    """Combinação de EMA, CCI e OBV."""

    def analisar(self, velas: list) -> tuple[Optional[str], float]:
        if len(velas) < 12:
            return None, 0.0
        try:
            closes  = np.array([v["close"] for v in velas], dtype=float)
            highs   = np.array([v["high"]  for v in velas], dtype=float)
            lows    = np.array([v["low"]   for v in velas], dtype=float)

            ema5  = ema_calc(closes, 5)
            ema10 = ema_calc(closes, 10)
            dif   = ((ema5 - ema10) / ema10) * 100 if ema10 > 0 else 0

            tp   = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
            mtp  = np.mean(tp[-7:]) if len(tp) >= 7 else np.mean(tp)
            desv = np.mean([abs(t - mtp) for t in tp[-7:]]) if len(tp) >= 7 else 1
            cci  = (tp[-1] - mtp) / (0.015 * desv) if desv > 0 else 0

            obv = sum(
                velas[i]["volume"] if closes[i] > closes[i - 1] else -velas[i]["volume"]
                for i in range(-min(5, len(velas) - 1), 0)
            )

            sc = sp = 0
            if   dif > 0.02 : sc += 3
            elif dif > 0.005: sc += 1
            elif dif < -0.02: sp += 3
            elif dif < -0.005: sp += 1

            if   cci < -100: sc += 3
            elif cci < -60 : sc += 2
            elif cci > 100 : sp += 3
            elif cci > 60  : sp += 2

            if   obv > 200 : sc += 2
            elif obv > 50  : sc += 1
            elif obv < -200: sp += 2
            elif obv < -50 : sp += 1

            if sc >= 3 and sc > sp:
                return "CALL", min(50 + sc * 4, 88)
            if sp >= 3 and sp > sc:
                return "PUT", min(50 + sp * 4, 88)
        except Exception as err:
            log.debug(f"Formiga erro: {err}")
        return None, 0.0


class Fortaleza:
    """RSI + Bollinger + Stochastic + MACD."""

    def analisar(self, velas: list) -> tuple[Optional[str], float]:
        if len(velas) < 18:
            return None, 0.0
        try:
            closes = np.array([v["close"] for v in velas], dtype=float)
            highs  = np.array([v["high"]  for v in velas], dtype=float)
            lows   = np.array([v["low"]   for v in velas], dtype=float)

            rsi_val = rsi_calc(closes)
            media   = np.mean(closes[-10:])
            desvio  = np.std(closes[-10:])
            banda_sup = media + 2 * desvio
            banda_inf = media - 2 * desvio

            h_max = highs[-5:].max()
            l_min = lows[-5:].min()
            stoch = ((closes[-1] - l_min) / (h_max - l_min)) * 100 if h_max != l_min else 50

            macd = ema_calc(closes, 5) - ema_calc(closes, 13)

            tendencia = sum(
                1 for i in range(-min(5, len(closes) - 1), 0)
                if closes[i] > closes[i - 1]
            )

            sc = sp = 0
            if   rsi_val < 30: sc += 3
            elif rsi_val < 40: sc += 2
            if   rsi_val > 70: sp += 3
            elif rsi_val > 60: sp += 2

            if closes[-1] <= banda_inf * 1.0004: sc += 3
            if closes[-1] >= banda_sup * 0.9996: sp += 3

            if   stoch < 25: sc += 3
            elif stoch < 35: sc += 1
            if   stoch > 75: sp += 3
            elif stoch > 65: sp += 1

            if macd > 0: sc += 2
            if macd < 0: sp += 2

            if tendencia >= 4: sc += 2
            if tendencia <= 1: sp += 2

            if sc >= 6 and sc > sp:
                return "CALL", min(65 + sc * 2, 92)
            if sp >= 6 and sp > sc:
                return "PUT", min(65 + sp * 2, 92)
        except Exception as err:
            log.debug(f"Fortaleza erro: {err}")
        return None, 0.0


class RaioNegro:
    """MACD simplificado + Momentum + Força direcional."""

    def analisar(self, velas: list) -> tuple[Optional[str], float]:
        if len(velas) < 12:
            return None, 0.0
        try:
            closes = np.array([v["close"] for v in velas], dtype=float)
            ema5   = ema_calc(closes, 5)
            ema13  = ema_calc(closes, 13)
            macd   = ema5 - ema13
            sinal  = macd * 0.5
            mom    = closes[-1] - closes[-3] if len(closes) >= 3 else 0
            altas  = sum(
                1 for i in range(-min(4, len(closes) - 1), 0)
                if closes[i] > closes[i - 1]
            )
            forca  = (altas / 4) * 100

            sc = sp = 0
            if   macd > sinal and macd > 0: sc += 3
            elif macd > sinal             : sc += 1
            elif macd < sinal and macd < 0: sp += 3
            elif macd < sinal             : sp += 1

            if   mom > 0.00003 : sc += 3
            elif mom > 0       : sc += 1
            elif mom < -0.00003: sp += 3
            elif mom < 0       : sp += 1

            if   forca >= 75: sc += 3
            elif forca >= 50: sc += 2
            elif forca >= 25: sc += 1
            elif forca <= 25: sp += 2

            if sc >= 2 and sc > sp:
                return "CALL", min(48 + sc * 4, 85)
            if sp >= 2 and sp > sc:
                return "PUT", min(48 + sp * 4, 85)
        except Exception as err:
            log.debug(f"RaioNegro erro: {err}")
        return None, 0.0


class Tsunami:
    """ADX + Aroon para detecção de tendência forte."""

    def analisar(self, velas: list) -> tuple[Optional[str], float]:
        if len(velas) < 12:
            return None, 0.0
        try:
            closes = np.array([v["close"] for v in velas], dtype=float)
            highs  = np.array([v["high"]  for v in velas], dtype=float)
            lows   = np.array([v["low"]   for v in velas], dtype=float)

            n = min(7, len(velas) - 1)
            trs = [
                max(highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i]  - closes[i - 1]))
                for i in range(-n, 0)
            ]
            atr_val = np.mean(trs) if trs else 0

            plus_dm = sum(
                max(highs[i] - highs[i - 1], 0)
                for i in range(-n, 0)
                if highs[i] - highs[i - 1] > lows[i - 1] - lows[i]
            )
            minus_dm = sum(
                max(lows[i - 1] - lows[i], 0)
                for i in range(-n, 0)
                if lows[i - 1] - lows[i] > highs[i] - highs[i - 1]
            )

            pdi = (plus_dm  / atr_val) * 100 if atr_val > 0 else 0
            mdi = (minus_dm / atr_val) * 100 if atr_val > 0 else 0
            adx = abs(pdi - mdi) / (pdi + mdi) * 100 if (pdi + mdi) > 0 else 0

            recente_h = highs[-7:]
            recente_l = lows[-7:]
            aroon_up   = ((7 - list(recente_h).index(recente_h.max())) / 7) * 100 if len(recente_h) >= 7 else 50
            aroon_down = ((7 - list(recente_l).index(recente_l.min())) / 7) * 100 if len(recente_l) >= 7 else 50

            sc = sp = 0
            if   adx > 20 and pdi > mdi: sc += 4
            elif adx > 15 and pdi > mdi: sc += 3
            elif adx > 10 and pdi > mdi: sc += 1
            elif adx > 20 and mdi > pdi: sp += 4
            elif adx > 15 and mdi > pdi: sp += 3
            elif adx > 10 and mdi > pdi: sp += 1

            if   aroon_up > 70  : sc += 3
            elif aroon_up > 50  : sc += 1
            if   aroon_down > 70: sp += 3
            elif aroon_down > 50: sp += 1

            if sc >= 3 and sc > sp:
                return "CALL", min(52 + sc * 3, 90)
            if sp >= 3 and sp > sc:
                return "PUT", min(52 + sp * 3, 90)
        except Exception as err:
            log.debug(f"Tsunami erro: {err}")
        return None, 0.0


# ════════════════════════════════════════════════
# ⚛️  MOTOR DE SINAIS — QUANTUM IA
# ════════════════════════════════════════════════
class QuantumIA:
    """Agrega os votos das 5 estratégias e escolhe o melhor par."""

    MIN_ESTRATEGIAS = 2
    MAX_CONF        = 95.0

    def __init__(self):
        self.estrategias = {
            "mortalha"  : Mortalha(),
            "formiga"   : Formiga(),
            "fortaleza" : Fortaleza(),
            "raio_negro": RaioNegro(),
            "tsunami"   : Tsunami(),
        }
        # Aprendizado adaptativo: peso por estratégia baseado nos resultados
        self.pesos: dict[str, float] = {k: 1.0 for k in self.estrategias}

    def ajustar_peso(self, nome_estrategia: str, acertou: bool):
        """Reforça ou penaliza levemente o peso da estratégia."""
        fator = 1.05 if acertou else 0.95
        self.pesos[nome_estrategia] = max(0.5, min(2.0, self.pesos[nome_estrategia] * fator))

    def analisar_completo(self, velas: list) -> tuple[Optional[str], float, int, list[str]]:
        """
        Retorna: (direção, confiança_media, num_estrategias, nomes_estrategias_concordantes)
        """
        if len(velas) < 30:
            return None, 0.0, 0, []

        votos: dict[str, float] = {"CALL": 0.0, "PUT": 0.0}
        confiancas: dict[str, list] = {"CALL": [], "PUT": []}
        estrategias_ativas: dict[str, list] = {"CALL": [], "PUT": []}

        for nome, est in self.estrategias.items():
            try:
                direcao, confianca = est.analisar(velas)
                if direcao and confianca > 0:
                    peso = self.pesos.get(nome, 1.0)
                    votos[direcao] += peso
                    confiancas[direcao].append(confianca)
                    estrategias_ativas[direcao].append(nome)
            except Exception as err:
                log.debug(f"Estratégia {nome} falhou: {err}")

        for direcao in ("CALL", "PUT"):
            outro = "PUT" if direcao == "CALL" else "CALL"
            if (
                votos[direcao] >= self.MIN_ESTRATEGIAS
                and votos[direcao] > votos[outro]
                and confiancas[direcao]
            ):
                n      = len(confiancas[direcao])
                conf   = float(np.mean(confiancas[direcao]))
                bonus  = (n - 2) * 3
                conf_f = min(conf + bonus, self.MAX_CONF)
                return direcao, conf_f, n, estrategias_ativas[direcao]

        return None, 0.0, 0, []

    def melhor_par(
        self,
        velas_dict: dict[str, deque],
        bloqueados: set[str],
        stats_pares: dict,
        pares_bloqueados_corr: set[str],
    ) -> Optional[dict]:
        """Retorna o par com maior score geral."""
        melhor = None
        melhor_score = 0.0

        for nome, velas in velas_dict.items():
            if nome in bloqueados or nome in pares_bloqueados_corr:
                continue
            sp = stats_pares.get(nome, {})
            if sp.get("total", 0) >= 5 and sp.get("taxa", 100) < 45:
                continue  # par com taxa ruim — skip
            if len(velas) < 30:
                continue

            direcao, conf, n_est, nomes_est = self.analisar_completo(list(velas))
            if not direcao:
                continue

            score = conf + n_est * 6
            if sp.get("total", 0) >= 5:
                score += sp["taxa"] * 0.25

            if score > melhor_score:
                melhor_score = score
                melhor = {
                    "ativo"      : nome,
                    "direcao"    : direcao,
                    "confianca"  : conf,
                    "estrategias": n_est,
                    "nomes_est"  : nomes_est,
                }

        return melhor


# ════════════════════════════════════════════════
# 👁️  CÉREBRO VISUAL
# ════════════════════════════════════════════════
class CerebroVisual:
    SCORE_BASE       = 55
    MAX_PAVIO_RATIO  = 0.70

    def __init__(self):
        self.historico          = deque(maxlen=50)
        self.score_minimo       = self.SCORE_BASE
        self.stats_pares: dict  = {n: {"wins": 0, "losses": 0, "total": 0, "taxa": 0.0} for n in ATIVOS_OTC}
        self.tendencias: dict   = {n: "NEUTRA" for n in ATIVOS_OTC}
        self._ultima_recusa: dict = {}

        self.wins_seguidos  = 0
        self.losses_seguidos= 0
        self.em_descanso    = False
        self.descanso_ate   = 0.0

    # ── persistência ─────────────────────────────
    def salvar_stats(self):
        try:
            dados = {
                "stats_pares"   : self.stats_pares,
                "wins_seguidos" : self.wins_seguidos,
                "losses_seguidos": self.losses_seguidos,
            }
            STATS_FILE.write_text(json.dumps(dados, indent=2, ensure_ascii=False))
        except Exception as err:
            log.warning(f"Falha ao salvar stats: {err}")

    def carregar_stats(self):
        if not STATS_FILE.exists():
            return
        try:
            dados = json.loads(STATS_FILE.read_text())
            sp    = dados.get("stats_pares", {})
            for nome in ATIVOS_OTC:
                if nome in sp:
                    self.stats_pares[nome] = sp[nome]
            self.wins_seguidos   = dados.get("wins_seguidos", 0)
            self.losses_seguidos = dados.get("losses_seguidos", 0)
            log.info("📂 Estatísticas anteriores carregadas.")
        except Exception as err:
            log.warning(f"Falha ao carregar stats: {err}")

    # ── score dinâmico ───────────────────────────
    def atualizar_score_dinamico(self):
        if   self.losses_seguidos >= 3: self.score_minimo = min(self.SCORE_BASE + 15, 72)
        elif self.losses_seguidos >= 2: self.score_minimo = min(self.SCORE_BASE + 10, 65)
        elif self.wins_seguidos   >= 3: self.score_minimo = self.SCORE_BASE
        else                          : self.score_minimo = self.SCORE_BASE

    # ── descanso ─────────────────────────────────
    def verificar_descanso(self) -> tuple[bool, str]:
        if self.em_descanso:
            if time.time() < self.descanso_ate:
                volta = datetime.fromtimestamp(self.descanso_ate).strftime("%H:%M:%S")
                return True, f"😴 Em descanso até {volta}"
            self.em_descanso = False
        return False, ""

    def _ativar_descanso(self, segundos: int):
        self.em_descanso = True
        self.descanso_ate = time.time() + segundos
        volta = datetime.fromtimestamp(self.descanso_ate).strftime("%H:%M:%S")
        log.warning(f"😴 Descanso ativado até {volta} ({segundos//60}min)")

    # ── registrar resultado ───────────────────────
    def registrar_win(self):
        self.wins_seguidos   += 1
        self.losses_seguidos  = 0
        self.em_descanso      = False

    def registrar_loss(self):
        self.losses_seguidos += 1
        self.wins_seguidos    = 0
        if   self.losses_seguidos >= 3: self._ativar_descanso(1800)
        elif self.losses_seguidos >= 2: self._ativar_descanso(600)

    def registrar(self, resultado: str):
        self.historico.append(1 if resultado == "win" else 0)
        if resultado == "win":
            self.registrar_win()
        else:
            self.registrar_loss()
        self.salvar_stats()

    def atualizar_stats(self, ativo: str, resultado: str):
        if ativo not in self.stats_pares:
            self.stats_pares[ativo] = {"wins": 0, "losses": 0, "total": 0, "taxa": 0.0}
        self.stats_pares[ativo]["total"] += 1
        if resultado == "win":
            self.stats_pares[ativo]["wins"] += 1
        else:
            self.stats_pares[ativo]["losses"] += 1
        t = self.stats_pares[ativo]["total"]
        w = self.stats_pares[ativo]["wins"]
        self.stats_pares[ativo]["taxa"] = round((w / t) * 100, 1) if t else 0.0

    # ── análise de tendência ──────────────────────
    def analisar_tendencia(self, velas: list) -> str:
        if len(velas) < 21:
            return "NEUTRA"
        closes = np.array([v["close"] for v in velas], dtype=float)
        e9  = ema_calc(closes, 9)
        e21 = ema_calc(closes, 21)
        if   e9 > e21 * 1.0002: return "ALTA 📈"
        elif e9 < e21 * 0.9998: return "BAIXA 📉"
        return "NEUTRA ➡️"

    def atualizar_tendencias(self, velas_dict: dict):
        for nome, velas in velas_dict.items():
            self.tendencias[nome] = self.analisar_tendencia(list(velas))

    # ── LTA / LTB ────────────────────────────────
    def detectar_lta_ltb(self, velas: list) -> tuple[str, float, float, str]:
        if len(velas) < 20:
            return "NEUTRA", 0.0, 0.0, ""
        try:
            lows  = np.array([v["low"]  for v in velas], dtype=float)
            highs = np.array([v["high"] for v in velas], dtype=float)

            fundos = [(i, lows[i]) for i in range(2, len(lows) - 2)
                      if lows[i] < lows[i-1] and lows[i] < lows[i-2]
                      and lows[i] < lows[i+1] and lows[i] < lows[i+2]]
            topos  = [(i, highs[i]) for i in range(2, len(highs) - 2)
                      if highs[i] > highs[i-1] and highs[i] > highs[i-2]
                      and highs[i] > highs[i+1] and highs[i] > highs[i+2]]

            lta_valida = ltb_valida = False
            nivel_lta  = nivel_ltb  = 0.0
            detalhes   = ""

            if len(fundos) >= 2:
                f1, f2 = fundos[-2], fundos[-1]
                if f2[1] > f1[1]:
                    lta_valida = True
                    slope      = (f2[1] - f1[1]) / max(f2[0] - f1[0], 1)
                    nivel_lta  = f2[1] + slope * (len(velas) - f2[0])
                    detalhes  += f"LTA({f1[1]:.5f}→{f2[1]:.5f}) "

            if len(topos) >= 2:
                t1, t2 = topos[-2], topos[-1]
                if t2[1] < t1[1]:
                    ltb_valida = True
                    slope      = (t2[1] - t1[1]) / max(t2[0] - t1[0], 1)
                    nivel_ltb  = t2[1] + slope * (len(velas) - t2[0])
                    detalhes  += f"LTB({t1[1]:.5f}→{t2[1]:.5f}) "

            if   lta_valida and ltb_valida: return "DUPLA", nivel_lta, nivel_ltb, detalhes
            elif lta_valida               : return "LTA",   nivel_lta, nivel_ltb, detalhes
            elif ltb_valida               : return "LTB",   nivel_lta, nivel_ltb, detalhes
        except Exception as err:
            log.debug(f"LTA/LTB erro: {err}")
        return "NEUTRA", 0.0, 0.0, ""

    def filtro_lta_ltb(self, velas: list, direcao: str) -> tuple[bool, str]:
        tipo, nivel_lta, nivel_ltb, _ = self.detectar_lta_ltb(velas)
        if tipo == "NEUTRA":
            return True, ""
        preco = velas[-1]["close"]
        if direcao == "CALL":
            if tipo in ("LTA", "DUPLA") and preco < nivel_lta * 0.9995:
                return False, f"📈 Abaixo da LTA ({nivel_lta:.5f})"
            if tipo == "LTB" and preco < nivel_ltb * 1.0005:
                return False, f"📉 Abaixo da LTB ({nivel_ltb:.5f})"
        if direcao == "PUT":
            if tipo in ("LTB", "DUPLA") and preco > nivel_ltb * 1.0005:
                return False, f"📉 Acima da LTB ({nivel_ltb:.5f})"
            if tipo == "LTA" and preco > nivel_lta * 0.9995:
                return False, f"📈 Acima da LTA ({nivel_lta:.5f})"
        return True, ""

    # ── avaliação visual (padrões de candle) ──────
    def avaliacao_visual(self, velas: list, direcao: str) -> tuple[float, str]:
        if len(velas) < 10:
            return 50.0, "Poucas velas"
        nota     = 50.0
        detalhes = []
        try:
            highs = np.array([v["high"] for v in velas], dtype=float)
            lows  = np.array([v["low"]  for v in velas], dtype=float)
            v_ult = velas[-1]
            v_ant = velas[-2]

            # Fundo / topo ascendente
            if direcao == "CALL" and lows[-1] > np.min(lows[-5:]) * 1.0002:
                nota += 10; detalhes.append("Fundo ascendente")
            elif direcao == "PUT" and highs[-1] < np.max(highs[-5:]) * 0.9998:
                nota += 10; detalhes.append("Topo descendente")

            # Padrões de candle
            corpo       = abs(v_ult["close"] - v_ult["open"])
            pavio_sup   = v_ult["high"] - max(v_ult["close"], v_ult["open"])
            pavio_inf   = min(v_ult["close"], v_ult["open"]) - v_ult["low"]
            corpo_ant   = abs(v_ant["close"] - v_ant["open"])

            if corpo > 0:
                if direcao == "CALL" and pavio_inf > corpo * 2 and pavio_sup < corpo * 0.3:
                    nota += 15; detalhes.append("🔨 Martelo")
                elif direcao == "PUT" and pavio_sup > corpo * 2 and pavio_inf < corpo * 0.3:
                    nota += 15; detalhes.append("⭐ Estrela Cadente")
                elif corpo > corpo_ant * 1.5:
                    if direcao == "CALL" and v_ult["close"] > v_ant["open"]:
                        nota += 15; detalhes.append("🐂 Engolfo Alta")
                    elif direcao == "PUT" and v_ult["close"] < v_ant["open"]:
                        nota += 15; detalhes.append("🐻 Engolfo Baixa")

            # Força visual (últimas 4 velas)
            closes = np.array([v["close"] for v in velas], dtype=float)
            altas  = sum(1 for i in range(-4, 0) if closes[i] > closes[i - 1])
            if direcao == "CALL" and altas >= 3:
                nota += 10; detalhes.append("Força visual ↑")
            elif direcao == "PUT" and altas <= 1:
                nota += 10; detalhes.append("Força visual ↓")

            # Sem rejeição
            if corpo > 0:
                if direcao == "CALL" and pavio_sup < corpo * 0.2:
                    nota += 5; detalhes.append("Sem rejeição sup")
                elif direcao == "PUT" and pavio_inf < corpo * 0.2:
                    nota += 5; detalhes.append("Sem rejeição inf")

            # LTA/LTB
            _, _, _, det_tend = self.detectar_lta_ltb(velas)
            if det_tend:
                detalhes.append(det_tend.strip())

        except Exception as err:
            log.debug(f"Avaliação visual erro: {err}")

        return min(nota, 100), ", ".join(detalhes) if detalhes else "Setup neutro"

    # ── filtros ───────────────────────────────────
    def _filtro_pavio(self, velas: list, direcao: str) -> tuple[bool, str]:
        try:
            v     = velas[-1]
            corpo = abs(v["close"] - v["open"])
            if corpo == 0:
                return True, ""
            if direcao == "CALL":
                ratio = (v["high"] - max(v["close"], v["open"])) / corpo
                if ratio > self.MAX_PAVIO_RATIO:
                    return False, f"🕯️ Pavio superior grande ({ratio:.1f}x)"
            else:
                ratio = (min(v["close"], v["open"]) - v["low"]) / corpo
                if ratio > self.MAX_PAVIO_RATIO:
                    return False, f"🕯️ Pavio inferior grande ({ratio:.1f}x)"
        except Exception as err:
            log.debug(f"Filtro pavio erro: {err}")
        return True, ""

    def _filtro_tendencia(self, velas: list, direcao: str) -> tuple[bool, str]:
        try:
            if len(velas) < 20:
                return True, ""
            closes = np.array([v["close"] for v in velas], dtype=float)
            e9     = ema_calc(closes, 9)
            e21    = ema_calc(closes, 21)
            diff   = abs(e9 - e21) / e21 if e21 != 0 else 0
            if diff < 0.001:
                return True, ""  # tendência muito fraca — neutro
            if direcao == "CALL" and e9 <= e21:
                return False, "📈 EMA9 < EMA21 (contra tendência)"
            if direcao == "PUT" and e9 >= e21:
                return False, "📉 EMA9 > EMA21 (contra tendência)"
        except Exception as err:
            log.debug(f"Filtro tendência erro: {err}")
        return True, ""

    def _filtro_volatilidade(self, velas: list) -> tuple[bool, str]:
        try:
            if len(velas) < 10:
                return True, ""
            closes = np.array([v["close"] for v in velas[-10:]], dtype=float)
            vol    = np.std(closes) / np.mean(closes) if closes.mean() > 0 else 0
            if vol > 0.003:
                return False, f"⚡ Volatilidade excessiva ({vol:.4f})"
            if vol < 0.00003:
                return False, f"😴 Mercado parado ({vol:.5f})"
        except Exception as err:
            log.debug(f"Filtro volatilidade erro: {err}")
        return True, ""

    def _filtro_volume(self, velas: list) -> tuple[bool, str]:
        try:
            if len(velas) < 10:
                return True, ""
            vols      = [v["volume"] for v in velas[-10:]]
            vol_atual = vols[-1]
            vol_medio = np.mean(vols[:-1]) if len(vols) > 1 else vol_atual
            if vol_medio > 0 and vol_atual < vol_medio * 0.8:
                return False, f"📊 Volume baixo ({vol_atual:.0f} < {vol_medio * 0.8:.0f})"
        except Exception as err:
            log.debug(f"Filtro volume erro: {err}")
        return True, ""

    def _filtro_zona_seguranca(self, velas: list) -> tuple[bool, str]:
        try:
            if len(velas) < 20:
                return True, ""
            highs      = np.array([v["high"] for v in velas], dtype=float)
            lows       = np.array([v["low"]  for v in velas], dtype=float)
            resistencia= highs[-20:].max()
            suporte    = lows[-20:].min()
            preco      = velas[-1]["close"]
            if abs(preco - resistencia) / preco < 0.0003:
                return False, f"🛡️ Próximo à resistência ({resistencia:.5f})"
            if abs(preco - suporte) / preco < 0.0003:
                return False, f"🛡️ Próximo ao suporte ({suporte:.5f})"
        except Exception as err:
            log.debug(f"Filtro zona erro: {err}")
        return True, ""

    def _filtro_horario(self) -> tuple[bool, str]:
        hora = datetime.now().hour
        if hora < 6:
            return False, f"🌙 Horário de baixa liquidez ({hora}h)"
        return True, ""

    def _pode_exibir_recusa(self, par: str, direcao: str) -> bool:
        chave = f"{par}_{direcao}"
        agora = time.time()
        if agora - self._ultima_recusa.get(chave, 0) < 300:
            return False
        self._ultima_recusa[chave] = agora
        return True

    def filtrar_correlacao(self, sinais: dict) -> set[str]:
        """Bloqueia EUR/GBP se EURUSD e GBPUSD divergem."""
        bloqueados = set()
        if "EURUSD" in sinais and "GBPUSD" in sinais:
            if sinais["EURUSD"]["direcao"] != sinais["GBPUSD"]["direcao"]:
                bloqueados.update(["EURUSD", "GBPUSD"])
        return bloqueados

    # ── avaliação final ───────────────────────────
    def avaliar(self, sinal: dict, velas: list, sinais_por_par: dict = None) -> tuple[bool, float, list[str], float, str]:
        direcao = sinal.get("direcao", "")
        ativo   = sinal.get("ativo", "")

        em_descanso, msg = self.verificar_descanso()
        if em_descanso:
            return False, 0.0, [msg], 0.0, ""

        self.atualizar_score_dinamico()

        checks = [
            self._filtro_horario(),
            self.filtro_lta_ltb(velas, direcao),
            self._filtro_pavio(velas, direcao),
            self._filtro_tendencia(velas, direcao),
            self._filtro_volatilidade(velas),
            self._filtro_volume(velas),
            self._filtro_zona_seguranca(velas),
        ]
        for ok, msg_filtro in checks:
            if not ok:
                mostrar = self._pode_exibir_recusa(ativo, direcao)
                return False, 0.0, [msg_filtro if mostrar else "__SILENCIADO__"], 0.0, ""

        nota_visual, det_visual = self.avaliacao_visual(velas, direcao)
        if nota_visual < 45:
            return False, 0.0, [f"👁️ Gráfico ruim ({det_visual})"], nota_visual, det_visual

        # Composição do score
        score   = 0.0
        motivos = []

        conf = sinal.get("confianca", 0)
        score += (conf / 100) * 35
        if conf >= 70: motivos.append(f"Confiança alta ({conf:.0f}%)")

        n_est = sinal.get("estrategias", 0)
        score += (n_est / 5) * 25
        if n_est >= 3: motivos.append(f"{n_est}/5 estratégias")

        hora = datetime.now().hour
        if   8 <= hora <= 17: score += 20; motivos.append("Horário nobre")
        elif 6 <= hora <= 23: score += 10

        if self.historico and np.mean(self.historico) > 0.65:
            score += 10; motivos.append("Histórico positivo")

        score += (nota_visual / 100) * 15
        motivos.append(f"👁️ {det_visual}")

        aprovado = score >= self.score_minimo
        return aprovado, score, motivos, nota_visual, det_visual


# ════════════════════════════════════════════════
# 🔌 CONEXÃO IQ OPTION
# ════════════════════════════════════════════════
class IQAPI:
    MAX_TENTATIVAS  = 5
    CANDLES_PADRAO  = 80

    def __init__(self, email: str, senha: str, ativos: dict[str, str], demo: bool = False):
        self.email  = email
        self.senha  = senha
        self.ativos = ativos
        self.demo   = demo
        self.api: Optional[IQ_Option] = None
        self.conectado = False
        self.erros     = 0
        self.velas: dict[str, deque] = {n: deque(maxlen=100) for n in ativos}

    def conectar(self) -> bool:
        for tentativa in range(1, self.MAX_TENTATIVAS + 1):
            try:
                if self.api:
                    try: self.api.close()
                    except: pass
                    time.sleep(2)

                self.api = IQ_Option(self.email, self.senha)
                ok, motivo = self.api.connect()
                if ok:
                    self.conectado = True
                    self.erros     = 0
                    tipo           = "DEMO" if self.demo else "REAL"
                    log.info(f"✅ Conectado à IQ Option [{tipo}]")
                    return True

                log.warning(f"Tentativa {tentativa}/{self.MAX_TENTATIVAS}: {motivo}")
                time.sleep(5 * tentativa)
            except Exception as err:
                log.warning(f"Erro na conexão ({tentativa}/{self.MAX_TENTATIVAS}): {err}")
                time.sleep(5 * tentativa)

        self.conectado = False
        return False

    def _nome_para_id(self, ativo_id: str) -> Optional[str]:
        for n, v in self.ativos.items():
            if v == ativo_id:
                return n
        return None

    def obter_velas(self, ativo_id: str, qtd: int = CANDLES_PADRAO) -> int:
        for retry in range(3):
            if not self.conectado and not self.conectar():
                return 0
            try:
                candles = self.api.get_candles(ativo_id, 60, qtd, time.time())
                if not candles:
                    time.sleep(2)
                    continue

                nome = self._nome_para_id(ativo_id)
                if not nome:
                    return 0

                self.velas[nome].clear()
                for c in candles[-qtd:]:
                    if not isinstance(c, dict):
                        continue
                    try:
                        self.velas[nome].append({
                            "time"  : datetime.fromtimestamp(c.get("from", 0)),
                            "open"  : float(c["open"]),
                            "high"  : float(c["max"]),
                            "low"   : float(c["min"]),
                            "close" : float(c["close"]),
                            "volume": int(c.get("volume", 0)),
                        })
                    except (KeyError, ValueError) as e:
                        log.debug(f"Vela inválida: {e}")

                return len(candles)

            except Exception as err:
                log.warning(f"obter_velas erro (retry {retry+1}): {err}")
                self.conectado = False
                if retry < 2:
                    time.sleep(3)

        return 0

    def atualizar(self):
        if not self.conectado:
            self.conectar()
        for nome, ativo_id in self.ativos.items():
            try:
                self.obter_velas(ativo_id)
            except Exception as err:
                log.warning(f"Falha ao atualizar {nome}: {err}")


# ════════════════════════════════════════════════
# 🤖 BOT PRINCIPAL
# ════════════════════════════════════════════════
class Bot:
    INTERVALO_MINIMO_PAR = 180  # segundos entre sinais do mesmo par

    def __init__(self):
        self.tg       = Telegram(CFG["token"], CFG["chat"])
        self.ia       = QuantumIA()
        self.placar   = Placar()
        self.iq       = IQAPI(CFG["email"], CFG["senha"], ATIVOS_OTC, demo=CFG["demo"])
        self.cerebro  = CerebroVisual()

        self.op_ativa         = False
        self.sinal_atual: Optional[dict] = None
        self.ultimo_sinal_ts  = 0.0
        self.total_sinais     = 0
        self.total_recusados  = 0
        self.ultimo_sinal_por_par: dict[str, float] = {}
        self.lta_ltb_info: dict[str, str] = {n: "" for n in ATIVOS_OTC}

    # ── helpers ──────────────────────────────────
    def _pode_enviar_par(self, ativo: str) -> bool:
        return time.time() - self.ultimo_sinal_por_par.get(ativo, 0) >= self.INTERVALO_MINIMO_PAR

    def _registrar_envio(self, ativo: str):
        self.ultimo_sinal_por_par[ativo] = time.time()

    def _bateu(self, direcao: str, preco_entrada: float, vela: dict) -> bool:
        return vela["high"] > preco_entrada if direcao == "CALL" else vela["low"] < preco_entrada

    # ── formatação Telegram ───────────────────────
    def _fmt_sinal(self, s: dict) -> str:
        horario = (
            datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)
        ).strftime("%H:%M")
        emoji_dir  = "🟢" if s["direcao"] == "CALL" else "🔴"
        nomes_est  = ", ".join(s.get("nomes_est", [])) or "—"
        return (
            f"<b>⚛️ SINAL QUANTUM IA v2 ⚛️</b>\n\n"
            f"⏰ <b>Horário:</b> {horario}\n"
            f"💰 <b>Ativo:</b> {s['ativo']}-OTC\n"
            f"📈 <b>Direção:</b> {s['direcao']} {emoji_dir}\n"
            f"⌛️ <b>Expiração:</b> M1\n"
            f"📊 <b>Confiança:</b> {s['confianca']:.0f}%\n"
            f"🧠 <b>Estratégias:</b> {s['estrategias']}/5 ({nomes_est})\n"
            f"🛡️ <b>Score IA:</b> {s.get('score_ia', 0):.0f}/{self.cerebro.score_minimo}\n\n"
            f"⚠️ Entrar somente no horário marcado.\n"
            f"🔄 1 recuperação (Gale 1)!"
        )

    def _fmt_resultado(self, resultado: str, sinal: dict) -> str:
        emoji_dir = "🟢" if sinal["direcao"] == "CALL" else "🔴"
        return (
            f"{resultado}\n"
            f"📊 <b>{sinal['ativo']}-OTC</b> | {sinal['direcao']} {emoji_dir}\n"
            f"📊 Placar: {self.placar}"
        )

    # ── aguarda próxima vela ──────────────────────
    async def _aguardar_vela(self, segundos_extra: int = 60):
        try:
            agora   = datetime.now()
            proxima = agora.replace(second=0, microsecond=0) + timedelta(minutes=1)
            proxima += timedelta(seconds=segundos_extra)
            espera  = max(0, (proxima - agora).total_seconds())
            if espera > 0:
                await asyncio.sleep(espera)
                self.iq.atualizar()
        except Exception as err:
            log.debug(f"aguardar_vela erro: {err}")

    # ── acompanhamento da operação ────────────────
    async def _acompanhar_operacao(self, sinal: dict):
        ativo    = sinal["ativo"]
        direcao  = sinal["direcao"]
        try:
            # Aguarda abertura da vela de entrada
            await self._aguardar_vela(10)
            velas = self.iq.velas[ativo]
            if len(velas) < 2:
                log.warning(f"Sem velas suficientes para {ativo}")
                self.op_ativa = False
                return

            preco_entrada = float(list(velas)[-1]["open"])
            hora_vela     = list(velas)[-1]["time"].strftime("%H:%M")
            log.info(f"⚛️  {ativo}-OTC {direcao} | OPEN: {preco_entrada:.5f} | Vela: {hora_vela}")

            # Aguarda fechamento
            await self._aguardar_vela(5)
            velas = self.iq.velas[ativo]

            if velas and self._bateu(direcao, preco_entrada, list(velas)[-1]):
                resultado = self.placar.registrar_win(0)
                log.info(f"✅ {resultado}")
                self.tg.enviar(self._fmt_resultado(resultado, sinal))
                self.cerebro.registrar("win")
                self.cerebro.atualizar_stats(ativo, "win")
                for nome_est in sinal.get("nomes_est", []):
                    self.ia.ajustar_peso(nome_est, True)
                self.op_ativa = False
                return

            # Gale 1
            log.info(f"❌ Principal perdeu — iniciando Gale 1")
            velas         = self.iq.velas[ativo]
            preco_gale    = float(list(velas)[-1]["open"]) if velas else preco_entrada
            log.info(f"🔄 GALE 1 | OPEN: {preco_gale:.5f}")

            await self._aguardar_vela(5)
            velas = self.iq.velas[ativo]

            if velas and self._bateu(direcao, preco_gale, list(velas)[-1]):
                resultado = self.placar.registrar_win(1)
                log.info(f"✅ {resultado}")
                self.tg.enviar(self._fmt_resultado(resultado, sinal))
                self.cerebro.registrar("win")
                self.cerebro.atualizar_stats(ativo, "win")
                for nome_est in sinal.get("nomes_est", []):
                    self.ia.ajustar_peso(nome_est, True)
                self.op_ativa = False
                return

            # Loss total
            resultado = self.placar.registrar_loss()
            log.info(f"🔴 {resultado}")
            self.tg.enviar(self._fmt_resultado(resultado, sinal))
            self.cerebro.registrar("loss")
            self.cerebro.atualizar_stats(ativo, "loss")
            for nome_est in sinal.get("nomes_est", []):
                self.ia.ajustar_peso(nome_est, False)

        except Exception as err:
            log.error(f"Erro no acompanhamento: {err}")
        finally:
            self.op_ativa = False

    # ── catalogação inicial ───────────────────────
    async def _catalogar(self):
        log.info(f"{'─'*55}")
        log.info("📊 CATALOGAÇÃO INICIAL (80 velas históricas)")
        log.info(f"{'─'*55}")
        for nome in ATIVOS_OTC:
            velas = list(self.iq.velas[nome])
            if len(velas) < 35:
                log.warning(f"⚠️ {nome}: poucas velas ({len(velas)})")
                continue
            wins = total = 0
            for i in range(35, len(velas) - 1):
                janela   = velas[i - 35 : i + 1]
                direcao, _, _, _ = self.ia.analisar_completo(janela)
                if direcao:
                    total += 1
                    prox   = velas[i + 1]
                    if self._bateu(direcao, prox["open"], prox):
                        wins += 1
            if total:
                taxa = round((wins / total) * 100, 1)
                self.cerebro.stats_pares[nome] = {"wins": wins, "losses": total - wins, "total": total, "taxa": taxa}
                log.info(f"  ✅ {nome}: {wins}/{total} acertos ({taxa}%)")
            else:
                log.info(f"  ⚠️ {nome}: nenhum sinal encontrado")
        log.info(f"{'─'*55}")

    # ── dashboard no console ──────────────────────
    def _exibir_dashboard(self):
        agora     = datetime.now()
        w, l, g1  = self.placar.wins, self.placar.losses, self.placar.gale1
        tx        = self.placar.taxa_acerto
        bloq      = [a for a in ATIVOS_OTC if not self._pode_enviar_par(a)]
        tend_str  = " | ".join(f"{n}:{self.cerebro.tendencias[n]}" for n in ATIVOS_OTC)
        stats_str = " | ".join(f"{n}:{self.cerebro.stats_pares[n]['taxa']}%" for n in ATIVOS_OTC)
        lta_str   = " | ".join(
            f"{n}:{self.lta_ltb_info[n]}" if self.lta_ltb_info[n] else f"{n}:--"
            for n in ATIVOS_OTC
        )
        pesos_str = " | ".join(f"{k[0:3]}:{v:.2f}" for k, v in self.ia.pesos.items())
        desc_icon = "😴" if self.cerebro.em_descanso else ""
        bloq_str  = f" | 🔒 {','.join(bloq)}" if bloq else ""
        L = "──────────────────────────────────────────────────────────"
        print(f"{Cor.OURO}┌{L}┐{Cor.RESET}")
        print(f"{Cor.OURO}│{Cor.RESET} ⏰ {agora.strftime('%H:%M:%S')} │ 📨 {self.total_sinais} sinais │ 🏆 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}% │ 🛡️ {self.total_recusados} recusados {desc_icon}{bloq_str}")
        print(f"{Cor.OURO}│{Cor.RESET} 📈 {tend_str} │ Score mín: {self.cerebro.score_minimo}")
        print(f"{Cor.OURO}│{Cor.RESET} 📐 {lta_str}")
        print(f"{Cor.OURO}│{Cor.RESET} 📊 {stats_str}")
        print(f"{Cor.OURO}│{Cor.RESET} 🧠 Pesos: {pesos_str}")
        print(f"{Cor.OURO}└{L}┘{Cor.RESET}")

    # ── loop principal ────────────────────────────
    async def run(self):
        exibir_banner()
        log.info("Iniciando Quantum IA v2 MODO TURBO...")

        if not self.iq.conectar():
            log.error("Falha crítica na conexão com IQ Option.")
            return

        self.iq.atualizar()
        self.cerebro.carregar_stats()
        await self._catalogar()

        log.info("✅ QUANTUM IA v2 ATIVA | 5 pares OTC | 5 estratégias | Aprendizado adaptativo")
        self.tg.enviar(
            f"<b>⚛️ QUANTUM IA v2 TURBO</b>\n"
            f"📊 {len(ATIVOS_OTC)} pares OTC\n"
            f"⚡ +Sinais +Assertividade\n"
            f"🧠 Aprendizado adaptativo\n"
            f"🇧🇷 Horário de Brasília\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )

        while True:
            try:
                agora = datetime.now()

                # Atualiza velas a cada 30 s
                if agora.second in (0, 30):
                    try:
                        self.iq.atualizar()
                        self.cerebro.atualizar_tendencias(self.iq.velas)
                    except Exception as err:
                        log.warning(f"Falha ao atualizar velas: {err}")
                        self.iq.conectado = False

                    for nome in ATIVOS_OTC:
                        velas = list(self.iq.velas[nome])
                        if len(velas) >= 20:
                            tipo, _, _, det = self.cerebro.detectar_lta_ltb(velas)
                            self.lta_ltb_info[nome] = tipo if tipo != "NEUTRA" else ""

                # Busca sinais quando não há operação aberta
                if not self.op_ativa:
                    try:
                        bloqueados     = {a for a in ATIVOS_OTC if not self._pode_enviar_par(a)}
                        sinais_por_par = {}

                        for nome in ATIVOS_OTC:
                            if nome in bloqueados or len(self.iq.velas[nome]) < 30:
                                continue
                            direcao, cf, n_est, nomes_est = self.ia.analisar_completo(list(self.iq.velas[nome]))
                            if direcao:
                                sinais_por_par[nome] = {"direcao": direcao, "confianca": cf, "estrategias": n_est}

                        corr_bloq = self.cerebro.filtrar_correlacao(sinais_por_par)
                        sinal     = self.ia.melhor_par(
                            self.iq.velas, bloqueados, self.cerebro.stats_pares, corr_bloq
                        )

                        if sinal and time.time() - self.ultimo_sinal_ts > 25:
                            velas_ativo = list(self.iq.velas[sinal["ativo"]])
                            aprovado, score, motivos, nota_vis, det_vis = self.cerebro.avaliar(
                                sinal, velas_ativo, sinais_por_par
                            )

                            if aprovado:
                                self.op_ativa       = True
                                self.sinal_atual    = sinal
                                self.total_sinais  += 1
                                self.ultimo_sinal_ts= time.time()
                                self._registrar_envio(sinal["ativo"])
                                sinal["score_ia"]   = score

                                horario_entrada = (
                                    agora.replace(second=0, microsecond=0) + timedelta(minutes=1)
                                ).strftime("%H:%M")
                                log.info(
                                    f"⚛️  #{self.total_sinais} {sinal['ativo']}-OTC {sinal['direcao']} "
                                    f"| {sinal['confianca']:.0f}% | 🧠{sinal['estrategias']}/5 "
                                    f"| 🛡️{score:.0f}/{self.cerebro.score_minimo} "
                                    f"| 👁️{nota_vis:.0f}/100 | ⏰ {horario_entrada}"
                                )
                                self.tg.enviar(self._fmt_sinal(sinal))
                                asyncio.create_task(self._acompanhar_operacao(sinal))

                            else:
                                motivos_visiveis = [m for m in motivos if m != "__SILENCIADO__"]
                                if motivos_visiveis:
                                    self.total_recusados += 1
                                    log.info(
                                        f"🧠 Recusado {sinal['ativo']}-OTC {sinal['direcao']}: "
                                        f"{', '.join(motivos_visiveis)} (Score: {score:.0f}/{self.cerebro.score_minimo})"
                                    )

                    except Exception as err:
                        log.warning(f"Erro na análise: {err}")

                # Dashboard a cada 30 s
                if agora.second in (0, 30):
                    try:
                        self._exibir_dashboard()
                    except Exception as err:
                        log.debug(f"Dashboard erro: {err}")

                await asyncio.sleep(3)

            except KeyboardInterrupt:
                limpar_tela()
                msg_final = (
                    f"\n👋 Encerrando Quantum IA\n"
                    f"{self.placar}\n"
                    f"📨 {self.total_sinais} sinais | 🛡️ {self.total_recusados} recusados\n"
                )
                log.info(msg_final)
                self.tg.enviar(
                    f"⚠️ <b>Desligado</b>\n"
                    f"{self.placar}\n"
                    f"🛡️ {self.total_recusados} recusados"
                )
                self.cerebro.salvar_stats()
                break

            except Exception as err:
                log.error(f"Erro no loop principal: {err}")
                self.iq.conectado = False
                await asyncio.sleep(5)


# ════════════════════════════════════════════════
if __name__ == "__main__":
    asyncio.run(Bot().run())
