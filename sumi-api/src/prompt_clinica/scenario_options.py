"""
Fonte única dos atributos de cenário (Gerar por Atributos).

O front consome a lista via GET /scenario-options e envia apenas os ids
selecionados; o backend resolve aqui o fragmento de prompt em inglês.
Mesmo formato de character_options, mas voltado a ambientação (local, hora do
dia, clima, atmosfera).
"""
from __future__ import annotations

from prompt_clinica.character_options import AttrGroup, AttrOption


def _g(group_id: str, label: str, multi: bool, *options: tuple[str, str, str]) -> AttrGroup:
    return AttrGroup(group_id, label, multi, tuple(AttrOption(*o) for o in options))


# A ordem dos grupos define a ordem dos fragmentos no prompt.
GROUPS: dict[str, AttrGroup] = {g.id: g for g in (
    _g("location", "Local", False,
       ("castelo", "Castelo", "a grand medieval castle"),
       ("fazenda", "Fazenda", "a rural farm with fields and barns"),
       ("floresta", "Floresta", "a dense forest"),
       ("cidade", "Cidade", "a bustling city street"),
       ("vila", "Vila", "a small quiet village"),
       ("praia", "Praia", "a sandy beach by the sea"),
       ("montanha", "Montanha", "a mountain landscape"),
       ("deserto", "Deserto", "a vast desert"),
       ("templo", "Templo", "an ancient temple"),
       ("caverna", "Caverna", "a cave interior"),
       ("interior", "Interior / cômodo", "an indoor room interior"),
       ("scifi", "Sci-fi / futurista", "a futuristic sci-fi environment")),
    _g("time_of_day", "Hora do dia", False,
       ("amanhecer", "Amanhecer", "at dawn, soft sunrise light"),
       ("manha", "Manhã", "in the morning, bright daylight"),
       ("tarde", "Tarde", "in the afternoon"),
       ("entardecer", "Entardecer", "at sunset, golden hour light"),
       ("noite", "Noite", "at night, moonlight")),
    _g("weather", "Clima", False,
       ("limpo", "Limpo", "clear sky"),
       ("nublado", "Nublado", "overcast cloudy sky"),
       ("chuva", "Chuva", "rain"),
       ("neve", "Neve", "snow"),
       ("tempestade", "Tempestade", "storm with lightning"),
       ("neblina", "Neblina", "misty fog")),
    _g("atmosphere", "Atmosfera", False,
       ("aconchegante", "Aconchegante", "cozy warm atmosphere"),
       ("sombrio", "Sombrio", "dark gloomy atmosphere"),
       ("epico", "Épico", "epic grand atmosphere"),
       ("misterioso", "Misterioso", "mysterious eerie atmosphere"),
       ("sereno", "Sereno", "calm serene atmosphere"),
       ("magico", "Mágico", "magical fantastical atmosphere"),
       ("decadente", "Decadente / ruínas", "decayed ruined atmosphere")),
)}


def prompt_for(group_id: str, option_id: str | None) -> str:
    """Fragmento EN de uma opção; '' para vazio ou desconhecido."""
    if not option_id:
        return ""
    opt = GROUPS[group_id].option(option_id)
    return opt.prompt if opt else ""
