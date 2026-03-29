"""
Módulo de cálculos de Matemática Financiera
Cubre: Interés Simple, Interés Compuesto, Anualidades, Gradientes,
       Amortización (Francés, Alemán, Americano), Conversión de Tasas,
       VPN/TIR
"""

import numpy as np
import pandas as pd
from typing import Optional


# ─────────────────────────────────────────────
# CONVERSIÓN DE TASAS
# ─────────────────────────────────────────────

def tasa_nominal_a_efectiva(tasa_nominal: float, m: int) -> float:
    """Convierte tasa nominal capitalizable m veces por período a efectiva."""
    return (1 + tasa_nominal / m) ** m - 1


def tasa_efectiva_a_nominal(tasa_efectiva: float, m: int) -> float:
    """Convierte tasa efectiva a nominal capitalizable m veces por período."""
    return m * ((1 + tasa_efectiva) ** (1 / m) - 1)


def tasa_equivalente(tasa: float, n_origen: int, n_destino: int) -> float:
    """
    Convierte una tasa efectiva de un período a otro equivalente.
    n_origen: número de subperíodos en el período base de la tasa original
    n_destino: número de subperíodos en el período al que se desea convertir
    Ejemplo: tasa mensual (n_origen=12, n_destino=1) → tasa anual
             tasa anual (n_origen=1, n_destino=12) → tasa mensual
    """
    return (1 + tasa) ** (n_origen / n_destino) - 1


def tasa_efectiva_periodica(tasa_efectiva_anual: float, m: int) -> float:
    """Tasa efectiva periódica dada tasa efectiva anual y número de períodos por año."""
    return (1 + tasa_efectiva_anual) ** (1 / m) - 1


# ─────────────────────────────────────────────
# INTERÉS SIMPLE
# ─────────────────────────────────────────────

def interes_simple_monto_final(capital: float, tasa: float, tiempo: float) -> float:
    """Monto final con interés simple. I = C * i * t"""
    return capital * (1 + tasa * tiempo)


def interes_simple_interes(capital: float, tasa: float, tiempo: float) -> float:
    return capital * tasa * tiempo


def interes_simple_capital(monto: float, tasa: float, tiempo: float) -> float:
    return monto / (1 + tasa * tiempo)


def interes_simple_tasa(capital: float, monto: float, tiempo: float) -> float:
    return (monto / capital - 1) / tiempo


def interes_simple_tiempo(capital: float, monto: float, tasa: float) -> float:
    return (monto / capital - 1) / tasa


