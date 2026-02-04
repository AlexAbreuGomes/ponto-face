from datetime import datetime

ESTADOS_OBRIGATORIOS = ["entrada", "intervalo_inicio", "intervalo_volta", "saida"]

def _parse_data_hora(iso: str) -> datetime:
    return datetime.fromisoformat(iso)

def formatar_hms(segundos: int) -> str:
    sinal = "-" if segundos < 0 else ""
    segundos = abs(segundos)
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    return f"{sinal}{h:02d}:{m:02d}:{s:02d}"

def calcular_total_do_dia(linhas):
    """
    linhas: (data_hora, estado, score, caminho_foto)
    """
    por_estado = {}
    for data_hora, estado, *_ in linhas:
        por_estado.setdefault(estado, data_hora)  # pega a primeira ocorrência do estado

    faltando = [e for e in ESTADOS_OBRIGATORIOS if e not in por_estado]
    if faltando:
        return False, {"faltando": faltando, "por_estado": por_estado}

    t_entrada = _parse_data_hora(por_estado["entrada"])
    t_i_ini = _parse_data_hora(por_estado["intervalo_inicio"])
    t_i_volta = _parse_data_hora(por_estado["intervalo_volta"])
    t_saida = _parse_data_hora(por_estado["saida"])

    bruto = int((t_saida - t_entrada).total_seconds())
    intervalo = int((t_i_volta - t_i_ini).total_seconds())
    total = bruto - intervalo

    return True, {"bruto": bruto, "intervalo": intervalo, "total": total, "por_estado": por_estado}
