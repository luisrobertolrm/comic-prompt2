"""
Fonte única dos atributos de personagem (Gerar por Atributos).

O front consome a lista via GET /character-options e envia apenas os ids
selecionados; o backend resolve aqui o fragmento de prompt em inglês.
Os grupos gender/body_type/skin_tone usam o label PT como id porque esses
valores são persistidos assim no banco (colunas de Character).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AttrOption:
    id: str
    label: str
    prompt: str


@dataclass(frozen=True)
class AttrGroup:
    id: str
    label: str
    multi: bool
    options: tuple[AttrOption, ...]

    def option(self, option_id: str) -> AttrOption | None:
        return next((o for o in self.options if o.id == option_id), None)


def _g(group_id: str, label: str, multi: bool, *options: tuple[str, str, str]) -> AttrGroup:
    return AttrGroup(group_id, label, multi, tuple(AttrOption(*o) for o in options))


# A ordem dos grupos define a ordem dos fragmentos no prompt.
GROUPS: dict[str, AttrGroup] = {g.id: g for g in (
    _g("gender", "Gênero", False,
       ("Feminino", "Feminino", "female character"),
       ("Masculino", "Masculino", "male character"),
       ("Outro", "Outro", "androgynous character"),
       ("Não especificado", "Não especificado", "")),
    _g("age_range", "Idade", False,
       ("crianca", "Criança", "young child"),
       ("adolescente", "Adolescente", "teenager"),
       ("jovem-adulto", "Jovem adulto", "young adult"),
       ("adulto", "Adulto", "adult in their 30s"),
       ("meia-idade", "Meia-idade", "middle-aged"),
       ("idoso", "Idoso", "elderly")),
    _g("body_type", "Tipo físico", False,
       ("Magro", "Magro", "slim thin build"),
       ("Médio", "Médio", "average build"),
       ("Atlético", "Atlético", "athletic toned build"),
       ("Forte", "Forte", "muscular heavy-set build, broad shoulders"),
       ("Gordo", "Gordo", "fat plus-size body, round chubby face")),
    _g("skin_tone", "Cor da pele", False,
       ("Clara", "Clara", "light fair skin"),
       ("Morena", "Morena", "medium brown skin"),
       ("Negra", "Negra", "Black person, very dark brown skin")),
    _g("ethnicity", "Etnia", False,
       ("asiatica", "Asiática (Leste)", "East Asian features"),
       ("sul-asiatica", "Sul-asiática", "South Asian features"),
       ("negra", "Africana", "African features"),
       ("branca", "Europeia", "European features"),
       ("latina", "Latina", "Latin American features"),
       ("indigena", "Indígena", "Indigenous features"),
       ("arabe", "Árabe / Oriente Médio", "Middle Eastern features")),
    _g("archetype", "Arquétipo", False,
       ("protagonista", "Protagonista", "heroic protagonist look"),
       ("rival", "Rival", "confident rival"),
       ("mentor", "Mentor", "wise mentor"),
       ("vilao", "Vilão", "menacing villain"),
       ("interesse-romantico", "Interesse romântico", "charming romantic interest"),
       ("alivio-comico", "Alívio cômico", "comic relief, expressive face"),
       ("misterioso", "Misterioso", "mysterious enigmatic figure")),
    _g("hair_color", "Cor do cabelo", False,
       ("preto", "Preto", "black hair"),
       ("castanho", "Castanho", "brown hair"),
       ("loiro", "Loiro", "blonde hair"),
       ("ruivo", "Ruivo", "red hair"),
       ("grisalho", "Grisalho / branco", "gray-white hair"),
       ("azul", "Azul", "blue hair"),
       ("rosa", "Rosa", "pink hair"),
       ("verde", "Verde", "green hair"),
       ("roxo", "Roxo", "purple hair")),
    _g("hair_style", "Estilo do cabelo", True,
       ("longo", "Longo", "long hair"),
       ("curto", "Curto", "short hair"),
       ("liso", "Liso", "straight hair"),
       ("ondulado", "Ondulado", "wavy hair"),
       ("cacheado", "Cacheado", "curly hair"),
       ("franja-reta", "Franja reta", "blunt bangs"),
       ("rabo-de-cavalo", "Rabo de cavalo", "ponytail"),
       ("coque", "Coque", "hair bun"),
       ("trancas", "Tranças", "braids"),
       ("raspado", "Raspado", "shaved head")),
    _g("eye_color", "Cor dos olhos", False,
       ("castanho", "Castanho", "brown eyes"),
       ("ambar", "Âmbar", "amber eyes"),
       ("azul", "Azul", "blue eyes"),
       ("verde", "Verde", "green eyes"),
       ("negro", "Negro", "black eyes"),
       ("vermelho", "Vermelho", "red eyes"),
       ("cinza", "Cinza", "gray eyes"),
       ("heterocromia", "Heterocromia", "heterochromia, two different colored eyes")),
    _g("outfit", "Figurino", False,
       ("uniforme-escolar", "Uniforme escolar", "school uniform"),
       ("casual", "Casual moderno", "modern casual clothes"),
       ("formal", "Formal / social", "formal suit attire"),
       ("kimono", "Kimono tradicional", "traditional kimono"),
       ("armadura", "Armadura", "armor"),
       ("capa", "Capa e manto", "cloak and hood"),
       ("esportivo", "Esportivo", "sportswear"),
       ("gotico", "Gótico / dark", "gothic dark clothing")),
    _g("accessories", "Acessórios e marcas", True,
       ("oculos", "Óculos", "glasses"),
       ("cicatriz", "Cicatriz no rosto", "facial scar"),
       ("sardas", "Sardas", "freckles"),
       ("tatuagem", "Tatuagem", "tattoo"),
       ("brincos", "Brincos", "earrings"),
       ("chapeu", "Chapéu", "hat"),
       ("mascara", "Máscara", "mask"),
       ("tapa-olho", "Tapa-olho", "eyepatch"),
       ("pinta", "Pinta no rosto", "beauty mark")),
    _g("personality", "Personalidade", True,
       ("timido", "Tímido", "shy reserved expression"),
       ("curioso", "Curioso", "curious bright expression"),
       ("corajoso", "Corajoso", "brave determined expression"),
       ("arrogante", "Arrogante", "arrogant smug expression"),
       ("sereno", "Sereno", "calm serene expression"),
       ("explosivo", "Explosivo", "fiery intense expression"),
       ("melancolico", "Melancólico", "melancholic wistful expression"),
       ("alegre", "Alegre", "cheerful smiling expression"),
       ("frio", "Frio", "cold stoic expression"),
       ("leal", "Leal", "warm loyal expression")),
)}


def prompt_for(group_id: str, option_id: str | None) -> str:
    """Fragmento EN de uma opção; '' para vazio ou desconhecido."""
    if not option_id:
        return ""
    opt = GROUPS[group_id].option(option_id)
    return opt.prompt if opt else ""


def validate_attrs(attrs: dict[str, list[str]]) -> None:
    for group_id, option_ids in attrs.items():
        group = GROUPS.get(group_id)
        if group is None:
            raise ValueError(f"Grupo de atributo inválido: '{group_id}'.")
        for oid in option_ids:
            if group.option(oid) is None:
                raise ValueError(f"Opção inválida em '{group_id}': '{oid}'.")


def attrs_fragment(attrs: dict[str, list[str]]) -> str:
    """Concatena os fragmentos EN das opções selecionadas, na ordem do catálogo."""
    parts: list[str] = []
    for group_id, group in GROUPS.items():
        for oid in attrs.get(group_id) or []:
            opt = group.option(oid)
            if opt is None:
                raise ValueError(f"Opção inválida em '{group_id}': '{oid}'.")
            if opt.prompt:
                parts.append(opt.prompt)
    return ", ".join(parts)