def tabla_interes_simple(capital: float, tasa: float, tiempo: float) -> pd.DataFrame:
    periodos = int(tiempo)
    rows = []
    saldo = capital
    for t in range(1, periodos + 1):
        interes = capital * tasa
        saldo = capital + capital * tasa * t
        rows.append({
            "Período": t,
            "Saldo Inicial": capital,
            "Interés del Período": interes,
            "Saldo Final": saldo,
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# INTERÉS COMPUESTO
# ─────────────────────────────────────────────

def interes_compuesto_monto_final(capital: float, tasa: float, n: float) -> float:
    """Valor Futuro con interés compuesto. VF = VP * (1+i)^n"""
    return capital * (1 + tasa) ** n


def interes_compuesto_valor_presente(monto: float, tasa: float, n: float) -> float:
    """Valor Presente. VP = VF / (1+i)^n"""
    return monto / (1 + tasa) ** n


def interes_compuesto_tasa(capital: float, monto: float, n: float) -> float:
    return (monto / capital) ** (1 / n) - 1


def interes_compuesto_tiempo(capital: float, monto: float, tasa: float) -> float:
    return np.log(monto / capital) / np.log(1 + tasa)


def tabla_interes_compuesto(capital: float, tasa: float, n: int) -> pd.DataFrame:
    rows = []
    saldo = capital
    for t in range(1, n + 1):
        interes = saldo * tasa
        saldo_nuevo = saldo * (1 + tasa)
        rows.append({
            "Período": t,
            "Saldo Inicial": saldo,
            "Interés del Período": interes,
            "Saldo Final": saldo_nuevo,
        })
        saldo = saldo_nuevo
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# ANUALIDADES
# ─────────────────────────────────────────────

def anualidad_cuota_ordinaria(vp: float, tasa: float, n: int) -> float:
    """Cuota de anualidad vencida dado VP."""
    if tasa == 0:
        return vp / n
    return vp * tasa * (1 + tasa) ** n / ((1 + tasa) ** n - 1)


def anualidad_vp_ordinaria(cuota: float, tasa: float, n: int) -> float:
    """Valor Presente de anualidad vencida."""
    if tasa == 0:
        return cuota * n
    return cuota * ((1 + tasa) ** n - 1) / (tasa * (1 + tasa) ** n)


def anualidad_vf_ordinaria(cuota: float, tasa: float, n: int) -> float:
    """Valor Futuro de anualidad vencida."""
    if tasa == 0:
        return cuota * n
    return cuota * ((1 + tasa) ** n - 1) / tasa


def anualidad_cuota_anticipada(vp: float, tasa: float, n: int) -> float:
    """Cuota de anualidad anticipada dado VP."""
    if tasa == 0:
        return vp / n
    return vp * tasa * (1 + tasa) ** (n - 1) / ((1 + tasa) ** n - 1)


def anualidad_vp_anticipada(cuota: float, tasa: float, n: int) -> float:
    """Valor Presente de anualidad anticipada."""
    if tasa == 0:
        return cuota * n
    return cuota * ((1 + tasa) ** n - 1) / (tasa * (1 + tasa) ** (n - 1))


def anualidad_vf_anticipada(cuota: float, tasa: float, n: int) -> float:
    """Valor Futuro de anualidad anticipada."""
    if tasa == 0:
        return cuota * n
    return cuota * (1 + tasa) * ((1 + tasa) ** n - 1) / tasa


# ─────────────────────────────────────────────
# GRADIENTES
# ─────────────────────────────────────────────

def gradiente_aritmetico_vp(primera_cuota: float, g: float, tasa: float, n: int) -> float:
    """Valor Presente de gradiente aritmético."""
    if tasa == 0:
        return primera_cuota * n + g * n * (n - 1) / 2
    vp_anualidad = anualidad_vp_ordinaria(primera_cuota, tasa, n)
    vp_gradiente = (g / tasa) * (anualidad_vp_ordinaria(1, tasa, n) - n / (1 + tasa) ** n)
    return vp_anualidad + vp_gradiente


def gradiente_aritmetico_vf(primera_cuota: float, g: float, tasa: float, n: int) -> float:
    """Valor Futuro de gradiente aritmético."""
    vp = gradiente_aritmetico_vp(primera_cuota, g, tasa, n)
    return vp * (1 + tasa) ** n


def gradiente_geometrico_vp(primera_cuota: float, g: float, tasa: float, n: int) -> float:
    """Valor Presente de gradiente geométrico."""
    if abs(tasa - g) < 1e-10:
        return primera_cuota * n / (1 + tasa)
    return primera_cuota * (1 - ((1 + g) / (1 + tasa)) ** n) / (tasa - g)


def gradiente_geometrico_vf(primera_cuota: float, g: float, tasa: float, n: int) -> float:
    """Valor Futuro de gradiente geométrico."""
    vp = gradiente_geometrico_vp(primera_cuota, g, tasa, n)
    return vp * (1 + tasa) ** n


def tabla_gradiente(primera_cuota: float, g: float, n: int, tipo: str = "aritmetico") -> pd.DataFrame:
    rows = []
    for t in range(1, n + 1):
        if tipo == "aritmetico":
            cuota = primera_cuota + g * (t - 1)
        else:
            cuota = primera_cuota * (1 + g) ** (t - 1)
        rows.append({"Período": t, "Cuota": cuota})
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# AMORTIZACIÓN
# ─────────────────────────────────────────────

def amortizacion_frances(capital: float, tasa: float, n: int) -> pd.DataFrame:
    """
    Sistema Francés: cuota constante (igual capital + interés cada período).
    """
    cuota = anualidad_cuota_ordinaria(capital, tasa, n)
    rows = []
    saldo = capital
    total_interes = 0
    total_capital = 0
    for t in range(1, n + 1):
        interes = saldo * tasa
        abono_capital = cuota - interes
        saldo_nuevo = saldo - abono_capital
        total_interes += interes
        total_capital += abono_capital
        rows.append({
            "Período": t,
            "Saldo Inicial": saldo,
            "Cuota Total": cuota,
            "Intereses": interes,
            "Abono Capital": abono_capital,
            "Saldo Final": max(saldo_nuevo, 0),
        })
        saldo = max(saldo_nuevo, 0)
    df = pd.DataFrame(rows)
    totales = {
        "Período": "TOTAL",
        "Saldo Inicial": "",
        "Cuota Total": cuota * n,
        "Intereses": total_interes,
        "Abono Capital": total_capital,
        "Saldo Final": "",
    }
    df = pd.concat([df, pd.DataFrame([totales])], ignore_index=True)
    return df, cuota


def amortizacion_aleman(capital: float, tasa: float, n: int) -> pd.DataFrame:
    """
    Sistema Alemán: abono a capital constante.
    """
    abono_capital = capital / n
    rows = []
    saldo = capital
    total_interes = 0
    total_cuota = 0
    for t in range(1, n + 1):
        interes = saldo * tasa
        cuota = abono_capital + interes
        saldo_nuevo = saldo - abono_capital
        total_interes += interes
        total_cuota += cuota
        rows.append({
            "Período": t,
            "Saldo Inicial": saldo,
            "Cuota Total": cuota,
            "Intereses": interes,
            "Abono Capital": abono_capital,
            "Saldo Final": max(saldo_nuevo, 0),
        })
        saldo = max(saldo_nuevo, 0)
    df = pd.DataFrame(rows)
    totales = {
        "Período": "TOTAL",
        "Saldo Inicial": "",
        "Cuota Total": total_cuota,
        "Intereses": total_interes,
        "Abono Capital": capital,
        "Saldo Final": "",
    }
    df = pd.concat([df, pd.DataFrame([totales])], ignore_index=True)
    return df


def amortizacion_americano(capital: float, tasa: float, n: int) -> pd.DataFrame:
    """
    Sistema Americano (Bullet): solo intereses periódicos, capital al final.
    """
    rows = []
    total_interes = 0
    for t in range(1, n + 1):
        interes = capital * tasa
        abono_capital = capital if t == n else 0
        cuota = interes + abono_capital
        saldo_nuevo = 0 if t == n else capital
        total_interes += interes
        rows.append({
            "Período": t,
            "Saldo Inicial": capital,
            "Cuota Total": cuota,
            "Intereses": interes,
            "Abono Capital": abono_capital,
            "Saldo Final": saldo_nuevo,
        })
    df = pd.DataFrame(rows)
    totales = {
        "Período": "TOTAL",
        "Saldo Inicial": "",
        "Cuota Total": capital * tasa * n + capital,
        "Intereses": total_interes,
        "Abono Capital": capital,
        "Saldo Final": "",
    }
    df = pd.concat([df, pd.DataFrame([totales])], ignore_index=True)
    return df


# ─────────────────────────────────────────────
# VPN / TIR
# ─────────────────────────────────────────────

def calcular_vpn(tasa: float, flujos: list) -> float:
    """
    Calcula el Valor Presente Neto.
    flujos[0] = inversión inicial (negativa), flujos[1..n] = flujos de caja.
    """
    vpn = 0
    for t, flujo in enumerate(flujos):
        vpn += flujo / (1 + tasa) ** t
    return vpn


def calcular_tir(flujos: list, guess: float = 0.1) -> Optional[float]:
    """
    Calcula la Tasa Interna de Retorno usando el método de Newton-Raphson.
    """
    if len(flujos) < 2:
        return None
    tasa = guess
    for _ in range(1000):
        vpn = calcular_vpn(tasa, flujos)
        # Derivada numérica
        d_vpn = sum(-t * f / (1 + tasa) ** (t + 1) for t, f in enumerate(flujos))
        if abs(d_vpn) < 1e-12:
            break
        nueva_tasa = tasa - vpn / d_vpn
        if abs(nueva_tasa - tasa) < 1e-10:
            return nueva_tasa
        tasa = nueva_tasa
    return tasa if abs(calcular_vpn(tasa, flujos)) < 1e-4 else None


def tabla_vpn_sensibilidad(flujos: list, tasa_min: float, tasa_max: float, pasos: int = 20) -> pd.DataFrame:
    tasas = np.linspace(tasa_min, tasa_max, pasos)
    rows = [{"Tasa (%)": round(t * 100, 2), "VPN": calcular_vpn(t, flujos)} for t in tasas]
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# FORMATEO
# ─────────────────────────────────────────────

def fmt_currency(value, prefix="$") -> str:
    try:
        return f"{prefix} {float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)


def fmt_percent(value) -> str:
    try:
        return f"{float(value) * 100:.4f}%"
    except (ValueError, TypeError):
        return str(value)
